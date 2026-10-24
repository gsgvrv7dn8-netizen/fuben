"""AI-assisted end-to-end tests of run evidence and immutable run directories."""

from datetime import datetime, timedelta
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from mathorcup_a import tracking


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    source = root / "src" / "probe.py"
    source.parent.mkdir(parents=True)
    source.write_text("SNAPSHOT_VERSION = 1\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "test-probe"\n', encoding="utf-8")
    features_path, targets_path, config_path = root / "1.csv", root / "4.csv", root / "config.json"
    metadata = {
        "beer": [f"beer_{i:02d}" for i in range(12)],
        "beer_id": list(range(12)),
        "tasting_category_fine": ["Common"] * 9 + ["Rare"] * 3,
    }
    features = pd.DataFrame({**metadata, "x_a": np.arange(12, dtype=float),
                             "x_b": [np.nan, 1, 4, 2, 5, 3, 9, 7, 8, 6, 11, 10]})
    targets = pd.DataFrame({**metadata, "y_a": np.arange(12) / 3,
                            "y_b": [1, 3, 2, 5, 8, 4, 9, 6, 7, 11, 12, 10]})
    features.to_csv(features_path, index=False)
    targets.iloc[::-1].to_csv(targets_path, index=False)
    config_path.write_text(json.dumps({
        "n_splits": 3, "seed": 72, "ridge_alpha": 100,
        "expected_samples": 12, "expected_features": 2, "expected_targets": 2,
    }), encoding="utf-8")
    monkeypatch.setattr(tracking, "PROJECT_ROOT", root)
    return root, features_path, targets_path, config_path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(project, run_id="complete-probe"):
    root, features, targets, config = project
    return tracking.run_experiment(features, targets, config, root / "runs", run_id=run_id)


def test_complete_run_provenance_hashes_and_metrics_recompute(project):
    root, features, targets, config = project
    output = run(project)
    manifest = read_json(output / "manifest.json")
    assert manifest["status"] == "completed"
    assert manifest["run_id"] == "complete-probe"
    assert manifest["official_final_output"] is False
    assert manifest["team_modeling_approval"] == "pending"
    assert manifest["target_scale"] == "observed_standardized_unverified_inverse"
    assert datetime.fromisoformat(manifest["started_at_utc_plus_8"]).utcoffset() == timedelta(hours=8)
    assert manifest["elapsed_seconds"] > 0
    for label, path in [("features", features), ("targets", targets), ("requested_config", config)]:
        assert manifest["inputs"][label] == {"path": str(path.resolve()), "sha256": digest(path)}
    assert manifest["environment"]["packages"]["scikit-learn"]
    assert manifest["code"]["source_manifest"]["src/probe.py"] == digest(root / "src" / "probe.py")
    assert (output / "source_snapshot" / "src" / "probe.py").read_bytes() == (root / "src" / "probe.py").read_bytes()
    assert (output / "requested_config.json").read_bytes() == config.read_bytes()
    assert manifest["folds_sha256"] == digest(output / "folds.csv")
    for relative, expected_hash in manifest["artifacts_sha256"].items():
        assert digest(output / relative) == expected_hash

    oof = pd.read_csv(output / "oof_predictions.csv")
    targets_table = pd.read_csv(output / "target_metrics.csv").set_index(["model", "target"])
    summary = read_json(output / "summary.json")["metrics"]
    for model, model_group in oof.groupby("model"):
        absolute_errors, rmses = [], []
        for target, group in model_group.groupby("target"):
            residual = group["predicted"].to_numpy() - group["observed"].to_numpy()
            mae = np.mean(np.abs(residual))
            rmse = np.sqrt(np.mean(residual**2))
            expected_r2 = 1 - np.sum(residual**2) / np.sum(
                (group["observed"] - group["observed"].mean())**2
            )
            recorded = targets_table.loc[(model, target)]
            assert recorded["n"] == 12
            assert recorded["mae"] == pytest.approx(mae, abs=1e-12)
            assert recorded["rmse"] == pytest.approx(rmse, abs=1e-12)
            assert recorded["r2"] == pytest.approx(expected_r2, abs=1e-12)
            absolute_errors.append(mae)
            rmses.append(rmse)
        assert summary[model]["macro_target_mae"] == pytest.approx(np.mean(absolute_errors))
        assert summary[model]["macro_target_rmse"] == pytest.approx(np.mean(rmses))
    assert manifest["metrics"] == summary


def test_failed_data_validation_leaves_manifest_and_traceback(project):
    root, _, targets, _ = project
    pd.read_csv(targets).iloc[:-1].to_csv(targets, index=False)
    with pytest.raises(ValueError, match="key sets differ"):
        run(project, run_id="failed-probe")
    output = root / "runs" / "failed-probe"
    manifest = read_json(output / "manifest.json")
    assert manifest["status"] == "failed"
    assert manifest["error"]["type"] == "ValueError"
    assert manifest["ended_at_utc_plus_8"]
    assert manifest["inputs"]["targets"]["sha256"] == digest(targets)
    assert "key sets differ" in (output / "error_traceback.txt").read_text(encoding="utf-8")
    assert "error_traceback.txt" in manifest["artifacts_sha256"]
    assert not (output / "summary.json").exists()


def test_existing_run_id_cannot_overwrite_evidence(project):
    output = run(project, run_id="keep-existing")
    before = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        run(project, run_id="keep-existing")
    assert (output / "manifest.json").read_bytes() == before


def test_input_mutation_during_evaluation_invalidates_run(project, monkeypatch):
    root, features, _, _ = project
    evaluate = tracking.evaluate

    def evaluate_then_mutate(*args, **kwargs):
        result = evaluate(*args, **kwargs)
        features.write_text(features.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return result

    monkeypatch.setattr(tracking, "evaluate", evaluate_then_mutate)
    with pytest.raises(RuntimeError, match="Input changed during run"):
        run(project, run_id="mutated-input")
    manifest = read_json(root / "runs" / "mutated-input" / "manifest.json")
    assert manifest["status"] == "failed"
    assert manifest["error"]["type"] == "RuntimeError"


@pytest.mark.parametrize("location", ["outside_project", "source_directory"])
def test_output_directory_must_be_inside_project_runs(project, location):
    root, features, targets, config = project
    outside = root.parent / "outside" if location == "outside_project" else root / "src"
    with pytest.raises(ValueError, match="runs directory"):
        tracking.run_experiment(features, targets, config, outside, run_id="outside-probe")
    assert not (outside / "outside-probe").exists()
