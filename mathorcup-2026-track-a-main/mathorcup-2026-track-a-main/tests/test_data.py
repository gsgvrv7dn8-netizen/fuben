"""AI-assisted synthetic tests of alignment and fail-closed data contracts."""

import json

import numpy as np
import pandas as pd
import pytest

from mathorcup_a.data import load_aligned_data


@pytest.fixture
def tables():
    features = pd.DataFrame(
        {
            "beer": ["beer_b", "beer_a", "beer_c"],
            "beer_id": [101, 102, 103],
            "tasting_category_fine": ["Blond", "Faro", "Faro"],
            "chemical_b": [2.0, np.nan, 3.0],
            "chemical_a": [20.0, 10.0, 30.0],
        }
    )
    targets = pd.DataFrame(
        {
            "beer": ["beer_c", "beer_b", "beer_a"],
            "beer_id": [1e8, 1e8, 1e8],
            "tasting_category_fine": ["Faro", "Blond", "Faro"],
            "sensory_b": [0.3, 0.2, 0.1],
            "sensory_a": [3.0, 2.0, 1.0],
        }
    )
    return features, targets


def write_tables(tmp_path, features, targets):
    features_path, targets_path = tmp_path / "1.csv", tmp_path / "4.csv"
    features.to_csv(features_path, index=False, encoding="utf-8-sig")
    targets.to_csv(targets_path, index=False, encoding="utf-8-sig")
    return features_path, targets_path


def test_sort_alignment_preserves_columns_and_missing_values(tmp_path, tables):
    result = load_aligned_data(*write_tables(tmp_path, *tables))
    assert result.metadata["beer"].tolist() == ["beer_a", "beer_b", "beer_c"]
    assert result.metadata["beer_id"].tolist() == ["102", "101", "103"]
    assert result.X.columns.tolist() == ["chemical_b", "chemical_a"]
    assert result.y.columns.tolist() == ["sensory_b", "sensory_a"]
    assert result.y["sensory_a"].tolist() == [1.0, 2.0, 3.0]
    assert result.X["chemical_a"].tolist() == [10.0, 20.0, 30.0]
    assert np.isnan(result.X.loc[0, "chemical_b"])
    assert result.audit["missing_counts"]["chemical_b"] == 1
    assert result.audit["beer_id_used_for_alignment"] is False
    json.dumps(result.audit, allow_nan=False)


def test_input_order_does_not_change_alignment(tmp_path, tables):
    features, targets = tables
    first = load_aligned_data(*write_tables(tmp_path, features, targets))
    second = load_aligned_data(
        *write_tables(tmp_path, features.iloc[::-1], targets.sample(frac=1, random_state=2))
    )
    pd.testing.assert_frame_equal(first.metadata, second.metadata)
    pd.testing.assert_frame_equal(first.X, second.X)
    pd.testing.assert_frame_equal(first.y, second.y)


@pytest.mark.parametrize("table_index", [0, 1])
def test_duplicate_beer_is_rejected(tmp_path, tables, table_index):
    tables[table_index].loc[1, "beer"] = tables[table_index].loc[0, "beer"]
    with pytest.raises(ValueError, match="duplicate beer"):
        load_aligned_data(*write_tables(tmp_path, *tables))


@pytest.mark.parametrize("change", ["missing", "extra", "replace"])
def test_unequal_key_sets_are_rejected(tmp_path, tables, change):
    features, targets = tables
    if change == "missing":
        targets = targets.iloc[:-1]
    elif change == "extra":
        extra = targets.iloc[[0]].copy()
        extra["beer"] = "beer_extra"
        targets = pd.concat([targets, extra], ignore_index=True)
    else:
        targets.loc[0, "beer"] = "beer_other"
    with pytest.raises(ValueError, match="beer key sets differ"):
        load_aligned_data(*write_tables(tmp_path, features, targets))


@pytest.mark.parametrize("column", ["beer", "tasting_category_fine"])
@pytest.mark.parametrize("bad_value", [None, "", "  ", " value", "value "])
def test_invalid_key_or_style_rejected(tmp_path, tables, column, bad_value):
    tables[0].loc[0, column] = bad_value
    with pytest.raises(ValueError, match="must be nonempty"):
        load_aligned_data(*write_tables(tmp_path, *tables))


def test_style_conflict_rejected(tmp_path, tables):
    tables[1].loc[0, "tasting_category_fine"] = "Stout"
    with pytest.raises(ValueError, match="style mismatch"):
        load_aligned_data(*write_tables(tmp_path, *tables))


@pytest.mark.parametrize("table_index,column", [(0, "chemical_a"), (1, "sensory_a")])
@pytest.mark.parametrize("bad_value,match", [("oops", "nonnumeric"), (np.inf, "infinite")])
def test_invalid_numeric_value_rejected(tmp_path, tables, table_index, column, bad_value, match):
    tables[table_index][column] = tables[table_index][column].astype(object)
    tables[table_index].loc[0, column] = bad_value
    with pytest.raises(ValueError, match=match):
        load_aligned_data(*write_tables(tmp_path, *tables))


def test_target_missing_rejected(tmp_path, tables):
    tables[1].loc[0, "sensory_a"] = np.nan
    with pytest.raises(ValueError, match="missing target"):
        load_aligned_data(*write_tables(tmp_path, *tables))


def test_entirely_missing_feature_rejected(tmp_path, tables):
    tables[0]["chemical_b"] = np.nan
    with pytest.raises(ValueError, match="entirely missing"):
        load_aligned_data(*write_tables(tmp_path, *tables))


@pytest.mark.parametrize(
    "expected", [{"expected_samples": 250}, {"expected_features": 231}, {"expected_targets": 50}]
)
def test_expected_dimensions_checked(tmp_path, tables, expected):
    with pytest.raises(ValueError, match="expected"):
        load_aligned_data(*write_tables(tmp_path, *tables), **expected)


@pytest.mark.parametrize("header,match", [("beer,beer", "duplicate column"), ("beer,", "empty column")])
def test_invalid_header_rejected_before_pandas_mangling(tmp_path, tables, header, match):
    features_path, targets_path = write_tables(tmp_path, *tables)
    features_path.write_text(header + "\na,b\n", encoding="utf-8-sig")
    with pytest.raises(ValueError, match=match):
        load_aligned_data(features_path, targets_path)


def test_missing_metadata_rejected(tmp_path, tables):
    features, targets = tables
    with pytest.raises(ValueError, match="missing metadata"):
        load_aligned_data(*write_tables(tmp_path, features.drop(columns="beer_id"), targets))


@pytest.mark.parametrize("row", ["beer_a,123,Faro,1,extra", "beer_a,123,Faro"])
def test_ragged_csv_row_rejected_instead_of_inferred_index(tmp_path, tables, row):
    features_path, targets_path = write_tables(tmp_path, *tables)
    features_path.write_text(
        "beer,beer_id,tasting_category_fine,chemical\n" + row + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="row width"):
        load_aligned_data(features_path, targets_path)
