"""AI-assisted behavioral tests of fold isolation, coverage, and metrics."""

import numpy as np
import pandas as pd
import pytest

from mathorcup_a.data import AlignedData
from mathorcup_a.experiment import (
    ExperimentConfig,
    evaluate,
    make_folds,
    make_ridge,
    regression_metrics,
)


@pytest.fixture
def small_data():
    return AlignedData(
        metadata=pd.DataFrame(
            {
                "beer": [f"beer_{i:02d}" for i in range(12)],
                "beer_id": [str(i) for i in range(12)],
                "tasting_category_fine": ["Common"] * 9 + ["Rare"] * 3,
            }
        ),
        X=pd.DataFrame({"chemical_a": np.arange(12, dtype=float),
                        "chemical_b": [np.nan, 2, 4, 1, 3, 8, 7, 5, 11, 13, 12, 9]}),
        y=pd.DataFrame({"sensory_a": np.arange(12) * 0.2,
                        "sensory_b": [1, 3, 2, 2, 8, 5, 6, 10, 7, 9, 4, 11]}),
        audit={},
    )


@pytest.fixture
def small_config():
    return ExperimentConfig(n_splits=3, seed=72, expected_samples=12,
                            expected_features=2, expected_targets=2)


def test_fixed_folds_cover_each_beer_once_and_require_canonical_order(small_data, small_config):
    first = make_folds(small_data.metadata, small_config)
    second = make_folds(small_data.metadata.copy(), small_config)
    pd.testing.assert_frame_equal(first, second)
    assert first["beer"].is_unique
    assert first["fold"].value_counts().to_dict() == {0: 4, 1: 4, 2: 4}
    with pytest.raises(ValueError, match="sorted"):
        make_folds(small_data.metadata.iloc[::-1], small_config)


def test_preprocessing_statistics_ignore_heldout_extremes(tmp_path, small_data, small_config):
    folds = make_folds(small_data.metadata, small_config)
    heldout = folds["fold"].eq(0)
    first_output, second_output = tmp_path / "first", tmp_path / "second"
    first_output.mkdir()
    second_output.mkdir()
    original = evaluate(small_data, small_config, first_output)
    changed_X = small_data.X.copy()
    changed_X.loc[heldout, :] = 1e7
    changed = AlignedData(small_data.metadata, changed_X, small_data.y, {})
    result = evaluate(changed, small_config, second_output)
    for statistic in ["imputer_statistics", "scaler_mean", "scaler_scale"]:
        np.testing.assert_array_equal(
            original["preprocessing"][0][statistic], result["preprocessing"][0][statistic]
        )


def test_training_empty_feature_is_kept_and_zero_imputed(tmp_path, small_data, small_config):
    heldout = make_folds(small_data.metadata, small_config)["fold"].eq(0)
    X = small_data.X.copy()
    X.loc[~heldout, "chemical_a"] = np.nan
    data = AlignedData(small_data.metadata, X, small_data.y, {})
    result = evaluate(data, small_config, tmp_path)
    report = result["preprocessing"][0]
    assert report["train_all_missing_features"] == ["chemical_a"]
    assert report["imputer_statistics"][0] == 0
    assert report["scaler_mean"][0] == 0
    assert report["scaler_scale"][0] == 1
    assert len(report["imputer_statistics"]) == 2
    model = make_ridge(small_config).fit(X.loc[~heldout], data.y.loc[~heldout])
    transformed = model[:-1].transform(X.loc[~heldout])
    assert transformed.shape == (8, 2)
    np.testing.assert_array_equal(transformed[:, 0], np.zeros(8))
    assert model.named_steps["regressor"].n_features_in_ == 2


def test_oof_coverage_and_baseline_use_only_training_targets(tmp_path, small_data, small_config):
    evaluate(small_data, small_config, tmp_path)
    oof = pd.read_csv(tmp_path / "oof_predictions.csv")
    folds = pd.read_csv(tmp_path / "folds.csv")
    assert len(oof) == 2 * 12 * 2
    assert not oof.duplicated(["model", "beer", "target"]).any()
    assert set(oof["model"]) == {"train_mean", "ridge"}
    assert np.isfinite(oof[["observed", "predicted"]].to_numpy()).all()
    expected_keys = {
        (model, beer, target)
        for model in ["train_mean", "ridge"]
        for beer in small_data.metadata["beer"]
        for target in small_data.y.columns
    }
    assert set(oof[["model", "beer", "target"]].itertuples(index=False, name=None)) == expected_keys
    for fold in range(3):
        train = folds["fold"].ne(fold)
        for target in small_data.y:
            baseline = oof.loc[(oof["model"] == "train_mean") & (oof["fold"] == fold)
                               & (oof["target"] == target), "predicted"]
            np.testing.assert_allclose(baseline, small_data.y.loc[train, target].mean())


def test_regression_metrics_have_defined_constant_policy():
    assert regression_metrics(np.array([1, 3]), np.array([2, 2])) == {
        "n": 2, "mae": 1, "rmse": 1, "r2": 0
    }
    constant = regression_metrics(np.array([2, 2]), np.array([3, 5]))
    assert constant["r2"] is None
    assert constant["mae"] == 2
    assert constant["rmse"] == pytest.approx(np.sqrt(5))


@pytest.mark.parametrize("sample_count", [3, 50])
def test_fractional_constant_target_has_no_r2(sample_count):
    metric = regression_metrics(np.full(sample_count, 0.1), np.zeros(sample_count))
    assert metric["r2"] is None
    assert metric["mae"] == pytest.approx(0.1)
    assert metric["rmse"] == pytest.approx(0.1)


@pytest.mark.parametrize(
    "observed,predicted", [([], []), ([1], [1, 2]), ([np.nan], [1]), ([1], [np.inf])]
)
def test_metrics_reject_invalid_arrays(observed, predicted):
    with pytest.raises(ValueError):
        regression_metrics(np.array(observed), np.array(predicted))
