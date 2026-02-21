# IndestructibleEco - Complete Token Manifest

**Date**: February 21, 2026
**Project**: IndestructibleEco
**Environment**: Production

---

## 🔐 GCP Service Account Token

### Service Account Details

- **Email**: `eco-deployer@my-project-ops-1991.iam.gserviceaccount.com`
- **Name**: IndestructibleEco Deployer
- **Key ID**: `9cd63bf911e39bdccc09ba4109c488ac76eaf523`

### Permissions

- ✅ Owner
- ✅ Editor
- ✅ Viewer
- ✅ Service Account User
- ✅ Service Account Key Admin
- ✅ Service Account Token Creator
- ✅ Service Account Credential Creator
- ✅ Create Service Accounts
- ✅ View Service Accounts
- ✅ Database Admin
- ✅ Site Reliability Engineer
- ✅ Data Scientist
- ✅ Machine Learning Engineer
- ✅ Developer Operations
- ✅ Workload Identity User
- ✅ Security Auditor
- ✅ Service Account API Key Binding Admin

### Usage

- GKE cluster authentication
- GCP resource management
- Deployment automation

---

## 🔑 Supabase Tokens

### Project Details

- **Project Name**: indestructibleeco
- **Project Reference**: `yrfxijooswpvdpdseswy`
- **Project URL**: `https://yrfxijooswpvdpdseswy.supabase.co`
- **Region**: ap-south-1

### API Keys

#### Publishable Key (Client)
```
sb_publishable_rhTyBa4IqqV14n_B87S7g_zKzDSYTd
```

- **Usage**: Client-side applications
- **Permissions**: Anonymous access (with RLS policies)
- **Security**: Safe to use in browser

#### Secret Key (Service Role)

```
sb_secret_YOUR_SERVICE_ROLE_KEY_HERE
```

- **Usage**: Server-side applications
- **Permissions**: Full access, bypasses RLS
- **Security**: Never expose to client

#### Anon Key (Legacy)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyZnhpam9vc3dwdmRwZHNlc3d5Iiwicm9s
```

- **Usage**: Legacy authentication
- **Status**: Migrated to new JWT keys

### JWT Configuration

#### JWT Signing Keys

- **JWT Key ID**: `d8cfd2f1-cb4d-4f15-925f-1cd9faadebfc`
- **Access Token Expiry**: 3600 seconds (1 hour)

#### Legacy JWT Secret
```
YOUR_JWT_SECRET_HERE
```

- **Usage**: JWT token verification
- **Status**: Legacy, consider rotating

### Database Connection

#### Direct Connection String
```
postgresql://postgres:YOUR_PASSWORD@db.yrfxijooswpvdpdseswy.supabase.co:5432/postgres
```

#### Connection Parameters

- **Host**: `db.yrfxijooswpvdpdseswy.supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: YOUR_PASSWORD

### S3 Configuration

#### S3 Protocol Connection

- **Endpoint**: `https://yrfxijooswpvdpdseswy.storage.supabase.co/storage/v1/s3`
- **Region**: `ap-south-1`
- **Bucket**: `autoecoops_keys`
- **Access Key**: `7bc8a0a036fbd497ba54ef47d76b5be4`

### Edge Functions

#### Function Deployment
```bash
supabase functions new hello-world
supabase functions deploy hello-world --project-ref yrfxijooswpvdpdseswy
```

#### Function Invocation
```bash
curl -L -X POST 'https://yrfxijooswpvdpdseswy.supabase.co/functions/v1/hello-world' \
  -H 'Authorization: Bearer sb_publishable_rhTyBa4IqqV14n_B87S7g_zKzDSYTd' \
  --data '{"name":"Functions"}'
```

---

## 🌐 Cloudflare Tokens

### Custom Hostname

- **Hostname**: `_cf-custom-hostname.autoecoops.io`
- **Hostname ID**: `21c5d22a-4512-485b-9557-8aa9fa7c96ed`

### SSL/TLS Certificates

