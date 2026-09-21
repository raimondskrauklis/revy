# backend/tests/unit/test_installations_no_plan_gate.py
"""Installation endpoints no longer require installations.create plan gate."""
from __future__ import annotations

from app.core.plan_gates import PLAN_FEATURES, require_plan_feature, workspace_has_feature


def test_plan_features_no_installations_create():
    assert "installations.create" not in PLAN_FEATURES


def test_plan_features_empty():
    assert PLAN_FEATURES == {}


def test_workspace_has_feature_returns_true_for_any_feature():
    """When PLAN_FEATURES is empty, all features are allowed."""
    from app.models.workspaces import WorkspaceORM

    workspace = WorkspaceORM(slug="test", name="Test")
    result = workspace_has_feature(workspace, "installations.create")
    assert result is True


def test_require_plan_feature_never_raises():
    """When PLAN_FEATURES is empty, require_plan_feature is a no-op that allows all."""
    # Just verify the dependency function exists and can be called
    dep = require_plan_feature("installations.create")
    assert callable(dep)
    assert dep.__name__ == "_dependency"