#!/bin/bash

# 查看事件驅動系統日誌

# 切換到 Python 腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(cd "$SCRIPT_DIR/../../workspace/tools/repository-understanding" && pwd)"
cd "$TOOLS_DIR"

if [ -f logs/event-driven.log ]; then
    echo "📝 事件驅動系統日誌 (最近50行):"
    echo "============================================================"
    tail -n 50 logs/event-driven.log
    echo "============================================================"
    echo ""
    echo "💡 持續監控: tail -f $TOOLS_DIR/logs/event-driven.log"
else
    echo "⚠️  日誌檔案不存在"
fi