#### Client Certificate (for Cloudflare Client Authentication)
**Certificate**:
```
-----BEGIN CERTIFICATE-----
MIIEFTCCAv2gAwIBAgIUawiwXL2eJk+aCSTwygfEjw2b97UwDQYJKoZIhvcNAQEL
BQAwgagxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRYwFAYDVQQH
Ew1TYW4gRnJhbmNpc2NvMRkwFwYDVQQKExBDbG91ZGZsYXJlLCBJbmMuMRswGQYD
VQQLExJ3d3cuY2xvdWRmbGFyZS5jb20xNDAyBgNVBAMTK01hbmFnZWQgQ0EgMmZl
YWQ0YTE0MWVjMmM2NzdlYjNiZjBhYzUzNWYxZDUwHhcNMjYwMjIxMDkzNzAwWhcN
MzYwMjE5MDkzNzAwWjAiMQswCQYDVQQGEwJVUzETMBEGA1UEAxMKQ2xvdWRmbGFy
ZTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAK9vVyOmoOS1TysXGZmj
gaF0C1BKf4+xDb1lOnrVe1n5rgdCpG+p7yukkxlLdMuGKq6RpUleeWZqd5eIVFR0
D3dxi2IwwkPy3kgy3FPDYRJs1mdO4svOriqXD95OsEeapCd6C79hbWLS15IG9+9p
6ypZpj4I6bvNwvv8nrbUbDMWaaH/qk3Al2vXRNwgfSDsHSIUUQvtOd0fgVBMh237
jVnATMKATVmgyIPZe04h4JvML4cYmaE+GlDPxc+HO8ajv1UUmqhkYlpo2tUyZ36h
iIHniQgN/XqTYalf/D5Xw2KBdcIKxkqQcO/lbCukaey1vwxgamtEMGLcutZ76EgB
fEMCAwEAAaOBuzCBuDATBgNVHSUEDDAKBggrBgEFBQcDAjAMBgNVHRMBAf8EAjAA
MB0GA1UdDgQWBBSQySbySYENcbGgcsykNpcGA2+ObzAfBgNVHSMEGDAWgBSSwhu6
pldoyL0SHohP5VBCQMeblTBTBgNVHR8ETDBKMEigRqBEhkJodHRwOi8vY3JsLmNs
b3VkZmxhcmUuY29tLzVhZTE4OGFkLWQyM2YtNGI0YS04ZDdjLTE5NGY2ZTY2ZDcw
MC5jcmwwDQYJKoZIhvcNAQELBQADggEBAIgCb+tJShIrFNYUx0uusjPN8v57ndxr
E6mwD4PBLlOU4clcfdS5K2PExdWv8DIX97ZodW0r3m7qt1CTWwYjGiRRVXr1UeqD
VkCpOSL0ayaEqgx5ySfXZBS33Bpag+8dtJPyzjTPNGXG3IrI6VSonk5bwVJkFIbY
PYBwU/XrN9kAG1OLv4lNTs3PONLwqQonq7wGSQZzuCp7fseatOcEZfsA3h615GGt
HL9TMhuLaKQhy3PUNFP+40FSihOhpT4PFpB67h9ppIcV4t/UBdS2ZepyMhkV6osL
pP7T5aMt5Q6O16ZHYUD5B/Zn8M29YHtuANbTnL0mANgSP6ylIHpBdgs=
-----END CERTIFICATE-----
```

