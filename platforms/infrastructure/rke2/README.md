# RKE2 Security Integration for MachineNativeOps

## Overview

This directory contains RKE2 (Rancher Kubernetes Engine 2) security hardening configurations and automation scripts for the MachineNativeOps project. RKE2 is a "hardened by default" Kubernetes distribution that provides enterprise-grade security and CIS compliance.

## 📁 Directory Structure

```
infrastructure/rke2/
├── profiles/                        # RKE2 configuration profiles
│   ├── cis/                         # CIS benchmark configurations
│   ├── production/                  # Production environment configs
│   │   ├── config.yaml              # Main RKE2 configuration
│   │   ├── encryption-provider-config.yaml  # Secrets encryption
│   │   ├── psa-config.yaml          # Pod Security Admission
│   │   └── audit-policy.yaml        # Audit logging policy
│   └── staging/                     # Staging environment configs
├── scripts/                         # Automation scripts
│   ├── install-rke2.sh             # RKE2 installation script
│   ├── validate-cis.sh             # CIS compliance validation
│   └── rotate-secrets.sh           # Key rotation script
├── manifests/                       # Kubernetes manifests
│   ├── network-policies/           # Network policies
│   ├── pod-security-policies/      # Pod Security Admission configs
│   └── audit-logging/              # Audit configurations
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

- Linux system with SELinux support (RHEL/CentOS/Oracle Linux 7.8+)
- Root or sudo access
- Minimum 2GB RAM, 20GB disk space
- Network connectivity

### Installation

```bash
# 1. Navigate to scripts directory
cd infrastructure/rke2/scripts

# 2. Make script executable
chmod +x install-rke2.sh

# 3. Run installation script
sudo ./install-rke2.sh

# 4. Verify installation
sudo systemctl status rke2-server
kubectl get nodes
```

### CIS Validation

```bash
# Run CIS compliance validation
cd infrastructure/rke2/scripts
sudo ./validate-cis.sh

# Review the report
cat outputs/cis-validation-*.json
```

## 🔧 Configuration

### Main Configuration File

The main RKE2 configuration is in `profiles/production/config.yaml`. Key settings:

```yaml
# CIS Profile
profile: cis-1.29

# SELinux
selinux: true

# Kernel Protection
protect-kernel-defaults: true

# Secrets Encryption
secrets-encryption: true

# Network Policies
network-policies: true
```

### Secrets Encryption

Before enabling secrets encryption, generate an encryption key:

```bash
# Generate a 32-byte random key
HEAD -c 32 /dev/urandom | base64

# Update encryption-provider-config.yaml with the key
# Restart RKE2
sudo systemctl restart rke2-server

# Encrypt existing secrets
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

### Kernel Parameters

RKE2 configures CIS-compliant kernel parameters during installation:

- `net.ipv4.ip_forward = 0` - Disable IP forwarding
- `net.bridge.bridge-nf-call-iptables = 1` - Enable iptables bridge
- `kernel.modules_disabled = 1` - Disable module loading

Review `/etc/sysctl.d/99-rke2-cis.conf` for all parameters.

## 🔒 Security Features

### CIS Compliance

RKE2 is designed to pass CIS Kubernetes benchmarks out-of-the-box. The installation script:

- Enables CIS profile configuration
- Configures SELinux in enforcing mode
- Sets up kernel hardening parameters
- Creates etcd user with restricted permissions
- Configures audit logging

### SELinux

SELinux provides mandatory access control (MAC) at the kernel level:

```bash
# Check SELinux status
getenforce

# View SELinux denials
ausearch -m avc -ts recent
```

### Secrets Encryption

Secrets are encrypted at rest using AES-CBC:

- Configuration: `encryption-provider-config.yaml`
- Encryption: AES-CBC with 256-bit keys
- Key rotation: Every 90 days recommended

### Network Policies

Default network policies enforce zero-trust networking:

- All traffic denied by default
- Explicit allow rules required
- Namespace-level isolation

### Pod Security Admission

Replaces deprecated Pod Security Policies (PSP):

- Restricted mode by default
- No privileged pods allowed
- Host networking disabled
- All capabilities dropped

### Audit Logging

Comprehensive audit logging for compliance:

