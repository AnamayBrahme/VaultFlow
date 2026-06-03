# VaultFlow 🔐

<p align="center">
  <img src="https://img.shields.io/badge/Kubernetes-v1.30+-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="Kubernetes">
  <img src="https://img.shields.io/badge/Helm-v3-0F1626?style=for-the-badge&logo=helm&logoColor=white" alt="Helm">
  <img src="https://img.shields.io/badge/Skaffold-v2-243447?style=for-the-badge&logo=skaffold&logoColor=white" alt="Skaffold">
  <img src="https://img.shields.io/badge/Security-PSA%20%26%20NetPol-success?style=for-the-badge" alt="Security Verified">
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="CI/CD">
</p>

***

## 📌 Problem Statement

Engineering teams at fast-growing companies face a recurring problem: application configurations and secrets are scattered across `.env` files, CI/CD pipeline variables, shared spreadsheets, and ad-hoc Kubernetes Secrets with no access control, no isolation between teams, and no audit trail.

When a developer on Team A can accidentally read Team B's database credentials, or when a container runs as root with full host privileges because nobody enforced a security policy, the organisation has a serious security and operational risk — even if the product itself is working fine.

**VaultFlow** solves this by engineering a secure, highly available, multi-tenant container platform. It establishes hard boundaries using namespace-isolated runtimes, explicit network routing restrictions, rigorous Pod Security Standards, and robust rollout/rollback workflows — all templated, versioned, and deployed through Helm.

***

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([External User / Client]) -->|HTTPS / TLS| Ingress[NGINX Ingress Controller]

    subgraph SystemNS [Namespace: vaultflow-system]
        Ingress
        DB[(vaultflow-db: PostgreSQL StatefulSet)]
        Prom[Prometheus]
        Grafana[Grafana]
    end

    subgraph AdminNS [Namespace: vaultflow-admin]
        AdminPanel[vaultflow-admin]
    end

    subgraph TeamA [Namespace: vaultflow-team-a  —  PSA restricted]
        direction TB
        UIA[vaultflow-ui]
        APIA[vaultflow-api]
        PDBA[PDB: minAvailable from values] -. protects .-> APIA
    end

    subgraph TeamB [Namespace: vaultflow-team-b  —  PSA restricted]
        direction TB
        UIB[vaultflow-ui]
        APIB[vaultflow-api]
        PDBB[PDB: minAvailable from values] -. protects .-> APIB
    end

    Ingress -->|/ui  →  team-a| UIA
    Ingress -->|/api →  team-a| APIA
    Ingress -->|/ui  →  team-b| UIB
    Ingress -->|/api →  team-b| APIB
    Ingress -->|/admin| AdminPanel

    APIA -->|Read / Write secrets| DB
    APIB -->|Read / Write secrets| DB
    AdminPanel -->|Cluster-wide oversight| DB

    Prom -->|Scrapes /metrics| APIA
    Prom -->|Scrapes /metrics| APIB
    Grafana -->|Queries| Prom
```

***

## 📁 Repository Structure

```
vaultflow/
├── Chart.yaml                          # Umbrella chart
├── values.yaml                         # Global defaults
├── values/
│   ├── dev.yaml                        # PSA warn, 1 replica, low limits
│   ├── staging.yaml                    # PSA enforce, 2 replicas, PDB enabled
│   ├── prod.yaml                       # PSA restricted, 3 replicas, TLS enforced
│   ├── team-a.yaml                     # Team A namespace overrides
│   └── team-b.yaml                     # Team B namespace overrides
├── charts/
│   ├── vaultflow-api/                  # Python Flask API chart
│   │   └── templates/
│   │       ├── deployment.yaml         # securityContext, affinity, probes
│   │       ├── service.yaml
│   │       ├── serviceaccount.yaml
│   │       ├── role.yaml
│   │       ├── rolebinding.yaml
│   │       ├── networkpolicy.yaml
│   │       ├── pdb.yaml
│   │       ├── resourcequota.yaml
│   │       └── pvc.yaml
│   ├── vaultflow-ui/                   # Dashboard frontend chart
│   ├── vaultflow-db/                   # PostgreSQL StatefulSet chart
│   └── vaultflow-observability/        # Prometheus + Grafana chart
├── .github/
│   └── workflows/
│       └── helm-ci.yml                 # helm lint + helm template on every push
└── README.md
```

***

## 🚀 Deployment

### Local Development (Skaffold)

```bash
skaffold dev
```

Starts the hot-reloading development cycle with live image builds and manifest sync.

### Production Cluster Installation (Helm)

```bash
# 1. Create namespaces
kubectl create namespace vaultflow-system
kubectl create namespace vaultflow-admin
kubectl create namespace vaultflow-team-a
kubectl create namespace vaultflow-team-b

