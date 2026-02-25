#!/bin/bash

# 停止事件驅動系統

# 切換到 Python 腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(cd "$SCRIPT_DIR/../../workspace/tools/repository-understanding" && pwd)"
cd "$TOOLS_DIR"

if [ -f pids/event-driven.pid ]; then
    PID=$(cat pids/event-driven.pid)
    echo "🛑 停止事件驅動系統 (PID: $PID)..."
    
    if kill $PID 2>/dev/null; then
        # 等待進程終止
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ 系統已停止"
                rm pids/event-driven.pid
                exit 0
            fi
            sleep 1
        done
        
        # 強制終止
        echo "⚠️  強制終止進程..."
        kill -9 $PID 2>/dev/null
        rm pids/event-driven.pid
        echo "✅ 系統已強制停止"
    else
        echo "⚠️  進程不存在"
        rm pids/event-driven.pid
    fi
else
    echo "⚠️  系統未運行"
fi
