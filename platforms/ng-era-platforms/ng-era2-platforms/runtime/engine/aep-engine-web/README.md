# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# AEP Engine - Governance & Audit Web Application

> GL Layer: ECO-70-PRESENTATION | Semantic Anchor: ECO-70-PRESENTATION-WEB | GL Unified Architecture Governance Framework Activated

一個零配置、開箱即用的 Web 應用，用於 AEP Engine 治理與稽核。

## 功能特性

- ✅ **零配置部署** - 無需設定即可運行
- ✅ **響應式設計** - 適配所有設備（桌面、平板、手機）
- ✅ **暗黑模式** - 內置深色主題支持
- ✅ **模擬資料** - 完整的示例數據
- ✅ **五個主要螢幕**：
  - 首頁 (Home) - 稽核摘要與事件時間線
  - 稽核執行 (Audit) - ETL Pipeline 監控
  - 檢測結果 (Results) - 治理問題分類與建議
  - 全局報告 (Report) - 綜合統計與導出
  - 設定 (Settings) - 應用配置與偏好

## 目錄結構

```
engine/aep-engine-web/
├── src/
│   ├── components/          # UI 元件
│   │   ├── StatisticCard.tsx
│   │   ├── EventCard.tsx
│   │   └── ProblemCard.tsx
│   ├── screens/            # 頁面螢幕
│   │   ├── HomeScreen.tsx
│   │   ├── AuditScreen.tsx
│   │   ├── ResultsScreen.tsx
│   │   ├── ReportScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── hooks/              # React Hooks
│   │   └── useAppState.ts
│   ├── data/               # 模擬資料
│   │   └── mock.ts
│   ├── App.tsx             # 主應用元件
│   ├── main.tsx            # 應用入口
│   └── index.css           # 全局樣式
├── index.html              # HTML 入口
├── package.json            # 依賴配置
├── vite.config.ts          # Vite 配置
├── tailwind.config.js      # Tailwind 配置
├── tsconfig.json           # TypeScript 配置
├── vercel.json             # Vercel 部署配置
├── netlify.toml            # Netlify 部署配置
└── .gl-manifest.yaml       # GL 治理清單
```

## 快速開始

### 安裝依賴

```bash
cd engine/aep-engine-web
npm install
# 或
pnpm install
```

### 開發模式

```bash
npm run dev
# 或
pnpm dev
```

應用將在 `[EXTERNAL_URL_REMOVED] 啟動

### 生產構建

```bash
npm run build
# 或
pnpm build
```

構建產物將在 `dist/` 目錄中

### 預覽生產構建

```bash
npm run preview
# 或
pnpm preview
```

## 技術棧

| 類別 | 技術 |
|------|------|
| **框架** | React 18 + TypeScript |
| **構建工具** | Vite 4 |
| **樣式** | Tailwind CSS 3 |
| **圖標** | Lucide React |
| **狀態管理** | React Hooks |

## 部署

### Vercel

```bash
vercel deploy
```

### Netlify

```bash
netlify deploy --prod --dir dist
```

### GitHub Pages

```bash
npm run build
# 將 dist/ 目錄推送至 gh-pages 分支
```

## 與 Mobile App 的關係

此 Web 應用與 `engine/aep-engine-app` (React Native/Expo) 為姊妹專案：

| 項目 | Web App | Mobile App |
|------|---------|------------|
| 路徑 | `engine/aep-engine-web` | `engine/aep-engine-app` |
| 框架 | React + Vite | React Native + Expo |
| 平台 | 瀏覽器 | iOS / Android |
| GL Layer | ECO-70-PRESENTATION-WEB | ECO-70-PRESENTATION-APP |

兩者共享相同的：
- 功能設計（五個主要螢幕）
- UI 元件概念
- 資料結構
- GL 治理標準

## 瀏覽器支持

- Chrome/Edge 最新版本
- Firefox 最新版本
- Safari 最新版本
- 移動瀏覽器（iOS Safari、Chrome Mobile）

## GL 治理合規

| 項目 | 狀態 |
|------|------|
| GL Layer | ECO-70-PRESENTATION |
| Semantic Anchor | ECO-70-PRESENTATION-WEB |
| Charter Activated | ✅ |
| Manifest | ✅ `.gl-manifest.yaml` |
| Audit Compliant | ✅ |

## 許可證

MIT

---

**版本**: 1.0.0  
**最後更新**: 2026-01-26  
**GL Unified Architecture Governance Framework Activated**