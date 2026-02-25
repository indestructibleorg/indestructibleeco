"""Test gate domain entity."""

from domain.entities.gate import Gate, GateCondition, GateStatus, GateType


def test_gate_creation():
    g = Gate(name="deploy-check", gate_type=GateType.PRE_DEPLOY)
    assert g.name == "deploy-check"
    assert g.gate_type == GateType.PRE_DEPLOY
    assert g.status == GateStatus.CLOSED


def test_gate_evaluate_no_conditions_passes():
    g = Gate(name="empty-gate", gate_type=GateType.COMPLIANCE)
    result = g.evaluate({})
    assert result is True
    assert g.status == GateStatus.OPEN


def test_gate_evaluate_conditions_pass():
    cond = GateCondition(field="compliance.score", operator="gte", value=90)
    g = Gate(name="score-gate", gate_type=GateType.COMPLIANCE, conditions=[cond])
    result = g.evaluate({"compliance": {"score": 95}})
    assert result is True
    assert g.status == GateStatus.OPEN


def test_gate_evaluate_conditions_fail():
    cond = GateCondition(field="compliance.score", operator="gte", value=90)
    g = Gate(name="score-gate", gate_type=GateType.COMPLIANCE, conditions=[cond])
    result = g.evaluate({"compliance": {"score": 70}})
    assert result is False
    assert g.status == GateStatus.CLOSED


def test_gate_blocked_skips_eval():
    cond = GateCondition(field="score", operator="gte", value=0)
    g = Gate(name="blocked", gate_type=GateType.SECURITY, conditions=[cond])
    g.block("security incident")
    assert g.status == GateStatus.BLOCKED
    result = g.evaluate({"score": 100})
    assert result is False
    assert g.status == GateStatus.BLOCKED


def test_gate_override():
    g = Gate(name="overridable", gate_type=GateType.POST_DEPLOY)
    g.block("maintenance window")
    g.override("admin@example.com")
    assert g.status == GateStatus.OVERRIDDEN
    assert g.override_approver == "admin@example.com"
    assert g.override_at is not None
    assert g.block_reason == ""


def test_gate_status_allows_passage():
    assert GateStatus.OPEN.allows_passage is True
    assert GateStatus.OVERRIDDEN.allows_passage is True
    assert GateStatus.CLOSED.allows_passage is False
    assert GateStatus.BLOCKED.allows_passage is False


def test_gate_condition_operators():
    assert GateCondition(field="x", operator="eq", value=5).evaluate({"x": 5}) is True
    assert GateCondition(field="x", operator="neq", value=5).evaluate({"x": 3}) is True
    assert GateCondition(field="x", operator="gt", value=5).evaluate({"x": 6}) is True
    assert GateCondition(field="x", operator="lt", value=5).evaluate({"x": 4}) is True
    assert GateCondition(field="x", operator="lte", value=5).evaluate({"x": 5}) is True
    assert GateCondition(field="x", operator="in", value=[1, 2, 3]).evaluate({"x": 2}) is True
    assert GateCondition(field="x", operator="not_in", value=[1, 2]).evaluate({"x": 3}) is True
    assert GateCondition(field="x", operator="contains", value="bc").evaluate({"x": "abcd"}) is True


def test_gate_condition_missing_field():
    cond = GateCondition(field="missing.path", operator="eq", value=1)
    assert cond.evaluate({"other": 1}) is False


def test_gate_condition_unknown_operator():
    cond = GateCondition(field="x", operator="invalid_op", value=1)
    assert cond.evaluate({"x": 1}) is False


def test_gate_condition_nested_resolution():
    cond = GateCondition(field="a.b.c", operator="eq", value=42)
    assert cond.evaluate({"a": {"b": {"c": 42}}}) is True
    assert cond.evaluate({"a": {"b": {"c": 0}}}) is False


def test_gate_add_condition():
    g = Gate(name="dynamic", gate_type=GateType.COMPLIANCE)
    assert len(g.conditions) == 0
    g.add_condition(GateCondition(field="x", operator="eq", value=1))
    assert len(g.conditions) == 1


def test_gate_summary():
    g = Gate(name="summary-gate", gate_type=GateType.SECURITY)
    s = g.summary()
    assert s["name"] == "summary-gate"
    assert s["type"] == "security"
    assert s["status"] == "closed"
    assert s["condition_count"] == 0


def test_gate_type_values():
    assert GateType.PRE_DEPLOY.value == "pre_deploy"
    assert GateType.POST_DEPLOY.value == "post_deploy"
    assert GateType.COMPLIANCE.value == "compliance"
    assert GateType.SECURITY.value == "security"
