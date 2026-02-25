#!/bin/bash
# FHS Integration System Initialization Script
# 初始化 FHS 整合系統，確保所有組件正確配置
#
# Usage:
#     ./init_fhs_integration.sh
#     ./init_fhs_integration.sh --verify-only

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FHS_TOOLS_DIR="$REPO_ROOT/workspace/tools/fhs-integration"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}FHS Integration System Initialization${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 階段 1: 環境檢查
echo -e "${YELLOW}[1/6] Environment Checks${NC}"
echo "Repository root: $REPO_ROOT"
echo "FHS tools directory: $FHS_TOOLS_DIR"

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
else
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"
fi

# 檢查必要的 Python 模組
echo "Checking Python dependencies..."
python3 -c "import yaml" 2>/dev/null && echo -e "${GREEN}✓ PyYAML available${NC}" || echo -e "${YELLOW}⚠ PyYAML not found (optional)${NC}"

# 階段 2: 目錄結構驗證
echo ""
echo -e "${YELLOW}[2/6] Directory Structure Validation${NC}"

REQUIRED_DIRS=(
    "bin"
    "sbin"
    "lib"
    "etc"
    "etc/systemd"
    "workspace/tools"
    "scripts"
    "docs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        echo -e "${GREEN}✓ $dir/${NC}"
    else
        echo -e "${RED}✗ $dir/ missing${NC}"
        echo "  Creating directory: $dir"
        mkdir -p "$REPO_ROOT/$dir"
        echo -e "${GREEN}✓ Created $dir/${NC}"
    fi
done

# 階段 3: FHS 整合工具驗證
echo ""
echo -e "${YELLOW}[3/6] FHS Integration Tools Validation${NC}"

REQUIRED_FILES=(
    "maturity_assessor.py"
    "fhs_integrator.py"
    "fhs_validator.py"
    "fhs_automation_master.py"
    "maturity-criteria.yaml"
    "README.md"
)

cd "$FHS_TOOLS_DIR"
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
        
        # 檢查 Python 文件語法
        if [[ "$file" == *.py ]]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                echo "  └─ Syntax OK"
            else
                echo -e "${RED}  └─ Syntax error in $file${NC}"
                exit 1
            fi
        fi
        
        # 確保 Python 文件可執行
        if [[ "$file" == *.py ]]; then
            if [ ! -x "$file" ]; then
                chmod +x "$file"
                echo "  └─ Made executable"
            fi
        fi
    else
        echo -e "${RED}✗ $file missing${NC}"
        exit 1
    fi
done

# 階段 4: 文檔驗證
echo ""
echo -e "${YELLOW}[4/6] Documentation Validation${NC}"

DOCS_DIR="$REPO_ROOT/docs/fhs-integration"
if [ ! -d "$DOCS_DIR" ]; then
    mkdir -p "$DOCS_DIR"
    echo -e "${GREEN}✓ Created $DOCS_DIR${NC}"
fi

DOC_FILES=(
    "FHS_AUTOMATION_SOLUTION.md"
    "VALIDATION_MECHANISM.md"
)

for doc in "${DOC_FILES[@]}"; do
    if [ -f "$DOCS_DIR/$doc" ]; then
        echo -e "${GREEN}✓ $doc${NC}"
    else
        echo -e "${YELLOW}⚠ $doc not found${NC}"
    fi
done

# 階段 5: 功能測試
echo ""
echo -e "${YELLOW}[5/6] Functional Tests${NC}"

# 測試成熟度評估器
echo "Testing maturity assessor..."
if python3 "$FHS_TOOLS_DIR/maturity_assessor.py" --help &>/dev/null; then
    echo -e "${GREEN}✓ Maturity assessor functional${NC}"
else
    echo -e "${RED}✗ Maturity assessor failed${NC}"
    exit 1
fi

# 測試 FHS 整合器
echo "Testing FHS integrator..."
if python3 "$FHS_TOOLS_DIR/fhs_integrator.py" --help &>/dev/null; then
    echo -e "${GREEN}✓ FHS integrator functional${NC}"
else
    echo -e "${RED}✗ FHS integrator failed${NC}"
    exit 1
fi

# 測試驗證器
echo "Testing FHS validator..."
if python3 "$FHS_TOOLS_DIR/fhs_validator.py" --help &>/dev/null; then
    echo -e "${GREEN}✓ FHS validator functional${NC}"
else
    echo -e "${RED}✗ FHS validator failed${NC}"
    exit 1
fi

# 測試主控器
echo "Testing automation master..."
if python3 "$FHS_TOOLS_DIR/fhs_automation_master.py" --help &>/dev/null; then
    echo -e "${GREEN}✓ Automation master functional${NC}"
else
    echo -e "${RED}✗ Automation master failed${NC}"
    exit 1
fi

# 階段 6: 快速評估測試
if [ "$1" != "--verify-only" ]; then
    echo ""
    echo -e "${YELLOW}[6/6] Running Quick Assessment${NC}"
    
    cd "$FHS_TOOLS_DIR"
    echo "Assessing all workspace components..."
    
    if python3 fhs_automation_master.py --assess-all > /tmp/fhs-assessment.txt 2>&1; then
        echo -e "${GREEN}✓ Assessment completed successfully${NC}"
        
        # 顯示摘要
        echo ""
        echo "Assessment Summary:"
        grep -A 10 "SUMMARY" /tmp/fhs-assessment.txt || echo "  (Summary not found in output)"
    else
        echo -e "${YELLOW}⚠ Assessment completed with warnings${NC}"
        echo "  See /tmp/fhs-assessment.txt for details"
    fi
else
    echo ""
    echo -e "${YELLOW}[6/6] Skipped (--verify-only mode)${NC}"
fi

# 完成
echo ""
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}✓ Initialization Complete${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo "FHS Integration System is ready to use."
echo ""
echo "Quick Start Commands:"
echo "  # Assess a component"
echo "  python3 $FHS_TOOLS_DIR/maturity_assessor.py <component-name>"
echo ""
echo "  # Assess all components"
echo "  python3 $FHS_TOOLS_DIR/fhs_automation_master.py --assess-all"
echo ""
echo "  # Integrate a component (dry-run)"
echo "  python3 $FHS_TOOLS_DIR/fhs_integrator.py <component-name>"
echo ""
echo "  # View documentation"
echo "  cat $DOCS_DIR/VALIDATION_MECHANISM.md"
echo ""
