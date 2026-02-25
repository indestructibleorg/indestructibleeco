# Supply Chain Evidence (ECO)

本目錄是 eco-base 專案的供應鏈證據專區（可稽核、可重播、不可漂移）。

## 內容

- `hashlock.json`：資源鎖定真值來源（SoT）
- `hashlock.attestation.intoto.json`：in-toto 格式 attestation（強綁定 hashlock sha256）
- `hashlock.sig` / `hashlock.pem`：cosign keyless blob 簽章與憑證（verify-blob gate）
- `reports/`：CI 產生的報表輸出（JSON + Markdown）
- `policy/`：治理規則文件（canonicalization、URN/URI 規則、信任模型）

## 強制規範

1. manifests 內的 `eco-base/urn` / `eco-base/uri` **禁止人工編輯**
2. `hashlock.json` 與 manifests **不可漂移**（main verify 必須為 0）
3. `hashlock.attestation.intoto.json` 必須與 `hashlock.json` 的 sha256 一致
4. `hashlock.sig` 必須能被 verify-blob 且 identity 綁定到 main 分支的 attest workflow

## 一鍵重播（本地）

### 1. 驗證 Cosign 簽章 (Keyless)
````bash
cosign verify-blob \
  --certificate supplychain/hashlock.pem \
  --signature supplychain/hashlock.sig \
  --certificate-identity "https://github.com/indestructibleorg/eco-base/.github/workflows/eco-supplychain-attest.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  supplychain/hashlock.json
````

### 2. 驗證 Attestation 綁定
````bash
python tools/eco-supplychain/verify_attestation.py \
  --hashlock supplychain/hashlock.json \
  --attestation supplychain/hashlock.attestation.intoto.json
````

### 3. 驗證資源漂移 (Drift Detection)
````bash
python tools/eco-supplychain/hashlock.py \
  --mode verify \
  --paths platforms k8s manifests \
  --hashlock supplychain/hashlock.json
````
