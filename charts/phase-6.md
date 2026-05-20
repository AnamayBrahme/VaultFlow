## 🔒 Phase 6 Verification: RBAC Least Privilege & Tenant Isolation

To ensure our application containers follow the principle of least privilege, we implemented namespace-scoped Role-Based Access Control (RBAC). This ensures that each team's API can only read configurations inside its own fence and is blocked from modifying infrastructure or touching other tenants.

### 📜 1. Applied RBAC Manifests (Team A Example)

#### Namespace-Scoped Permissions (`role.yaml`)
This configuration grants our Python Flask app explicit read/write access to basic configurations (`configmaps`) and encryption keys (`secrets`), but excludes administrative capabilities like deletion.
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: vaultflow-api-team-a
  namespace: vaultflow-team-a
rules:
  - apiGroups: [""] # Core API group for basic resources
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"] # Restricted visibility for health check synchronization