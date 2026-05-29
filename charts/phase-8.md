## 🔒 Cluster Hardening & Local Development Lifecycle (Phase 8)

This project utilizes a fully automated, synchronized GitOps-style local development pipeline managed by **Skaffold** and **Helm**. The local cluster is hardened against unauthorized network cross-talk, resource starvation, and privilege escalation.

### 🏗️ Architecture Overview

The local stack automatically splits development concerns and enforces infrastructure constraints in real-time:
- **Code Hot-Reloading:** Changes to the Python backend (`./app`) trigger optimized, localized container updates.
- **Infrastructure-as-Code (IaC) Automation:** Modifications to Helm templates, values, or security policies trigger a background `helm upgrade` instantly.

### 🛡️ Implemented Security Controls

1. **Pod Security Admission (PSA):** Enforces a strict `restricted` profile on the `vaultflow-team-a` namespace to block privileged containers.
2. **Network Isolation (`NetworkPolicy`):** Enforces a `default-deny` ingress posture on the database namespace (`vaultflow-team-b`). Explicitly whitelists traffic *only* from the API service via internal cluster DNS.
3. **Resource Guardrails (`ResourceQuota`):** Implements strict namespace boundaries to prevent local cluster Denial of Service (DoS):
   - Max Pods: `12` (with overhead allocation for rolling updates)
   - CPU Requests/Limits: `2` Cores / `4` Cores Max
   - Memory Requests/Limits: `2Gi` / `4Gi` Max

---

### 🚀 Getting Started (Local Dev)

#### Prerequisites
- [Skaffold](https://skaffold.dev/) (v4beta11 or higher)
- [Helm](https://helm.sh/)
- A local Kubernetes cluster ([Kind](https://kind.sigs.k8s.io/) or Minikube)

#### Spin Up the Environment
Run the following command in the root directory to initiate the automated builder, deployment engine, and secure port-forwards:

```bash
skaffold dev