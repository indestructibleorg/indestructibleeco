# ECO URN/URI 組成規則 (Naming Rules)

## 1. URN (Uniform Resource Name)
- **格式**: `urn:eco-base:k8s:<platform-id>:<component>:<resource-name>:sha256-<content-hash>`
- **範例**: `urn:eco-base:k8s:platform-01:deployment:backend-api:sha256-12345678...`
- **組成**:
  - `platform-id`: 資源歸屬的平台 ID（如 `platform-01`, `core`）。
  - `component`: 資源種類（如 `deployment`, `service`, `configmap`）。
  - `resource-name`: 資源名稱。
  - `content-hash`: 資源內容的 SHA256 哈希值。

## 2. URI (Uniform Resource Identifier)
- **格式**: `eco-base://k8s/<platform-id>/<component>/<resource-name>`
- **範例**: `eco-base://k8s/platform-01/deployment/backend-api`
- **組成**:
  - `platform-id`: 資源歸屬的平台 ID。
  - `component`: 資源種類。
  - `resource-name`: 資源名稱。

## 3. 命名限制
- **字元集**: `[a-z0-9-]`（小寫字母、數字、連字號）。
- **禁止**: 大寫字母、下劃線、特殊符號。
- **長度**: 遵循 Kubernetes 資源命名限制。
