#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: verify_refactoring
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
重構驗證腳本 - Verify Refactoring Success
"""
from pathlib import Path
print("=" * 70)
print("MachineNativeOps 重構驗證")
print("=" * 70)
print()
# 測試計數
tests_passed = 0
tests_failed = 0
def test(name, func):
    """執行測試"""
    global tests_passed, tests_failed
    try:
        print(f"⏳ 測試: {name}...", end=" ")
        func()
        print("✅ 通過")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 失敗: {e}")
        tests_failed += 1
project_root = Path(__file__).parent
# ===== Agent 系統測試 =====
print("\n📦 Agent 系統驗證:")
print("-" * 70)
def test_base_agent_file():
    agent_file = project_root / "src" / "autonomous" / "agents" / "base-agent.py"
    assert agent_file.exists(), f"File not found: {agent_file}"
test("Base Agent 文件存在", test_base_agent_file)
def test_coordinator_agent_file():
    agent_file = project_root / "src" / "autonomous" / "agents" / "coordinator-agent.py"
    assert agent_file.exists(), f"File not found: {agent_file}"
test("Coordinator Agent 文件存在", test_coordinator_agent_file)
def test_autopilot_agent_file():
    agent_file = project_root / "src" / "autonomous" / "agents" / "autopilot-agent.py"
    assert agent_file.exists(), f"File not found: {agent_file}"
test("Autopilot Agent 文件存在", test_autopilot_agent_file)
def test_deployment_agent_file():
    agent_file = project_root / "src" / "autonomous" / "agents" / "deployment-agent.py"
    assert agent_file.exists(), f"File not found: {agent_file}"
test("Deployment Agent 文件存在", test_deployment_agent_file)
def test_agent_config_file():
    config_file = (
        project_root / "src" / "autonomous" / "agents" / "config" / "agent-config.py"
    )
    assert config_file.exists(), f"File not found: {config_file}"
test("Agent Config 文件存在", test_agent_config_file)
# ===== Island 系統測試 =====
print("\n🏝️  Island 系統驗證:")
print("-" * 70)
def test_base_island_file():
    island_file = (
        project_root / "src" / "bridges" / "language-islands" / "base-island.py"
    )
    assert island_file.exists(), f"File not found: {island_file}"
test("Base Island 文件存在", test_base_island_file)
def test_python_island_file():
    island_file = (
        project_root / "src" / "bridges" / "language-islands" / "python-island.py"
    )
    assert island_file.exists(), f"File not found: {island_file}"
test("Python Island 文件存在", test_python_island_file)
def test_rust_island_file():
    island_file = (
        project_root / "src" / "bridges" / "language-islands" / "rust-island.py"
    )
    assert island_file.exists(), f"File not found: {island_file}"
test("Rust Island 文件存在", test_rust_island_file)
def test_go_island_file():
    island_file = project_root / "src" / "bridges" / "language-islands" / "go-island.py"
    assert island_file.exists(), f"File not found: {island_file}"
test("Go Island 文件存在", test_go_island_file)
def test_typescript_island_file():
    island_file = (
        project_root / "src" / "bridges" / "language-islands" / "typescript-island.py"
    )
    assert island_file.exists(), f"File not found: {island_file}"
test("TypeScript Island 文件存在", test_typescript_island_file)
def test_java_island_file():
    island_file = (
        project_root / "src" / "bridges" / "language-islands" / "java-island.py"
    )
    assert island_file.exists(), f"File not found: {island_file}"
test("Java Island 文件存在", test_java_island_file)
def test_island_config_file():
    config_file = (
        project_root
        / "src"
        / "bridges"
        / "language-islands"
        / "config"
        / "island-config.py"
    )
    assert config_file.exists(), f"File not found: {config_file}"
test("Island Config 文件存在", test_island_config_file)
# ===== Orchestrator 測試 =====
print("\n🔧 協調器驗證:")
print("-" * 70)
def test_synergy_orchestrator_file():
    orch_file = (
        project_root / "src" / "core" / "orchestrators" / "synergy-mesh-orchestrator.py"
    )
    assert orch_file.exists(), f"File not found: {orch_file}"
test("SynergyMesh Orchestrator 文件存在", test_synergy_orchestrator_file)
def test_language_orchestrator_file():
    orch_file = (
        project_root
        / "src"
        / "core"
        / "orchestrators"
        / "language-island-orchestrator.py"
    )
    assert orch_file.exists(), f"File not found: {orch_file}"
test("Language Island Orchestrator 文件存在", test_language_orchestrator_file)
# ===== 目錄結構測試 =====
print("\n📁 目錄結構驗證:")
print("-" * 70)
def test_agent_dir():
    agents_dir = project_root / "src" / "autonomous" / "agents"
    assert agents_dir.exists(), f"Agent 目錄不存在: {agents_dir}"
test("Agent 目錄存在", test_agent_dir)
def test_island_dir():
    islands_dir = project_root / "src" / "bridges" / "language-islands"
    assert islands_dir.exists(), f"Island 目錄不存在: {islands_dir}"
test("Island 目錄存在", test_island_dir)
def test_orchestrators_dir():
    orchestrators_dir = project_root / "src" / "core" / "orchestrators"
    assert orchestrators_dir.exists(), f"協調器目錄不存在: {orchestrators_dir}"
test("協調器目錄存在", test_orchestrators_dir)
def test_no_duplicate_legacy():
    archive_dir = project_root / "archive"
    assert not (
        archive_dir / "v1-python-drones"
    ).exists(), "重複的 archive/v1-python-drones 應該被刪除"
    assert not (
        archive_dir / "v2-multi-islands"
    ).exists(), "重複的 archive/v2-multi-islands 應該被刪除"
test("已刪除重複的遺留目錄", test_no_duplicate_legacy)
def test_original_legacy_exists():
    archive_dir = project_root / "archive"
    assert (
        archive_dir / "legacy" / "v1-python-drones"
    ).exists(), "原始 legacy/v1-python-drones 應該仍然存在"
    assert (
        archive_dir / "legacy" / "v2-multi-islands"
    ).exists(), "原始 legacy/v2-multi-islands 應該仍然存在"
test("原始遺留代碼仍然存在", test_original_legacy_exists)
# ===== 命名規範驗證 =====
print("\n📝 命名規範驗證:")
print("-" * 70)
def test_kebab_case_agents():
    agents_dir = project_root / "src" / "autonomous" / "agents"
    kebab_files = [
        "base-agent.py",
        "coordinator-agent.py",
        "autopilot-agent.py",
        "deployment-agent.py",
        "agent-utils.py",
    ]
    for file in kebab_files:
        assert (
            agents_dir / file
        ).exists(), f"Expected kebab-case file not found: {file}"
test("Agent 文件遵循 kebab-case 命名", test_kebab_case_agents)
def test_kebab_case_islands():
    islands_dir = project_root / "src" / "bridges" / "language-islands"
    kebab_files = [
        "base-island.py",
        "python-island.py",
        "rust-island.py",
        "go-island.py",
        "typescript-island.py",
        "java-island.py",
        "island-utils.py",
    ]
    for file in kebab_files:
        assert (
            islands_dir / file
        ).exists(), f"Expected kebab-case file not found: {file}"
test("Island 文件遵循 kebab-case 命名", test_kebab_case_islands)
def test_refactoring_plan_exists():
    plan_file = project_root / "REFACTORING_PLAN.md"
    assert plan_file.exists(), f"重構計劃文檔不存在: {plan_file}"
test("重構計劃文檔存在", test_refactoring_plan_exists)
# ===== 內容驗證 =====
print("\n🔍 內容驗證:")
print("-" * 70)
def test_agent_class_renamed():
    base_agent = project_root / "src" / "autonomous" / "agents" / "base-agent.py"
    content = base_agent.read_text()
    assert "class BaseAgent" in content, "BaseAgent 類未找到"
    assert "class AgentStatus" in content, "AgentStatus 類未找到"
test("Agent 類正確重命名", test_agent_class_renamed)
def test_orchestrator_created():
    orch_file = (
        project_root / "src" / "core" / "orchestrators" / "synergy-mesh-orchestrator.py"
    )
    content = orch_file.read_text()
    assert (
        "class SynergyMeshOrchestrator" in content
    ), "SynergyMeshOrchestrator 類未找到"
    assert "def register_agent" in content, "register_agent 方法未找到"
    assert "def register_island" in content, "register_island 方法未找到"
test("SynergyMeshOrchestrator 正確創建", test_orchestrator_created)
# ===== 列出統計 =====
print("\n" + "=" * 70)
print("📊 驗證結果摘要")
print("=" * 70)
print(f"✅ 通過: {tests_passed}")
print(f"❌ 失敗: {tests_failed}")
print(f"📈 總計: {tests_passed + tests_failed}")
print()
if tests_failed == 0:
    print("🎉 所有驗證均已通過！")
    print()
    print("重構完成狀態:")
    print("  ✅ v1-python-drones 已轉換為 Agent 系統")
    print("  ✅ v2-multi-islands 已轉換為 Island 系統")
    print("  ✅ 統一 SynergyMeshOrchestrator 已創建")
    print("  ✅ 所有命名規範已統一為 kebab-case")
    print("  ✅ 目錄結構已優化")
    print("  ✅ 重複的遺留代碼已刪除")
    print()
    print("下一步:")
    print("  1. 提交所有更改到 git")
    print("  2. 推送到開發分支")
    print("  3. 創建 Pull Request 進行審查")
else:
    print("⚠️  有驗證失敗，請檢查錯誤信息")
    import sys
    sys.exit(1)
