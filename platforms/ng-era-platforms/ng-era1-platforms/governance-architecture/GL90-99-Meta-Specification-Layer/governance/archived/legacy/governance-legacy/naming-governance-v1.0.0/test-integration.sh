#!/bin/bash
# 集成測試腳本 - 驗證命名治理系統所有組件

echo "=========================================="
echo "命名治理系統 v1.0.0 - 集成測試"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試計數器
TESTS_PASSED=0
TESTS_FAILED=0

# 測試函數
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "測試: $test_name ... "
    
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✅ 通過${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失敗${NC}"
        echo "錯誤信息:"
        cat /tmp/test_output.log | head -5
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Python 語法驗證
echo "1. Python 腳本語法驗證"
run_test "naming_generator.py 語法" "python3 -m py_compile scripts/generation/naming_generator.py"
run_test "naming_validator.py 語法" "python3 -m py_compile scripts/validation/naming_validator.py"
run_test "change_manager.py 語法" "python3 -m py_compile scripts/audit/change_manager.py"
run_test "exception_manager.py 語法" "python3 -m py_compile scripts/audit/exception_manager.py"
echo ""

# 2. YAML 配置文件驗證
echo "2. YAML 配置文件驗證"
run_test "machine-spec.yaml 格式" "python3 -c &quot;import yaml; yaml.safe_load(open('config/machine-spec.yaml'))&quot;"
run_test "roles-curriculum.yaml 格式" "python3 -c &quot;import yaml; yaml.safe_load(open('training/modules/roles-curriculum.yaml'))&quot;"
echo ""

# 3. 命名生成器測試
echo "3. 命名生成器功能測試"
run_test "生成標準資源名稱" "python3 scripts/generation/naming_generator.py --environment prod --app payment --resource-type deploy --version v1.2.3 --tenant finance --output /tmp/test-generated.yaml"
echo ""

# 4. 命名驗證器測試
echo "4. 命名驗證器功能測試"
run_test "驗證配置目錄" "python3 scripts/validation/naming_validator.py --spec config/machine-spec.yaml --directory config --format json --output /tmp/test-validation.json"
echo ""

# 5. 變更管理器測試
echo "5. 變更管理器功能測試"
run_test "創建 RFC 變更請求" "python3 scripts/audit/change_manager.py create --title '測試變更' --type standard --requester 'tester' --risk low --output /tmp/test-rfc.yaml"
run_test "驗證 RFC 文件" "python3 scripts/audit/change_manager.py validate --rfc /tmp/test-rfc.yaml"
echo ""

# 6. 例外管理器測試
echo "6. 例外管理器功能測試"
run_test "創建例外申請" "python3 scripts/audit/exception_manager.py create --applicant 'tester' --type '測試例外' --justification '集成測試' --risk low --expiry 2025-12-31 --db /tmp/test-exceptions.yaml"
echo ""

# 7. 監控配置驗證
echo "7. 監控配置驗證"
run_test "Prometheus 規則格式" "python3 -c &quot;import yaml; yaml.safe_load(open('monitoring/prometheus/naming-governance-rules.yaml'))&quot;"
run_test "Grafana Dashboard 格式" "python3 -c &quot;import json; json.load(open('monitoring/grafana/naming-governance-dashboard.json'))&quot;"
echo ""

# 8. CI/CD 配置驗證
echo "8. CI/CD 配置驗證"
run_test "GitHub Actions 工作流格式" "python3 -c &quot;import yaml; yaml.safe_load(open('ci-cd/workflows/naming-governance-ci.yml'))&quot;"
echo ""

# 9. 文檔完整性檢查
echo "9. 文檔完整性檢查"
run_test "README.md 存在" "test -f README.md"
run_test "CHANGELOG.md 存在" "test -f CHANGELOG.md"
run_test "實施指南存在" "test -f docs/guides/implementation-guide.md"
run_test "最佳實踐存在" "test -f docs/best-practices/naming-patterns.md"
echo ""

# 10. 目錄結構檢查
echo "10. 目錄結構檢查"
run_test "config 目錄" "test -d config"
run_test "scripts 目錄" "test -d scripts"
run_test "docs 目錄" "test -d docs"
run_test "monitoring 目錄" "test -d monitoring"
run_test "training 目錄" "test -d training"
run_test "ci-cd 目錄" "test -d ci-cd"
echo ""

# 測試結果總結
echo "=========================================="
echo -e "測試結果總結"
echo "=========================================="
echo -e "${GREEN}通過: $TESTS_PASSED${NC}"
echo -e "${RED}失敗: $TESTS_FAILED${NC}"
echo "總計: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有測試通過！系統驗證完成。${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 $TESTS_FAILED 個測試失敗，請檢查錯誤。${NC}"
    exit 1
fi