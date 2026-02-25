#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: operational_test
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
FHS Integration System Operational Test
系統完整運作測試
這個測試腳本確保整個 FHS 整合系統能夠正確運作
"""
import sys
from pathlib import Path
# 添加工具目錄到路徑
REPO_ROOT = Path(__file__).parent.parent.parent.absolute()
FHS_TOOLS_DIR = REPO_ROOT / "workspace" / "tools" / "fhs-integration"
sys.path.insert(0, str(FHS_TOOLS_DIR))
# 顏色定義
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'
def print_test(name, passed):
    """打印測試結果"""
    if passed:
        print(f"{Colors.GREEN}✓{Colors.NC} {name}")
    else:
        print(f"{Colors.RED}✗{Colors.NC} {name}")
    return passed
def main():
    """主測試函數"""
    print("=" * 60)
    print("FHS Integration System Operational Test")
    print("=" * 60)
    print("")
    tests_passed = 0
    tests_failed = 0
    # 測試 1: 導入模組
    print(f"{Colors.YELLOW}[1/5] Module Import Tests{Colors.NC}")
    try:
        from maturity_assessor import MaturityAssessor
        tests_passed += print_test("Import MaturityAssessor", True)
    except Exception as e:
        tests_failed += print_test(f"Import MaturityAssessor: {e}", False)
    try:
        from fhs_integrator import FHSIntegrator
        tests_passed += print_test("Import FHSIntegrator", True)
    except Exception as e:
        tests_failed += print_test(f"Import FHSIntegrator: {e}", False)
    try:
        from fhs_validator import FHSIntegrationValidator
        tests_passed += print_test("Import FHSIntegrationValidator", True)
    except Exception as e:
        tests_failed += print_test(f"Import FHSIntegrationValidator: {e}", False)
    try:
        from fhs_automation_master import FHSAutomationMaster
        tests_passed += print_test("Import FHSAutomationMaster", True)
    except Exception as e:
        tests_failed += print_test(f"Import FHSAutomationMaster: {e}", False)
    # 測試 2: 實例化
    print(f"\n{Colors.YELLOW}[2/5] Instantiation Tests{Colors.NC}")
    try:
        from maturity_assessor import MaturityAssessor
        assessor = MaturityAssessor(repo_root=str(REPO_ROOT))
        tests_passed += print_test("Create MaturityAssessor instance", True)
    except Exception as e:
        tests_failed += print_test(f"Create MaturityAssessor instance: {e}", False)
    try:
        from fhs_integrator import FHSIntegrator
        FHSIntegrator(repo_root=str(REPO_ROOT), dry_run=True)
        tests_passed += print_test("Create FHSIntegrator instance", True)
    except Exception as e:
        tests_failed += print_test(f"Create FHSIntegrator instance: {e}", False)
    try:
        from fhs_validator import FHSIntegrationValidator
        validator = FHSIntegrationValidator(repo_root=str(REPO_ROOT))
        tests_passed += print_test("Create FHSIntegrationValidator instance", True)
    except Exception as e:
        tests_failed += print_test(f"Create FHSIntegrationValidator instance: {e}", False)
    # 測試 3: 成熟度評估
    print(f"\n{Colors.YELLOW}[3/5] Maturity Assessment Tests{Colors.NC}")
    try:
        from maturity_assessor import MaturityAssessor
        assessor = MaturityAssessor(repo_root=str(REPO_ROOT))
        # 評估一個已知組件
        assessment = assessor.assess_component("fhs-integration", verbose=False)
        if "error" not in assessment:
            tests_passed += print_test("Assess fhs-integration component", True)
            # 驗證評估結果結構
            required_keys = ["component", "total_score", "maturity_level"]
            has_all_keys = all(k in assessment for k in required_keys)
            tests_passed += print_test("Assessment result structure valid", has_all_keys)
            if not has_all_keys:
                tests_failed += 1
        else:
            tests_failed += print_test(f"Assess fhs-integration: {assessment['error']}", False)
    except Exception as e:
        tests_failed += print_test(f"Maturity assessment: {e}", False)
    # 測試 4: 驗證功能
    print(f"\n{Colors.YELLOW}[4/5] Validation Tests{Colors.NC}")
    try:
        from fhs_validator import FHSIntegrationValidator
        validator = FHSIntegrationValidator(repo_root=str(REPO_ROOT))
        # 創建測試計劃
        test_plan = {
            "maturity_score": 85,
            "actions": [
                "Create wrapper: bin/mno-test",
                "Copy library file: test.py -> lib/test-component/test.py"
            ],
            "structure": {
                "python_files": ["test.py"],
                "config_files": []
            }
        }
        # 執行驗證
        report = validator.validate_integration("test-component", test_plan)
        if "checks" in report:
            tests_passed += print_test("Validation execution successful", True)
        else:
            tests_failed += print_test("Validation execution failed", False)
    except Exception as e:
        tests_failed += print_test(f"Validation test: {e}", False)
    # 測試 5: 批量評估
    print(f"\n{Colors.YELLOW}[5/5] Batch Assessment Test{Colors.NC}")
    try:
        from fhs_automation_master import FHSAutomationMaster
        master = FHSAutomationMaster(repo_root=str(REPO_ROOT), threshold=80)
        result = master.run_full_assessment()
        if "assessments" in result and "categorized" in result:
            tests_passed += print_test("Batch assessment successful", True)
            # 顯示評估統計
            categorized = result["categorized"]
            total = sum(len(v) for v in categorized.values())
            print(f"  └─ Assessed {total} components")
        else:
            tests_failed += print_test("Batch assessment failed", False)
    except Exception as e:
        tests_failed += print_test(f"Batch assessment: {e}", False)
    # 總結
    print("")
    print("=" * 60)
    print("Test Summary:")
    print(f"  Passed: {tests_passed}")
    print(f"  Failed: {tests_failed}")
    if tests_failed == 0:
        print(f"{Colors.GREEN}✓ All tests passed - System fully operational{Colors.NC}")
        return 0
    else:
        print(f"{Colors.RED}✗ {tests_failed} test(s) failed{Colors.NC}")
        return 1
if __name__ == "__main__":
    sys.exit(main())
