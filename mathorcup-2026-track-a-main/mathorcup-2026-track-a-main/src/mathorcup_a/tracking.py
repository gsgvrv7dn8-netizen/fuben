"""AI-assisted local run provenance; no remote tracking or original-file writes."""

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
from uuid import uuid4

from threadpoolctl import threadpool_info

from .data import load_aligned_data
from .experiment import ExperimentConfig, evaluate


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BEIJING = timezone(timedelta(hours=8))
LIMITATIONS = [
    "Exploratory engineering only; team confirmation of modeling and validation is pending.",
    "Targets are the 50 observed standardized columns in attachment 4, not original 0-6 scores.",
    "Targets were standardized per taster and aggregated; complete raw ratings/parameters are unavailable.",
    "Targets include 26 numeric and 24 parent-intensity-derived descriptors; no binary interpretation is used.",
    "Single shuffled KFold is neither style-stratified nor brewery-grouped nor external validation.",
    "No hyperparameter selection or statistical significance claim; alpha is fixed in the config.",
    "Small style slices describe errors only; no reliable style-specific inference is claimed.",
    "No inverse chemical transforms, threshold checks, Top-3 or generation claims in this stage.",
    "No attachment 2/5/6/7/8 or existing SHAP/importance is used as model input or selection evidence.",
]


def now_beijing() -> str:
    return datetime.now(BEIJING).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def log_event(output: Path, event: str, **details: object) -> None:
    with (output / "execution_log.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"at_utc_plus_8": now_beijing(), "event": event, **details},
                                ensure_ascii=False, allow_nan=False) + "\n")


def source_files(root: Path) -> list[Path]:
    paths = [root / "pyproject.toml", root / "requirements.txt"]
    for directory, pattern in (("src", "*.py"), ("scripts", "*.py"),
                               ("tests", "*.py"), ("configs", "*.json")):
        paths.extend((root / directory).rglob(pattern))
    return sorted(path for path in paths if path.is_file())


def source_manifest(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in source_files(root)}


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def git_evidence(root: Path) -> dict:
    scope = ["src", "scripts", "tests", "configs", "pyproject.toml", "requirements.txt"]

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              timeout=15, check=False)

    try:
        revision = git("rev-parse", "--verify", "HEAD")
        head = revision.stdout.decode("utf-8", errors="replace").strip() if revision.returncode == 0 else None
        status = git("status", "--porcelain=v1", "--untracked-files=all", "--", *scope)
        diff_args = ["diff", "--binary", "--no-ext-diff"] + (["HEAD"] if head else [])
        diff = git(*diff_args, "--", *scope)
        return {
            "head": head,
            "scoped_status": status.stdout.decode("utf-8", errors="replace"),
            "tracked_diff_sha256": hashlib.sha256(diff.stdout).hexdigest(),
            "status_returncode": status.returncode, "diff_returncode": diff.returncode,
            "note": "Untracked file contents are covered by source_manifest and source_snapshot.",
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"head": None, "error": str(exc)}


def environment() -> dict:
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl", "pytest",
                 "joblib", "python-dateutil", "pytz", "tzdata", "six", "setuptools"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "cpu_count": os.cpu_count(), "packages": packages,
        "threadpool_info": threadpool_info(), "fit_thread_limit": 1,
    }


def evidence_context(root: Path) -> dict:
    """Freeze context identity without feeding evidence tables into model fitting."""
    references = {}
    for relative in ("research/target-dictionary.csv", "research/chemical-units.csv",
                     "research/scoring-scale-investigation.md", "research/target-unit-findings.md",
                     "docs/TEAM_PROTOCOL.md", "docs/ARCHITECTURE.md", "AGENTS.md"):
        path = root / relative
        references[relative] = {"sha256": sha256_file(path)} if path.is_file() else {"status": "missing"}
    return {"used_as_model_input": False, "references": references}


