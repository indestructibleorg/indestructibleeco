#!/bin/bash

# 啟動事件驅動系統

# 切換到 Python 腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(cd "$SCRIPT_DIR/../../workspace/tools/repository-understanding" && pwd)"
cd "$TOOLS_DIR"

# 建立必要的目錄
mkdir -p logs pids

# 檢查是否已經運行
if [ -f pids/event-driven.pid ]; then
    PID=$(cat pids/event-driven.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  系統已經在運行 (PID: $PID)"
        echo "使用 '$SCRIPT_DIR/stop_event_driven.sh' 來停止系統"
        exit 1
    else
        rm pids/event-driven.pid
    fi
fi

# 啟動系統
echo "🚀 啟動事件驅動系統..."
echo "📍 工作目錄: $TOOLS_DIR"
nohup python3 -u event_driven_system.py > logs/event-driven.log 2>&1 &
echo $! > pids/event-driven.pid

echo "✅ 系統已啟動 (PID: $!)"
echo "📊 日誌文件: $TOOLS_DIR/logs/event-driven.log"
echo "🔍 查看狀態: tail -f $TOOLS_DIR/logs/event-driven.log"
echo "⏹️  停止系統: $SCRIPT_DIR/stop_event_driven.sh"
