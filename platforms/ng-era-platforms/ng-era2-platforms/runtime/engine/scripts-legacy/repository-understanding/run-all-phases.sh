#!/bin/bash

# 自動化儲存庫理解系統 - 一鍵執行腳本
# 執行所有四個階段並生成完整報告

set -e  # 遇到錯誤立即退出

# 切換到 Python 腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(cd "$SCRIPT_DIR/../../workspace/tools/repository-understanding" && pwd)"
cd "$TOOLS_DIR"

echo "============================================================"
echo "🚀 自動化儲存庫理解系統"
echo "============================================================"
echo "📍 工作目錄: $TOOLS_DIR"
echo ""

# 顯示開始時間
START_TIME=$(date +%s)
echo "⏰ 開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 第一階段：儲存庫掃描和知識庫建立
echo "============================================================"
echo "📊 第一階段：儲存庫掃描和知識庫建立"
echo "============================================================"
echo ""

if python3 phase1_scanner.py; then
    echo "✅ 第一階段完成"
else
    echo "❌ 第一階段失敗"
    exit 1
fi

echo ""
echo "============================================================"
echo "🛡️  第二階段：操作前的檢查機制"
echo "============================================================"
echo ""

if python3 phase2_operation_checker.py; then
    echo "✅ 第二階段完成"
else
    echo "❌ 第二階段失敗"
    exit 1
fi

echo ""
echo "============================================================"
echo "🔍 第三階段：視覺化與查詢系統"
echo "============================================================"
echo ""

if python3 phase3_visualizer.py; then
    echo "✅ 第三階段完成"
else
    echo "❌ 第三階段失敗"
    exit 1
fi

echo ""
echo "============================================================"
echo "🧠 第四階段：持續學習機制"
echo "============================================================"
echo ""

if python3 phase4_learning_system.py; then
    echo "✅ 第四階段完成"
else
    echo "❌ 第四階段失敗"
    exit 1
fi

# 計算執行時間
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "============================================================"
echo "🎉 所有階段執行完成！"
echo "============================================================"
echo ""
echo "⏰ 結束時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo "⏱️  總執行時間: ${MINUTES} 分 ${SECONDS} 秒"
echo ""
echo "📁 生成的報告："
echo "   - phase1_report.md"
echo "   - phase2_report.md"
echo "   - phase3_report.md"
echo "   - phase4_report.md"
echo "   - PHASES_COMPLETION_SUMMARY.md"
echo ""
echo "💾 核心檔案："
echo "   - knowledge_base.json (完整知識庫)"
echo ""
echo "🔧 系統檔案："
echo "   - phase1_scanner.py"
echo "   - phase2_operation_checker.py"
echo "   - phase3_visualizer.py"
echo "   - phase4_learning_system.py"
echo ""
echo "📖 文檔："
echo "   - AUTOMATED_REPOSITORY_UNDERSTANDING_SYSTEM.md"
echo ""
echo "✨ 系統已就緒，可以開始使用！"
echo "============================================================"