**Private Key**:
```
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCvb1cjpqDktU8r
FxmZo4GhdAtQSn+PsQ29ZTp61XtZ+a4HQqRvqe8rpJMZS3TLhiqukaVJXnlmaneX
iFRUdA93cYtiMMJD8t5IMtxTw2ESbNZnTuLLzq4qlw/eTrBHmqQnegu/YW1i0teS
BvfvaesqWaY+COm7zcL7/J621GwzFmmh/6pNwJdr10TcIH0g7B0iFFEL7TndH4FQ
TIdt+41ZwEzCgE1ZoMiD2XtOIeCbzC+HGJmhPhpQz8XPhzvGo79VFJqoZGJaaNrV
Mmd+oYiB54kIDf16k2GpX/w+V8NigXXCCsZKkHDv5WwrpGnstb8MYGprRDBi3LrW
e+hIAXxDAgMBAAECggEAKYBF1W20LxaDGXb3++P1pQuOJ5rQDV59mRnK2UcKTLEn
jZkizDWfmivvDnNOuFzPWQekWbRrNKKoEuVRyb7A7+kg54QQWMGp+ttpSrl0C8dK
exrqxPrqMbIVs2nbAr1e6uXQxJ/YICIvk+BpI65jTtvxW0iBfoeBAlpy815SEE1u
cKG/lOZkWxvGI0MH5XiSlp42wsZrYlffK8/khGZyvdKFmYxO7ikdn0rzatoeCLTn
vVgFbiTDnNa/A3k+CnFbmDzeOf19XpUp8b0gVrIPSbpL0Dm8s+2UDEY1iKKQt4Gs
3LKDa0NDABVw4efeDK6JkBb7feNRbZjPwAeD8FXKdQKBgQDwqE2ldZhiEClnuJq7
foujqB877o1Lp5HXzm4uzObAk3IbTMJFF099U0IAt/1ZxbCVhIKsfFxb9xbLpZ/J
hEgSKdr/7oW+b7wksrJuAKvZNbXyvQezIipW0TaSnuDMXITkDJaqcd1ne5clkDJA
1XDAV94UAD+21+JDYrdqw6ZDZwKBgQC6no9yWibASQJ+exfdHoBGw3+j2R4keQ1F
DRNFcfruTo2cQLKfX2+4rUJWYuVYCOz87Gv0nxhapZuN9moIztbK0tOVR4BQxouD
SVPgfsU+82WZuBJWXzVzI56DcU+X87nFOsbXnNjhBrjhY4OqFb+6QlVZIu+MYG4j
dM2uEv6yxQKBgQDv/idQtfD8+jkQYpyMFiqTTnm3frIRnE5o9EgVC+miamgEqYui
8xgmVv0fUlypRehPcxINiQdh/wsQk17By9VDp9HqIKfnve3Wew5NfQXjWxjTtYcU
MSIf6guONDriEfHEqnkmCN9O74VPxHkZBsGmTvn84DKp2KiforZfFjWcSQKBgEK/
E29C7zk24715KT/c+ORWaACiVzWUVjqsQohEDAvP7LZGLZzy9XKIBYIAPScPijOs
G7CSdpN1R/2udJ5R3GEOpr5tpGc/nAaI44cX0FSDmYMxYt2hj+xugPNiQ6WFdpwk
OZpEbw2M6fMzNJRQ0xI7R2tqI2OB2eK0lBv+jzpBAoGBAJUwppcqLIn9LULC1GIh
G2iJTh8ivctk83A780zjhuG9QD/XgonMEJ9j7x4QIGmdJT4SUJsTTGd8d1+LZue2
SVasVbmGA/ERN/ifo+Baq7LDpL5EQ8k5EC4/JQlldlCTwxU7EGP4zQSY+qgJVJUx
qs63/DMWa1DOA4zlwLHVqAHU
-----END PRIVATE KEY-----
```

#### Origin Certificate (for Kubernetes Ingress)
**Certificate**:
```
-----BEGIN CERTIFICATE-----
MIIEpjCCA46gAwIBAgIUR8w1qbqgFOn+YuUOLCrGrJx75FswDQYJKoZIhvcNAQEL
BQAwgYsxCzAJBgNVBAYTAlVTMRkwFwYDVQQKExBDbG91ZEZsYXJlLCBJbmMuMTQw
MgYDVQQLEytDbG91ZEZsYXJlIE9yaWdpbiBTU0wgQ2VydGlmaWNhdGUgQXV0aG9y
aXR5MRYwFAYDVQQHEw1TYW4gRnJhbmNpc2NvMRMwEQYDVQQIEwpDYWxpZm9ybmlh
MB4XDTI2MDIyMTA5MzkwMFoXDTQxMDIxNzA5MzkwMFowYjEZMBcGA1UEChMQQ2xv
dWRGbGFyZSwgSW5jLjEdMBsGA1UECxMUQ2xvdWRGbGFyZSBPcmlnaW4gQ0ExJjAk
BgNVBAMTHUNsb3VkRmxhcmUgT3JpZ2luIENlcnRpZmljYXRlMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEApaZeV2w0eiIrP4F4XyVdnSi3DrZWoVeZKm0l
X2KAU6JwK/oAaeZjD2wpUwOwXMq/D3xLAHqCFNDXvWbt2I4grx6fw7vj1gZ6YNDH
UYULNiN4R2/uKVddiZJOXzO+e2V4bncCbCFLQH0Wh3ChFOkhgh6BvV1gM4Don5y1
cjxkiuDjVZXWiaP3ZV4pS3ySF7k8EvpQWD+7VGK3fvZNQ+1aO8tw1jR0nu7CspO+
3Y25FbpMdziTkGJBxuFIoh7p5ucjUHA97MtHz8d8ipSx7+E7UxiZRKtBLO4IlQLt
Jq9kDqYR3R9KHgvOQWw1aY9Fi0/A3O4fs1C1Zbni6ZN+AXaiRQIDAQABo4IBKDCC
ASQwDgYDVR0PAQH/BAQDAgWgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggrBgEFBQcD
ATAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBTZUJHCuDFsV3H3IgULqpZCFyEUHjAf
BgNVHSMEGDAWgBQk6FNXXXw0QIep65TbuuEWePwppDBABggrBgEFBQcBAQQ0MDIw
MAYIKwYBBQUHMAGGJGh0dHA6Ly9vY3NwLmNsb3VkZmxhcmUuY29tL29yaWdpbl9j
YTApBgNVHREEIjAggg8qLmF1dG9lY29vcHMuaW+CDWF1dG9lY29vcHMuaW8wOAYD
VR0fBDEwLzAtoCugKYYnaHR0cDovL2NybC5jbG91ZGZsYXJlLmNvbS9vcmlnaW5f
Y2EuY3JsMA0GCSqGSIb3DQEBCwUAA4IBAQB6PHkOwCWha9QG4UCl1zD3/G6NvRPt
zgdD4Ul47vsn6apP0fih4wPzc0KfR1705EzKAOHVDcsHtmfPHHMN78E0HW9IUvmG
WKPb4klPYmEzl9HRChe5l9LxMYx2e7bfEJiGaWmd54QKacwIBTn3UmADHhc1MHUh
p/fPqwLQ7OEbqc6MyJo66f5pckqcCy/DIJsM5Q819mgOBMnHN1Qys5kjYLLhlE7S
GSJ15IBEgIl5ONrslD/BtODHDY/+fOeh4g+soU2zlBJQyMuGmLi0m3krwVEbT1yH
iT+ciFJD4+BEM+sSXnkMoboLFNs8iOso3WYX2OT3EA+AqpbZZfvBvH66
-----END CERTIFICATE-----
```