def run_experiment(features_path: Path, targets_path: Path, config_path: Path,
                   output_root: Path, run_id: str | None = None) -> Path:
    # Parsing invalid configuration does not start a training run.
    config_raw = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(config_raw, dict):
        raise ValueError("Config must be a JSON object")
    config = ExperimentConfig(**config_raw)
    output_root = output_root.resolve()
    if not output_root.is_relative_to(PROJECT_ROOT / "runs"):
        raise ValueError("output-root must be within this project's runs directory")
    run_id = run_id or ("A-" + datetime.now(BEIJING).strftime("%Y%m%dT%H%M%S%f+0800") + "-" + uuid4().hex[:8])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+\-]{0,100}", run_id):
        raise ValueError("Invalid run_id; use up to 101 safe ASCII characters")
    output = output_root / run_id
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    record = {
        "run_id": run_id, "status": "running", "started_at_utc_plus_8": now_beijing(),
        "purpose": "AI-assisted engineering baseline and one fixed exploratory Ridge candidate",
        "owner": "A mainline engineering (AI-assisted; not an independent human review)",
        "hypothesis": "Check whether a fixed regularized chemical predictor improves over train-target means on observed standardized targets.",
        "team_modeling_approval": "pending", "official_final_output": False,
        "target_scale": "observed_standardized_unverified_inverse",
        "validation_version": config.validation_version, "config": asdict(config),
        "metric_version": config.metric_version,
        "argv": sys.argv, "cwd": str(Path.cwd()), "output": str(output),
        "execution_log": "execution_log.jsonl",
        "limitations": LIMITATIONS,
    }
    write_json(output / "manifest.json", record)
    try:
        log_event(output, "run_started", run_id=run_id)
        inputs = {name: {"path": str(path.resolve()), "sha256": sha256_file(path)}
                  for name, path in (("features", features_path), ("targets", targets_path),
                                     ("requested_config", config_path))}
        record["inputs"] = inputs
        sources = source_manifest(PROJECT_ROOT)
        record["code"] = {
            "source_manifest": sources, "source_fingerprint_sha256": fingerprint(sources),
            "git": git_evidence(PROJECT_ROOT),
        }
        record["code"]["uncommitted_state_fingerprint_sha256"] = fingerprint(record["code"])
        for relative in sources:
            destination = output / "source_snapshot" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT_ROOT / relative, destination)
        shutil.copyfile(config_path, output / "requested_config.json")
        record["environment"] = environment()
        record["evidence_context"] = evidence_context(PROJECT_ROOT)
        write_json(output / "resolved_config.json", asdict(config))
        write_json(output / "manifest.json", record)
        log_event(output, "loading_and_validating_inputs")
        data = load_aligned_data(features_path, targets_path,
                                 expected_samples=config.expected_samples,
                                 expected_features=config.expected_features,
                                 expected_targets=config.expected_targets)
        write_json(output / "data_audit.json", data.audit)
        log_event(output, "inputs_validated", samples=len(data.X), features=data.X.shape[1],
                  targets=data.y.shape[1])
        log_event(output, "evaluation_started", n_splits=config.n_splits, seed=config.seed)
        result = evaluate(data, config, output)
        write_json(output / "preprocessing_by_fold.json", {
            "feature_order": data.X.columns.tolist(),
            "empty_training_column_policy": "keep feature, impute 0; scaler fit on training rows",
            "folds": result["preprocessing"],
        })
        write_json(output / "summary.json", {
            "run_id": run_id, "target_scale": record["target_scale"],
            "validation_version": config.validation_version,
            "metric_version": config.metric_version,
            "metrics": result["metrics"], "limitations": LIMITATIONS,
        })
        for entry in inputs.values():
            if sha256_file(Path(entry["path"])) != entry["sha256"]:
                raise RuntimeError(f"Input changed during run: {entry['path']}")
        if source_manifest(PROJECT_ROOT) != sources:
            raise RuntimeError("Source files changed during run; this run is not reproducibly frozen")
        record["folds_sha256"] = sha256_file(output / "folds.csv")
        record["metrics"] = result["metrics"]
        record["status"] = "completed"
        log_event(output, "run_completed")
    except Exception as exc:
        record["status"] = "failed"
        record["error"] = {"type": type(exc).__name__, "message": str(exc)}
        (output / "error_traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        log_event(output, "run_failed", error_type=type(exc).__name__, message=str(exc))
        raise
    finally:
        record["ended_at_utc_plus_8"] = now_beijing()
        record["elapsed_seconds"] = time.perf_counter() - started
        record["artifacts_sha256"] = {
            path.relative_to(output).as_posix(): sha256_file(path)
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
        write_json(output / "manifest.json", record)
    return output