# 2. Apply PSA restricted labels to team namespaces
kubectl label namespace vaultflow-team-a pod-security.kubernetes.io/enforce=restricted
kubectl label namespace vaultflow-team-b pod-security.kubernetes.io/enforce=restricted

# 3. Deploy core platform (DB + Observability)
helm install vaultflow-db    ./charts/vaultflow-db            -n vaultflow-system
helm install vaultflow-obs   ./charts/vaultflow-observability -n vaultflow-system

# 4. Deploy Team A
helm install vaultflow-api-a ./charts/vaultflow-api -n vaultflow-team-a -f values/team-a.yaml
helm install vaultflow-ui-a  ./charts/vaultflow-ui  -n vaultflow-team-a -f values/team-a.yaml

# 5. Deploy Team B
helm install vaultflow-api-b ./charts/vaultflow-api -n vaultflow-team-b -f values/team-b.yaml
helm install vaultflow-ui-b  ./charts/vaultflow-ui  -n vaultflow-team-b -f values/team-b.yaml

# 6. Deploy Admin panel
helm install vaultflow-admin ./charts/vaultflow-admin -n vaultflow-admin
```

### Environment Promotion

```bash
# Staging
helm upgrade vaultflow-api-a ./charts/vaultflow-api \
  -n vaultflow-team-a -f values/staging.yaml -f values/team-a.yaml

# Production
helm upgrade vaultflow-api-a ./charts/vaultflow-api \
  -n vaultflow-team-a -f values/prod.yaml -f values/team-a.yaml
```

***

## 🛡️ Security Verification Proofs

### 1. RBAC — `kubectl auth can-i` Matrix

Team-scoped identities are blocked from accessing resources outside their own namespace:

```bash
# Team A developer CAN manage their own namespace
$ kubectl auth can-i create deployments --namespace vaultflow-team-a
yes

# Team A developer CANNOT read Team B resources
$ kubectl auth can-i get pods --namespace vaultflow-team-b
no - User cannot list resource "pods" in API group "" in the namespace "vaultflow-team-b"

# Team A developer CANNOT access admin namespace
$ kubectl auth can-i get pods --namespace vaultflow-admin
no - User cannot list resource "pods" in API group "" in the namespace "vaultflow-admin"
```

### 2. NetworkPolicy — Cross-Namespace Traffic Blocked

A pod launched outside the allowed label set cannot reach the API:

```bash
$ kubectl run netpol-test \
    --image=radial/busyboxplus:curl -i --tty --rm \
    -n default

[ root@netpol-test:/ ]$ curl --connect-timeout 5 \
    http://vaultflow-api-team-a.vaultflow-team-a.svc.cluster.local:8080/api

curl: (28) Connection timed out after 5001 milliseconds
# ❌ BLOCKED — cross-namespace traffic dropped by NetworkPolicy
```

An authorised pod with the correct label selector succeeds:

```bash
[ root@authorised-client:/ ]$ curl \
    http://vaultflow-api-team-a.vaultflow-team-a.svc.cluster.local:8080/health
{"status": "ok"}
# ✅ ALLOWED
```

### 3. PSA Enforcement — Privileged Container Rejected

All team namespaces enforce the `restricted` Pod Security Standard. Any workload attempting to bypass security controls is rejected at admission:

```bash
$ kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: privileged-exploit-pod
  namespace: vaultflow-team-a
spec:
  containers:
  - name: exploit
    image: nginx:latest
    securityContext:
      privileged: true
EOF