**Private Key**:
```
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQClpl5XbDR6Iis/
gXhfJV2dKLcOtlahV5kqbSVfYoBTonAr+gBp5mMPbClTA7Bcyr8PfEsAeoIU0Ne9
Zu3YjiCvHp/Du+PWBnpg0MdRhQs2I3hHb+4pV12Jkk5fM757ZXhudwJsIUtAfRaH
cKEU6SGCHoG9XWAzgOifnLVyPGSK4ONVldaJo/dlXilLfJIXuTwS+lBYP7tUYrd+
9k1D7Vo7y3DWNHSe7sKyk77djbkVukx3OJOQYkHG4UiiHunm5yNQcD3sy0fPx3yK
lLHv4TtTGJlEq0Es7giVAu0mr2QOphHdH0oeC85BbDVpj0WLT8Dc7h+zULVlueLp
k34BdqJFAgMBAAECggEACuk//+3X27miHqSWZgdYjhBkqm/r7zm4FDmB7jFXTEBV
Yi2CrHcT9wFEDDygd87qXIiZNMwHrdD/J5x+4IulbyjgaNdYpRGNKxEQJ/hQVOhr
ik0UTh3RQqK5TdUN4CPpawv6GV7suC/lICu/jdiOBVD2xnSURcrhHRkIl0s6Fi7/
NW2G7gvBpem3970gp5KoyR262XKcnDgDFGbpgHtynNicPMIjMNjEZu2/Oox7ezY8
XUF6Jqv5MaKosJoGqrGF/T1Yne06JUWWO148fwEjgEF5MvuvjVyzuF1dGLfSbTjN
eUscwsnL4TozenKT11bc5JSg3LAvljkUJc4Oswz32wKBgQDVFXM2CHkZHggyFeZr
I5spbifadZPILNdvSzDgoOdR1tNhUJGE6ldV9pZlGbIg2fnT/N/CgvbsjLJYid+f
VGfUdps1X3zL/AP6QIyU5vU908Xz6HpYv9OLZWel+h8zeskzEybbEe8zsRuUVLWm
b5Qd8ozses2CqFGn4TBZspWYGwKBgQDHAzy1drgYmkxgJeUy+usuAW6qefcStCTC
czSxHjLFZQFToQ04QN1eEKe84cX8pqvyhf/bsDzHQo3DbycHy1PjOHqsp/ZnrJmp
J6hjGLzftsCsyRFbVQ+XmfN+Pd/k2GxDNmFvmMjHfnhM6YQotyIvyuOAX+WEBQj3
6zpST40VHwKBgG8a7CP0bxBFtIhJGwgqXLFRmr4yKIhruTlyv12hCHyHw1gupnHj
rv5HwUueBl9SyQ1cAWBu4UmeYy//U/bEEA+ceHlv/KZwFbLbDXJmquE+Fy2Cvqif
/THmAhFtRe+VymszRUNdKpiNdI/3S3ApJdYnrotvzNCf61PZ+1gJ4i6ZAoGABmUq
PEKWY+QBdE2DcgHyMMZHAh9tOyKi08TT+qUXyJQYWNGiFR6wfmdWnJE8xYOtntuD
f1HIgja3S4J05KE6DuEvwACdwHMhdPgbRyPyXdYHlwXXEvJGz/5YfsQKP9ZclERZ
GTb1rMN5pi8S2iQYayS/7s4mF/n5cc4TT7XSuM0CgYBXH195B2AUhKZwZMQ7dQ5w
/nIVEXQA2UNBrmEn1AjGkCjtSjRf7ENtDd+8LcDmpR7WQEQiGcJeYEkB5/sO37RI
4ePnuZeabHPXbHvBZ8VDI+ZMulc+bXHlhuAFTsGTzrFiABh3srNtDVqwXBtH1Hx5
QKjDo7c6YikYQaLW8EDc/Q==
-----END PRIVATE KEY-----
```