- Secret operations logged at RequestResponse level
- RBAC operations logged at RequestResponse level
- All other operations at Metadata level
- Retention: 30 days, 10 backups

## 📊 Monitoring

### Prometheus Metrics

RKE2 exposes metrics on `/metrics` endpoint. Key metrics:

```yaml
# CIS Compliance
rke2_cis_compliance_status

# SELinux Status
rke2_selinux_mode

# Encryption Status
rke2_secrets_encryption_enabled

# Policy Violations
rke2_pod_security_violations
rke2_network_policy_violations
```

### Grafana Dashboards

Example dashboard queries:

```promql
# CIS Compliance Score
sum(rke2_cis_compliance_status) / count(rke2_cis_compliance_status) * 100

# SELinux Mode
rke2_selinux_mode

# Secrets Encryption Status
rke2_secrets_encryption_enabled

# Policy Violations (last 24h)
sum(increase(rke2_pod_security_violations[24h]))
```

## 🔄 Maintenance

### Updates and Upgrades

```bash
# Check current version
rke2 --version

# Upgrade to latest version
curl -sfL [EXTERNAL_URL_REMOVED] | sh -
systemctl restart rke2-server

# Verify upgrade
kubectl get nodes
kubectl get pods -A
```

### Backup and Restore

```bash
# Backup etcd
kubectl etcdctl snapshot save /tmp/etcd-backup.db

# Restore etcd
kubectl etcdctl snapshot restore /tmp/etcd-backup.db
```

### Key Rotation

```bash
# Generate new key
NEW_KEY=$(head -c 32 /dev/urandom | base64)

# Update encryption config
# Add new key to encryption-provider-config.yaml

# Apply configuration
systemctl restart rke2-server

# Re-encrypt secrets
kubectl get secrets --all-namespaces -o json | kubectl replace -f -

# Remove old key after verification
```

## 🐛 Troubleshooting

### Common Issues

**Issue: RKE2 fails to start**

```bash
# Check logs
journalctl -u rke2-server -f

# Check configuration
cat /etc/rancher/rke2/config.yaml

# Verify SELinux
getenforce
```

**Issue: CIS validation fails**

```bash
# Run validation
./validate-cis.sh

# Review report
cat outputs/cis-validation-*.json

# Fix specific issues
# For example, fix etcd permissions:
chmod 700 /var/lib/rancher/rke2/server/db/etcd
chown etcd:etcd /var/lib/rancher/rke2/server/db/etcd
```

**Issue: Secrets not encrypted**

```bash
# Verify encryption provider config exists
ls -la /etc/rancher/rke2/encryption-provider-config.yaml

# Check if encryption is enabled
grep secrets-encryption /etc/rancher/rke2/config.yaml

# Restart RKE2
systemctl restart rke2-server
```

## 📚 Documentation

### Integration with GL Governance

This RKE2 integration follows GL (Governance Layers) framework:

- **GL00-09**: Strategic Layer - Security policies and CIS compliance
- **GL10-19**: Risk & Metrics - CIS compliance tracking
- **GL20-29**: Resource & Standards - Configuration standards
- **GL30-39**: Process & Control - Audit processes
- **GL40-49**: Monitoring & Optimization - Security monitoring
- **GL50-59**: Observability Layer - Audit logging
- **GL90-99**: Meta-Specification - Documentation governance

### Related Documentation

- [RKE2 Official Documentation]([EXTERNAL_URL_REMOVED])
- [CIS Kubernetes Benchmark]([EXTERNAL_URL_REMOVED])
- [MachineNativeOps README](../../../README.md)
- [GL Governance System](../../../ECO-STATUS-REPORT.md)

## 🤝 Contributing

When contributing to RKE2 configurations:

1. Ensure all files include GL governance markers
2. Follow GL semantic boundaries
3. Validate YAML syntax before committing
4. Run CIS validation after changes
5. Update documentation as needed

## 📞 Support

For issues and questions:

1. Check troubleshooting section
2. Review RKE2 documentation
3. Check GitHub issues
4. Contact MachineNativeOps team

## 📜 License

MIT License - See [LICENSE](../../../LICENSE)

---

**Version**: 1.0  
**Last Updated**: 2026-01-30  
**GL Layer**: GL90-99  
**Status**: 📋 Ready for Integration