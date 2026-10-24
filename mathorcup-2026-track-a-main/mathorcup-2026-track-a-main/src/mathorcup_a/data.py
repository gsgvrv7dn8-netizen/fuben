"""AI-assisted CSV contracts; model decisions require team review.

Only observed standardized sensory targets are loaded here. No imputation,
feature selection, inverse transform, or use of reference-model outputs occurs.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


METADATA_COLUMNS = ["beer", "beer_id", "tasting_category_fine"]
TARGET_SCALE = "observed_standardized_unverified_inverse"


@dataclass(frozen=True)
class AlignedData:
    metadata: pd.DataFrame
    X: pd.DataFrame
    y: pd.DataFrame
    audit: dict


def _read_table(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
        if header:
            for row in reader:
                if row and len(row) != len(header):
                    raise ValueError(f"{path.name}: CSV row width differs from header")
    if not header:
        raise ValueError(f"{path.name}: missing CSV header")
    if any(not name.strip() for name in header):
        raise ValueError(f"{path.name}: empty column name")
    duplicates = [name for name, count in Counter(header).items() if count > 1]
    if duplicates:
        raise ValueError(f"{path.name}: duplicate column names: {duplicates}")
    missing_columns = sorted(set(METADATA_COLUMNS) - set(header))
    if missing_columns:
        raise ValueError(f"{path.name}: missing metadata columns: {missing_columns}")
    table = pd.read_csv(
        path, encoding="utf-8-sig", dtype={name: "string" for name in METADATA_COLUMNS}
    )
    if table.empty:
        raise ValueError(f"{path.name}: no samples")
    for name in ["beer", "tasting_category_fine"]:
        values = table[name]
        invalid = values.isna() | values.str.strip().eq("") | values.ne(values.str.strip())
        if invalid.any():
            raise ValueError(f"{path.name}: {name} must be nonempty without surrounding whitespace")
    if table["beer"].duplicated().any():
        duplicates = table.loc[table["beer"].duplicated(keep=False), "beer"].tolist()
        raise ValueError(f"{path.name}: duplicate beer keys: {duplicates}")
    return table


def _numeric_values(table: pd.DataFrame, *, name: str, allow_missing: bool) -> pd.DataFrame:
    columns = [column for column in table.columns if column not in METADATA_COLUMNS]
    if not columns:
        raise ValueError(f"{name}: no numeric columns")
    try:
        values = table[columns].apply(pd.to_numeric, errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: nonnumeric feature/target value") from exc
    if np.isinf(values.to_numpy()).any():
        raise ValueError(f"{name}: infinite numeric values")
    if not allow_missing and values.isna().any().any():
        raise ValueError(f"{name}: missing target values")
    empty_columns = values.columns[values.isna().all()].tolist()
    if empty_columns:
        raise ValueError(f"{name}: entirely missing columns: {empty_columns}")
    return values


def load_aligned_data(
    features_path: Path,
    targets_path: Path,
    *,
    expected_samples: int | None = None,
    expected_features: int | None = None,
    expected_targets: int | None = None,
) -> AlignedData:
    """Read two tables and enforce a one-to-one, sorted ``beer`` alignment."""
    features = _read_table(Path(features_path))
    targets = _read_table(Path(targets_path))
    feature_keys = set(features["beer"])
    target_keys = set(targets["beer"])
    if feature_keys != target_keys:
        raise ValueError(
            "beer key sets differ: "
            f"missing_targets={sorted(feature_keys - target_keys)}, "
            f"extra_targets={sorted(target_keys - feature_keys)}"
        )

    # Unique indices and exact key-set equality prevent row expansion or loss.
    keys = sorted(feature_keys)
    features = features.set_index("beer", verify_integrity=True).loc[keys].reset_index()
    targets = targets.set_index("beer", verify_integrity=True).loc[keys].reset_index()
    conflicts = features["tasting_category_fine"].ne(targets["tasting_category_fine"])
    if conflicts.any():
        raise ValueError(
            "style mismatch for beer keys: " + str(features.loc[conflicts, "beer"].tolist())
        )

    X = _numeric_values(features, name="features", allow_missing=True)
    y = _numeric_values(targets, name="targets", allow_missing=False)
    dimensions = {
        "samples": (len(features), expected_samples),
        "features": (X.shape[1], expected_features),
        "targets": (y.shape[1], expected_targets),
    }
    for name, (actual, expected) in dimensions.items():
        if expected is not None and actual != expected:
            raise ValueError(f"expected {expected} {name}, found {actual}")

    metadata = features[METADATA_COLUMNS].copy()
    audit = {
        "samples": len(metadata),
        "features": X.shape[1],
        "targets": y.shape[1],
        "shape": {"X": list(X.shape), "y": list(y.shape)},
        "columns": {"features": X.columns.tolist(), "targets": y.columns.tolist()},
        "missing_counts": {column: int(count) for column, count in X.isna().sum().items()},
        "target_missing_count": int(y.isna().sum().sum()),
        "style_counts": {
            str(style): int(count)
            for style, count in metadata["tasting_category_fine"].value_counts().sort_index().items()
        },
        "join_key": "beer",
        "alignment": "unique_keys_exact_set_sorted_ascending",
        "beer_id_used_for_alignment": False,
        "target_scale": TARGET_SCALE,
        "feature_units": "as_supplied_unverified_no_inverse_transform",
    }
    return AlignedData(metadata=metadata, X=X, y=y, audit=audit)
