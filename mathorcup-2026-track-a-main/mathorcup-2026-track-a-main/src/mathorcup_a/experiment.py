"""AI-assisted exploratory CV; model/validation decisions await team confirmation."""

from dataclasses import asdict, dataclass
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .data import AlignedData


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int = 20261024
    n_splits: int = 5
    ridge_alpha: float = 100.0
    validation_version: str = "exploratory-beer-sorted-shuffled-kfold-v0"
    metric_version: str = "standardized-oof-regression-v0"
    expected_samples: int | None = 250
    expected_features: int | None = 231
    expected_targets: int | None = 50

    def __post_init__(self) -> None:
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer in [0, 2**32)")
        if type(self.n_splits) is not int or self.n_splits < 2:
            raise ValueError("n_splits must be an integer >= 2")
        if (type(self.ridge_alpha) not in (int, float)
                or not math.isfinite(self.ridge_alpha) or self.ridge_alpha <= 0):
            raise ValueError("ridge_alpha must be finite and positive")
        for name in ("validation_version", "metric_version"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a nonempty string")
        for name in ("expected_samples", "expected_features", "expected_targets"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError(f"{name} must be a positive integer or null")


def make_folds(metadata: pd.DataFrame, config: ExperimentConfig) -> pd.DataFrame:
    """Canonical string beer ordering makes source CSV ordering irrelevant."""
    beer = metadata["beer"].astype(str)
    if beer.tolist() != sorted(beer.tolist()) or beer.duplicated().any():
        raise ValueError("metadata must have unique beer keys sorted as strings")
    if len(metadata) < 2 * config.n_splits:
        raise ValueError("Need at least two validation samples per fold for R2")
    folds = metadata[["beer", "tasting_category_fine"]].copy().reset_index(drop=True)
    folds["fold"] = -1
    splitter = KFold(config.n_splits, shuffle=True, random_state=config.seed)
    for fold, (_, valid) in enumerate(splitter.split(folds)):
        folds.loc[valid, "fold"] = fold
    return folds


def make_ridge(config: ExperimentConfig) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", StandardScaler()),
        ("regressor", Ridge(alpha=config.ridge_alpha, solver="svd")),
    ])


def regression_metrics(observed: np.ndarray, predicted: np.ndarray) -> dict:
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if observed.shape != predicted.shape or observed.size == 0:
        raise ValueError("Metrics require nonempty matching shapes")
    if not np.isfinite(observed).all() or not np.isfinite(predicted).all():
        raise ValueError("Metrics require finite observations and predictions")
    error = predicted - observed
    total = float(np.sum((observed - observed.mean()) ** 2))
    constant = bool(np.all(observed == observed.flat[0]))
    return {
        "n": int(observed.size),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "r2": None if constant or total == 0 or observed.size < 2 else float(1 - np.sum(error**2) / total),
    }


def evaluate(data: AlignedData, config: ExperimentConfig, output: Path) -> dict:
    """Fit only on fold-training rows, then emit auditable, unrounded OOF values."""
    folds = make_folds(data.metadata, config)
    folds.to_csv(output / "folds.csv", index=False, lineterminator="\n")
    style_counts = pd.crosstab(folds["tasting_category_fine"], folds["fold"])
    style_counts.to_csv(output / "fold_style_counts.csv", lineterminator="\n")
    truth = data.y.to_numpy(dtype=float)
    predictions = {name: np.full_like(truth, np.nan) for name in ("train_mean", "ridge")}
    preprocessing = []
    for fold in range(config.n_splits):
        valid = folds["fold"].to_numpy() == fold
        train = ~valid
        baseline = DummyRegressor(strategy="mean")
        baseline.fit(data.X.loc[train], truth[train])
        predictions["train_mean"][valid] = baseline.predict(data.X.loc[valid])
        model = make_ridge(config)
        with threadpool_limits(limits=1):
            model.fit(data.X.loc[train], truth[train])
            predictions["ridge"][valid] = model.predict(data.X.loc[valid])
        preprocessing.append({
            "fold": fold,
            "train_n": int(train.sum()), "valid_n": int(valid.sum()),
            "train_all_missing_features": data.X.columns[data.X.loc[train].isna().all()].tolist(),
            "imputer_statistics": model.named_steps["imputer"].statistics_.tolist(),
            "scaler_mean": model.named_steps["scaler"].mean_.tolist(),
            "scaler_scale": model.named_steps["scaler"].scale_.tolist(),
        })

    oof_tables, target_rows, fold_rows, style_rows = [], [], [], []
    summary = {}
    for name, pred in predictions.items():
        if not np.isfinite(pred).all():
            raise ValueError(f"Missing or nonfinite OOF prediction: {name}")
        table = folds.loc[folds.index.repeat(truth.shape[1])].reset_index(drop=True)
        table["model"] = name
        table["target"] = np.tile(data.y.columns.to_numpy(), len(data.y))
        table["observed"] = truth.ravel()
        table["predicted"] = pred.ravel()
        table["residual_pred_minus_true"] = table["predicted"] - table["observed"]
        oof_tables.append(table)
        model_rows = []
        for column, target in enumerate(data.y.columns):
            row = {"model": name, "target": target,
                   **regression_metrics(truth[:, column], pred[:, column])}
            target_rows.append(row)
            model_rows.append(row)
            for fold in range(config.n_splits):
                selected = folds["fold"].to_numpy() == fold
                fold_rows.append({"model": name, "target": target, "fold": fold,
                                  **regression_metrics(truth[selected, column], pred[selected, column])})
        for style, group in folds.groupby("tasting_category_fine", sort=True):
            error = pred[group.index] - truth[group.index]
            style_rows.append({"model": name, "style": style, "n_beers": len(group),
                               "pooled_mae": float(np.abs(error).mean()),
                               "pooled_rmse": float(np.sqrt((error**2).mean()))})
        defined_r2 = [row["r2"] for row in model_rows if row["r2"] is not None]
        summary[name] = {
            "macro_target_mae": float(np.mean([row["mae"] for row in model_rows])),
            "macro_target_rmse": float(np.mean([row["rmse"] for row in model_rows])),
            "macro_target_r2_defined_only": float(np.mean(defined_r2)) if defined_r2 else None,
            "r2_defined_target_count": len(defined_r2),
            "pooled_rmse": float(np.sqrt(np.mean((pred - truth) ** 2))),
        }
    oof = pd.concat(oof_tables, ignore_index=True)
    if oof.duplicated(["model", "beer", "target"]).any():
        raise ValueError("OOF coverage duplicated")
    oof.to_csv(output / "oof_predictions.csv", index=False, lineterminator="\n")
    pd.DataFrame(target_rows).to_csv(output / "target_metrics.csv", index=False, lineterminator="\n")
    pd.DataFrame(fold_rows).to_csv(output / "fold_target_metrics.csv", index=False, lineterminator="\n")
    pd.DataFrame(style_rows).to_csv(output / "style_metrics.csv", index=False, lineterminator="\n")
    return {"metrics": summary, "preprocessing": preprocessing, "config": asdict(config)}
