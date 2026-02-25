<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Policy-as-Code Framework - MachineNativeOps

This directory contains the OPA/Rego policies that implement Governance-as-Code for the MachineNativeOps platform. All governance rules are codified as machine-readable policies that can be automatically validated and enforced.

## Policy Structure

```
controlplane/governance/policies/
├── POLICY_MANIFEST.yaml    # Central policy registry and metadata
├── naming.rego             # Naming conventions and namespace governance
├── semantic.rego           # Semantic consistency and health monitoring
├── security.rego           # Security policies and supply chain requirements
├── autonomy.rego           # Autonomy level requirements and progression
└── README.md              # This file
```

## Available Policies

### 1. Naming Policy (`naming.rego`)
**Purpose:** Enforces kebab-case naming conventions and namespace governance

**Rules:**
- Files and directories must use kebab-case
- Module IDs must follow `XX-name` format (e.g., "01-core")
- Namespaces must follow `mno-name` format (e.g., "mno-core")
- Reserved namespaces require specific module IDs
- Interface and component names must be kebab-case

**Applies To:**
- Files, directories, modules, interfaces, components

**Severity:** Medium
**Remediation:** Automatic

### 2. Semantic Policy (`semantic.rego`)
**Purpose:** Ensures semantic consistency across modules and components

**Rules:**
- Modules must have a namespace
- Modules must have semantic mappings
- Semantic health score must be ≥ 80
- No duplicate concepts with different mappings
- Components must have semantic mappings
- Semantic mappings must follow `mno-name` format

**Applies To:**
- Modules, semantic mappings, components

**Severity:** High
**Remediation:** Manual

### 3. Security Policy (`security.rego`)
**Purpose:** Enforces security policies, secret management, and vulnerability requirements

**Rules:**
- Artifacts must have SBOM and SLSA Level 3+ provenance
- Artifacts must be signed with Cosign
- No critical vulnerabilities allowed
- All secrets must be encrypted
- Secrets must be rotated within 90 days
- Dependencies must be scanned and approved
- No secrets in configuration files
- Container images must be scanned and trusted

**Applies To:**
- Artifacts, deployments, secrets, dependencies, code, images

**Severity:** Critical
**Remediation:** Manual

### 4. Autonomy Policy (`autonomy.rego`)
**Purpose:** Enforces autonomy level requirements and progression rules

**Rules:**
- Modules must have valid autonomy levels (L1-L5 or Global Layer)
- Module autonomy must match or exceed dependencies
- Autonomy progression limited to 2 levels at a time
- Operations must comply with module autonomy levels
- L5 operations must not require human intervention
- Specific autonomy ranges for each module:
  - 01-core: L1-L2
  - 02-intelligence: L2-L3
  - 03-governance: L3-L4
  - 04-autonomous: L4-L5
  - 05-observability: L4-L5
  - 06-security: Global Layer

**Applies To:**
- Modules, operations, components

**Severity:** Medium
**Remediation:** Manual

## Using the Policies

### Policy Validation with OPA

```bash
# Validate a resource against a policy
opa eval -d policies/ \
  -i input.json \
  'data.mno.governance.policies.naming.allow'

# Get detailed violation messages
opa eval -d policies/ \
  -i input.json \
  'data.mno.governance.policies.naming.deny'
```

### Input Format Example

```json
{
  "resource": {
    "type": "module",
    "module_id": "01-core",
    "namespace": "mno-core",
    "autonomy_level": "L1-L2",
    "semantic_health_score": 100,
    "semantic_mappings": [
      {
        "concept": "Service Discovery",
        "mapping": "mno-core.service-registry"
      }
    ]
  }
}
```

### Integration with CI/CD

Policies are integrated into GitHub Actions workflows:

1. **PR Quality Check:** Validates naming and semantic policies on pull requests
2. **AI Integration Analyzer:** Validates all policies during code analysis
3. **Policy Gate:** Blocks deployments that violate policies

### Policy Enforcement Modes

- **Strict:** Violations block operations (default for production)
- **Advisory:** Violations generate warnings but don't block
- **Disabled:** Policy not enforced

### Policy Severity Levels

- **Critical:** Security/compliance violations that must be blocked
- **High:** Significant violations that should be blocked
- **Medium:** Important violations that should be addressed
- **Low:** Minor violations for informational purposes

## VETO Authority

The Global Layer (module 06-security) has VETO authority over:
- Security policy changes that decrease security level
- Semantic changes that create namespace conflicts
- Global Layer autonomy level changes

VETO decisions require manual exception requests and approval.

## Policy Development

### Creating a New Policy

1. Create a new `.rego` file following naming conventions
2. Define the package: `package mno.governance.policies.<policy_name>`
3. Implement `allow` rule with validation logic
4. Implement `deny` rules with violation messages
5. Update `POLICY_MANIFEST.yaml`
6. Add tests and documentation

### Policy Testing

```bash
# Test a policy with valid input
opa test policies/ -v

# Test with coverage report
opa test policies/ --coverage
```

## Policy Statistics

- **Total Policies:** 4
- **Active Policies:** 4
- **Strict Enforcement:** 4
- **Critical Severity:** 1 (security)
- **High Severity:** 1 (semantic)
- **Medium Severity:** 2 (naming, autonomy)
- **Automatic Remediation:** 1 (naming)
- **Manual Remediation:** 3 (semantic, security, autonomy)

## Next Steps

- [ ] Integrate policies with GitHub Actions workflows
- [ ] Implement policy gate tool (`bin/mno-policy-gate`)
- [ ] Create policy validation test suite
- [ ] Set up policy violation alerting
- [ ] Develop policy documentation portal
- [ ] Implement automatic remediation for naming policy

## Related Documentation

- [Module Organization](/controlplane/baseline/modules/README.md)
- [Governance Architecture](/docs/architecture/governance.md)
- [Research Report Verification](/research_report_verification_plan.md)

## Support

For policy questions or issues:
- Review policy documentation in individual `.rego` files
- Check `POLICY_MANIFEST.yaml` for policy metadata
- Submit an issue or pull request with policy change proposals