Error from server (Forbidden): pods "privileged-exploit-pod" is forbidden:
violates PodSecurity "restricted:latest": privileged containers are not allowed
# ❌ REJECTED by PSA admission controller
```

**Compliant `securityContext` applied to all production containers:**

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

### 4. ResourceQuota — Namespace Limit Enforcement

Each team namespace has hard CPU, memory, and pod limits. Exceeding the quota is rejected by the API server:

```bash
$ kubectl describe resourcequota -n vaultflow-team-a
Name:       vaultflow-team-a-quota
Namespace:  vaultflow-team-a
Resource    Used   Hard
--------    ----   ----
cpu         1800m  2
memory      3Gi    4Gi
pods        4      5
```

***

## 🔄 Resilience — Rolling Updates & Rollback

### Rolling Update (zero-downtime)

```bash
# Trigger a rolling update via Helm upgrade
helm upgrade vaultflow-api-a ./charts/vaultflow-api \
  -n vaultflow-team-a -f values/team-a.yaml \
  --set image.tag=v2.0.0

# Watch the rollout — new pod reaches Ready before old pod terminates
kubectl get pods -n vaultflow-team-a -w
```

### Emergency Rollback

```bash
# Inspect deployment revision history
kubectl rollout history deployment/vaultflow-api-team-a -n vaultflow-team-a

# Instantly revert to the previous stable revision
kubectl rollout undo deployment/vaultflow-api-team-a -n vaultflow-team-a
```

### PodDisruptionBudget — Node Drain Protection

```bash
# Drain a node — PDB prevents all replicas being evicted simultaneously
kubectl drain desktop-worker --ignore-daemonsets --delete-emptydir-data --force

# ALLOWED DISRUPTIONS drops to 0 — remaining replica is protected
kubectl get pdb -n vaultflow-team-a

# Restore the node after maintenance
kubectl uncordon desktop-worker
```

***

## 🔑 Production Secret Strategy — Sealed Secrets

To keep the entire platform declarable in Git (GitOps workflows) without exposing plaintext credentials, VaultFlow documents [Bitnami Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) as the production secret management approach.

```
[Plaintext Secret]
        +
[kubeseal + Cluster Public Key]
        │
        ▼
[SealedSecret .yaml]  ──►  Push to Git  ──►  Deploy to Cluster
                                                      │
                                                      ▼
                              [Sealed Secrets Controller decrypts]
                                                      │
                                                      ▼
                                          [Native Kubernetes Secret]
```

For external secret stores (HashiCorp Vault, AWS Secrets Manager), the [External Secrets Operator](https://external-secrets.io/) provides an equivalent GitOps-compatible integration path.

***

## 📊 Multi-Environment Values

| Setting | `dev` | `staging` | `prod` |
|---|---|---|---|
| `replicaCount` | 1 | 2 | 3 |
| `psa` | warn | enforce | restricted |
| `pdb.enabled` | false | true | true |
| `pdb.minAvailable` | — | 1 | 2 |
| `ingress.tls` | false | true | true |
| CPU quota | 1 core | 2 cores | 4 cores |
| Memory quota | 2 Gi | 4 Gi | 8 Gi |

***

## 🧭 Concept Coverage Map

| Kubernetes Concept | VaultFlow Implementation |
|---|---|
| RBAC Roles + Bindings | Per-team `Role`, `ClusterRole` for admin, `ServiceAccount` per component |
| Pod Scheduling | `nodeSelector`, `nodeAffinity`, `podAntiAffinity` in `deployment.yaml` |
| Taints + Tolerations | DB node tainted `role=db:NoSchedule`; only DB pods carry matching toleration |
| Storage | `emptyDir` scratch volume + PVC for config history + StatefulSet `volumeClaimTemplates` |
| NetworkPolicy | UI → API only; API → DB only; all else denied |
| Ingress + TLS | Single HTTPS entry point, path-based routing to `/ui`, `/api`, `/admin` |
| PSA + SecurityContext | `restricted` enforced on all team namespaces; full `securityContext` on every container |
| ResourceQuota | Per-team CPU, memory, pod, and secret limits enforced at namespace level |
| PodDisruptionBudget | API pods protected during node drain with `minAvailable` from values |
| Helm Charts | Every resource templated, versioned, multi-env value files |
| Prometheus + Grafana | Deployed via Helm, scraping `/metrics`, dashboards for pod health |
| GitHub Actions CI | `helm lint` + `helm template` on every push and PR |