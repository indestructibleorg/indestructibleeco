# VSCode Plugin for MNGA

@ECO-governed
@ECO-layer: GL30-39
@ECO-semantic: platform-ide-vscode

## Overview

VSCode 插件，提供 MNGA 推理系統集成。

## Features

- 🔍 **智能代碼搜索** - 使用雙路檢索系統搜索代碼
- 📚 **文檔查詢** - 快速查詢內部和外部文檔
- 🤖 **AI 輔助** - 集成推理 API 提供智能建議
- 📊 **治理檢查** - 實時 GL 合規性檢查

## Installation

```bash
# 從 VSIX 安裝
code --install-extension mnga-vscode-0.1.0.vsix
```

## Configuration

```json
{
  "mnga.apiEndpoint": "http://localhost:8080",
  "mnga.enableInternalSearch": true,
  "mnga.enableExternalSearch": true,
  "mnga.maxResults": 10
}
```

## Commands

| Command | Description |
|---------|-------------|
| `MNGA: Search` | 執行雙路搜索 |
| `MNGA: Query Docs` | 查詢文檔 |
| `MNGA: Check Compliance` | 檢查 GL 合規性 |
| `MNGA: Submit Feedback` | 提交反饋 |

## Development

```bash
cd platforms/gov-platform-ide/plugins/vscode
npm install
npm run compile
npm run package
```

## API Integration

插件通過 REST API 與推理服務通信：

```typescript
// 查詢示例
const response = await fetch('http://localhost:8080/api/v1/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'how to implement authentication',
    type: 'code',
    options: { include_external: true }
  })
});
```

## License

MIT