#!/bin/bash

# 重啟事件驅動系統

# 切換到腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 重啟事件驅動系統..."

# 停止系統
"$SCRIPT_DIR/stop_event_driven.sh"

# 等待一秒
sleep 1

# 啟動系統
"$SCRIPT_DIR/start_event_driven.sh"

echo "✅ 系統已重啟"