---

## 📋 Environment Variables Summary

### GCP Environment Variables
```bash
export GCP_PROJECT="my-project-ops-1991"
export GCP_REGION="asia-east1"
export GCP_ZONE="asia-east1-a"
export GKE_CLUSTER="eco-staging"
export GCP_SA_EMAIL="eco-deployer@my-project-ops-1991.iam.gserviceaccount.com"
export GCP_SA_KEY="9cd63bf911e39bdccc09ba4109c488ac76eaf523"
```

### Supabase Environment Variables
```bash
export SUPABASE_URL="https://yrfxijooswpvdpdseswy.supabase.co"
export SUPABASE_ANON_KEY="sb_publishable_rhTyBa4IqqV14n_B87S7g_zKzDSYTd"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_YOUR_SERVICE_ROLE_KEY"
export SUPABASE_DB_URL="postgresql://postgres:YOUR_PASSWORD@db.yrfxijooswpvdpdseswy.supabase.co:5432/postgres"
export SUPABASE_JWT_SECRET="YOUR_JWT_SECRET"
export SUPABASE_PROJECT_REF="yrfxijooswpvdpdseswy"
```

### Cloudflare Environment Variables

```bash
export CLOUDFLARE_CUSTOM_HOSTNAME="_cf-custom-hostname.autoecoops.io"
export CLOUDFLARE_HOSTNAME_ID="21c5d22a-4512-485b-9557-8aa9fa7c96ed"
```

### Monitoring Environment Variables
```bash
export PROMETHEUS_URL="https://prometheus._cf-custom-hostname.autoecoops.io"
export GRAFANA_URL="https://grafana._cf-custom-hostname.autoecoops.io"
export GRAFANA_ADMIN_USER="admin"
export GRAFANA_ADMIN_PASSWORD="YOUR_SECURE_PASSWORD"
```

---

## 🔒 Security Notes

### Critical Security Practices

1. **Never commit secrets to version control**
2. **Rotate keys regularly** (every 90 days recommended)
3. **Use environment variables** for all sensitive data
4. **Implement RBAC** for all services
5. **Enable audit logging** for all GCP resources
6. **Use TLS** for all communications
7. **Monitor access logs** for suspicious activity

### Key Rotation Schedule

- **GCP Service Account Keys**: Every 90 days
- **Supabase Service Role Keys**: Every 90 days
- **Cloudflare Certificates**: Every 15 years (Origin Certs)
- **JWT Secrets**: Every 6 months

### Access Control

- **GCP Service Account**: Owner permissions (use with caution)
- **Supabase Service Role**: Full database access (server-side only)
- **Supabase Anon Key**: Client-side access (with RLS)
- **Cloudflare Certificates**: SSL/TLS termination

---

## 📞 Emergency Contacts

### GCP Support

- **Project**: my-project-ops-1991
- **Service Account**: eco-deployer@my-project-ops-1991.iam.gserviceaccount.com

### Supabase Support

- **Project**: indestructibleeco
- **Reference**: yrfxijooswpvdpdseswy
- **Dashboard**: https://supabase.com/dashboard/project/yrfxijooswpvdpdseswy

### Cloudflare Support

- **Account**: indestructibleorg
- **Custom Hostname**: _cf-custom-hostname.autoecoops.io

---

**End of Token Manifest**

⚠️ **WARNING**: This document contains sensitive credentials. Store securely and never commit to version control.
