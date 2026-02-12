# Cloudflare Pages 自定義域名配置指南

本文檔說明如何在 Cloudflare Pages 中為 autoecoops/ecosystem 項目配置自定義域名。

## 前置要求

- Cloudflare Pages 項目已部署並可通過 `*.pages.dev` 域名訪問
- 已擁有或計劃購買的自定義域名（例如：app.autoecoops.io）
- Cloudflare 帳戶具有域名管理權限

## 域名選擇建議

根據 AutoEcoOps 生態系統的架構，建議使用以下域名方案：

| 用途 | 建議域名 | 說明 |
|------|---------|------|
| 主應用 | `app.autoecoops.io` | 前端應用主入口 |
| API 端點 | `api.autoecoops.io` | 後端 API 服務 |
| 文檔 | `docs.autoecoops.io` | 開發者文檔 |
| 儀表板 | `dashboard.autoecoops.io` | 管理員儀表板 |

本指南以 `app.autoecoops.io` 為例進行配置。

## 配置步驟

### 第一步：在 Cloudflare Pages 中添加自定義域名

1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 進入 **Pages** 部分，選擇 autoecoops 項目
3. 在項目設置中，進入 **自定義域名** 或 **域名**
4. 點擊 **設置自定義域名** 或 **添加域名** 按鈕
5. 在輸入框中輸入您的自定義域名（例如：`app.autoecoops.io`）
6. 點擊 **繼續** 或 **添加**

### 第二步：配置 DNS 記錄

Cloudflare 將提供兩種配置方式。根據您的域名管理方式選擇：

#### 選項 A：域名已在 Cloudflare 上管理

如果您的域名已使用 Cloudflare 作為 DNS 提供商：

1. Cloudflare Pages 將自動為您創建 CNAME 記錄
2. 記錄類型：**CNAME**
3. 名稱：`app` （或您選擇的子域名）
4. 內容：`autoecoops.pages.dev`
5. TTL：自動（或 3600 秒）
6. 代理狀態：已代理（橙色雲）

**自動配置**：如果您已將域名轉移至 Cloudflare，系統會自動添加此記錄。

#### 選項 B：域名在其他 DNS 提供商上

如果您的域名在其他 DNS 提供商（如 GoDaddy、Route 53、阿里雲等）上管理：

1. 在您的 DNS 提供商控制面板中添加 CNAME 記錄：
   - **記錄類型**：CNAME
   - **名稱**：`app` （或您選擇的子域名）
   - **值**：`autoecoops.pages.dev`
   - **TTL**：3600（或提供商默認值）

2. 保存記錄並等待 DNS 傳播（通常 5-30 分鐘）

3. 返回 Cloudflare Pages，點擊 **驗證** 以確認 DNS 配置

### 第三步：HTTPS 證書配置

Cloudflare Pages 自動為所有自定義域名配置 HTTPS 證書：

1. 在域名添加後，Cloudflare 將自動申請 SSL/TLS 證書
2. 證書通常在 5-10 分鐘內頒發
3. 您可以在 **SSL/TLS** 設置中查看證書狀態
4. 無需手動配置，Cloudflare 自動管理證書更新

### 第四步：驗證自定義域名

完成 DNS 配置後，驗證域名是否正常工作：

```bash
# 檢查 DNS 解析
nslookup app.autoecoops.io

# 或使用 dig 命令
dig app.autoecoops.io

# 測試 HTTPS 連接
curl -I https://app.autoecoops.io
```

預期結果：
- DNS 應解析至 Cloudflare Pages IP 地址
- HTTPS 連接應返回 200 OK 狀態碼
- SSL 證書應有效且由 Cloudflare 簽發

### 第五步：測試應用訪問

1. 在瀏覽器中訪問 `https://app.autoecoops.io`
2. 應看到與 `*.pages.dev` 相同的應用內容
3. 檢查瀏覽器控制台是否有任何錯誤
4. 驗證所有資源（CSS、JavaScript、圖片）正確加載

## 高級配置

### 配置 WWW 子域名重定向

為了提供更好的用戶體驗，建議配置 `www.app.autoecoops.io` 重定向至 `app.autoecoops.io`：

1. 在 Cloudflare Pages 中添加另一個自定義域名 `www.app.autoecoops.io`
2. 在 Cloudflare Workers 中創建重定向規則：

```javascript
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.hostname === 'www.app.autoecoops.io') {
      return Response.redirect('https://app.autoecoops.io' + url.pathname + url.search, 301);
    }
    return fetch(request);
  }
}
```

### 配置多個自定義域名

如果需要多個域名指向同一應用（例如：`app.autoecoops.io` 和 `ecosystem.autoecoops.io`）：

