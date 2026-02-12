# Cloudflare Pages 自動部署配置指南

本文檔說明如何在 Cloudflare Pages 中配置 autoecoops/ecosystem 倉庫的自動部署。

## 前置要求

- Cloudflare 帳戶（免費或付費）
- GitHub 帳戶與 autoecoops/ecosystem 倉庫的存取權限
- 完成的 ESLint 與 pnpm 依賴修復

## 配置步驟

### 第一步：連接 GitHub 倉庫

1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 在左側導航欄選擇 **Pages**
3. 點擊 **連接到 Git** 按鈕
4. 選擇 GitHub 作為 Git 提供商
5. 授權 Cloudflare 訪問您的 GitHub 帳戶
6. 在倉庫列表中選擇 `autoecoops/ecosystem`

### 第二步：配置構建設置

在「設置構建和部署」頁面中，配置以下參數：

| 設置項目 | 值 |
|---------|-----|
| **框架預設** | Next.js |
| **構建命令** | `npx @cloudflare/next-on-pages@1` |
| **構建輸出目錄** | `vercel/output/static` |
| **根目錄** | `/frontend/project-01` |

### 第三步：配置環境變數

1. 在部署前，進入 **設置** → **環境變數**
2. 根據 `.env.example` 添加以下環境變數：

```
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_OAUTH_CLIENT_ID=your_client_id
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

**注意**：所有前端可見的變數必須使用 `NEXT_PUBLIC_` 前綴。

### 第四步：設置自動部署觸發

1. 在「部署」設定中，確認以下配置：
   - **自動部署分支**：`main`
   - **自動部署**：已啟用

2. 點擊 **保存和部署** 完成配置

## 驗證部署

### 首次部署

1. 配置完成後，Cloudflare Pages 將自動觸發首次部署
2. 在 Pages 儀表板中監控部署進度
3. 部署完成後，您將獲得一個 `*.pages.dev` 域名

### 測試自動部署

1. 在本地修改代碼並推送至 main 分支：
   ```bash
   git add .
   git commit -m "test: verify Cloudflare Pages auto-deployment"
   git push origin main
   ```

2. 返回 Cloudflare Pages 儀表板，觀察新的部署是否自動觸發
3. 部署完成後，訪問 `*.pages.dev` 域名驗證更改是否已生效

## 故障排除

### 構建失敗

如果部署失敗，檢查以下項目：

1. **ESLint 版本衝突** - 確認 pnpm-lock.yaml 已提交至 main 分支
2. **根目錄設置** - 驗證根目錄設置為 `/frontend/project-01`
3. **環境變數缺失** - 檢查所有必需的環境變數是否已配置
4. **Next.js 版本** - 確認 frontend/project-01/package.json 中 next 版本 ≥ 15.0.0

### 部署後頁面空白

1. 檢查瀏覽器控制台是否有 JavaScript 錯誤
2. 驗證環境變數是否正確傳遞至前端
3. 檢查 Cloudflare Pages 的構建日誌以獲取詳細錯誤信息

## 自定義域名配置

完成初始部署後，您可以將自定義域名綁定到 Cloudflare Pages：

1. 在 Pages 項目設置中進入 **自定義域名**
2. 點擊 **設置自定義域名**
3. 輸入您的域名（例如 `app.autoecoops.io`）
4. 按照 Cloudflare 的指示配置 DNS 記錄

## 監控與維護

### 查看部署日誌

1. 進入 Pages 項目
2. 點擊具體的部署記錄
3. 查看「構建日誌」和「部署日誌」以診斷問題

### 回滾部署

如果最新部署出現問題：

1. 進入 Pages 項目的部署歷史
2. 找到上一個成功的部署
3. 點擊 **回滾至此部署**

## 後續步驟

1. **配置 GitHub 分支保護規則** - 要求 Cloudflare Pages 部署成功後才允許合併 PR
2. **設置監控告警** - 配置 Cloudflare 通知以在部署失敗時收到警報
3. **實施 A/B 測試** - 使用 Cloudflare Workers 進行流量分配測試

## 參考資源

- [Cloudflare Pages 文檔](https://developers.cloudflare.com/pages/)
- [Next.js 在 Cloudflare Pages 上的部署](https://developers.cloudflare.com/pages/framework-guides/nextjs/)
- [Cloudflare Pages 環境變數配置](https://developers.cloudflare.com/pages/platform/build-configuration/)
