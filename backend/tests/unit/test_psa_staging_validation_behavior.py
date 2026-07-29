# backend/tests/unit/test_psa_staging_validation_behavior.py
"""PSA staging validation — local behavior probes (not production logic).

Documents what operators check on dogfood PR #63 after each push:
- two-block issue comment (`### This generation` + `### Still open on PR`)
- `summary_json.generation_active_count` vs `pr_active_count`
- inline thread count ≈ generation block rows
"""
import importlib.util
from pathlib import Path

_PSA_STAGING_PROBE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "psa_staging" / "probe_module.py"
)


def _load_probe_module():
    spec = importlib.util.spec_from_file_location(
        "psa_staging_probe_module",
        _PSA_STAGING_PROBE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_psa_staging_probe_module_returns_wired_marker():
    probe = _load_probe_module()
    assert probe.psa_staging_probe_value() == "psa-staging-ok:psa-dogfood-push-2"


def test_psa_staging_probe_fixture_path_exists():
    assert _PSA_STAGING_PROBE_PATH.is_file()