1. 在 Cloudflare Pages 中重複上述步驟，添加每個域名
2. 所有域名將指向同一應用
3. 在應用代碼中可通過 `window.location.hostname` 區分不同域名訪問

### 配置根域名

如果要使用根域名（例如：`autoecoops.io` 而非 `app.autoecoops.io`）：

1. 在 Cloudflare Pages 中添加根域名 `autoecoops.io`
2. 根據 Cloudflare 的指示配置 A 記錄或 CNAME 記錄
3. 注意：根域名通常需要 A 記錄而非 CNAME

**A 記錄配置**：
- **名稱**：@ （表示根域名）
- **類型**：A
- **值**：Cloudflare 提供的 IP 地址
- **TTL**：自動
- **代理狀態**：已代理（橙色雲）

## 故障排除

### DNS 未解析

**症狀**：訪問自定義域名時顯示 DNS 解析失敗

**解決方案**：
1. 驗證 DNS 記錄是否正確添加至 DNS 提供商
2. 使用 `nslookup` 或 `dig` 檢查 DNS 傳播狀態
3. 等待 DNS 傳播完成（最多 48 小時，通常 5-30 分鐘）
4. 清除本地 DNS 緩存：`ipconfig /flushdns` (Windows) 或 `sudo dscacheutil -flushcache` (macOS)

### HTTPS 證書錯誤

**症狀**：訪問自定義域名時顯示 SSL 證書錯誤

**解決方案**：
1. 確認 DNS 記錄已完全傳播
2. 在 Cloudflare Dashboard 中檢查 SSL/TLS 證書狀態
3. 如果證書仍未頒發，嘗試重新添加域名
4. 檢查域名是否通過 DNS 驗證

### 應用內容不顯示

**症狀**：域名解析正常，但頁面空白或顯示錯誤

**解決方案**：
1. 檢查瀏覽器控制台是否有 JavaScript 錯誤
2. 驗證應用環境變數是否正確配置
3. 檢查 Cloudflare Pages 部署日誌
4. 比較 `*.pages.dev` 和自定義域名的訪問結果

### 重定向循環

**症狀**：訪問域名時陷入無限重定向

**解決方案**：
1. 檢查應用代碼中是否有強制重定向邏輯
2. 驗證 Cloudflare Page Rules 中是否有衝突規則
3. 清除瀏覽器緩存並重試
4. 檢查 Cloudflare Workers 腳本是否有問題

## 安全建議

### 啟用 HSTS

在 Cloudflare 中啟用 HTTP Strict Transport Security (HSTS) 以強制 HTTPS：

1. 進入 **SSL/TLS** → **邊緣證書**
2. 啟用 **HSTS** 選項
3. 設置最大年齡為 12 個月（31536000 秒）
4. 啟用 **包含子域名** 和 **預加載** 選項

### 配置 DDoS 保護

Cloudflare 自動提供 DDoS 保護，但可進一步加強：

1. 進入 **安全** → **DDoS**
2. 設置敏感度級別（建議：高）
3. 配置速率限制規則防止濫用

### 配置 WAF 規則

啟用 Web 應用防火牆 (WAF) 保護應用：

1. 進入 **安全** → **WAF**
2. 啟用 Cloudflare 管理的規則
3. 配置自定義規則以阻止特定攻擊模式

## 監控與維護

### 監控域名健康狀態

1. 在 Cloudflare Dashboard 中定期檢查域名狀態
2. 設置 Cloudflare 通知以接收域名問題警報
3. 監控 SSL 證書過期日期（Cloudflare 自動續期）

### 查看訪問日誌

1. 進入 **分析** 部分查看流量統計
2. 監控頁面加載時間和性能指標
3. 分析訪問來源和地理分佈

### 定期備份

雖然 Cloudflare Pages 自動備份，但建議：

1. 定期備份應用源代碼至 GitHub
2. 記錄所有自定義域名和 DNS 配置
3. 保存 SSL 證書信息以備查詢

## 後續步驟

1. **配置子域名** - 為 API、文檔等添加額外子域名
2. **實施 CDN 優化** - 配置 Cloudflare 緩存規則以提升性能
3. **設置分析** - 使用 Cloudflare Analytics 監控流量和性能
4. **配置自定義錯誤頁面** - 為 404、500 等錯誤創建自定義頁面

## 參考資源

- [Cloudflare Pages 文檔](https://developers.cloudflare.com/pages/)
- [Cloudflare 自定義域名設置](https://developers.cloudflare.com/pages/platform/custom-domain/)
- [DNS 配置最佳實踐](https://developers.cloudflare.com/dns/)
- [SSL/TLS 證書管理](https://developers.cloudflare.com/ssl/)
- [Cloudflare Workers 文檔](https://developers.cloudflare.com/workers/)
