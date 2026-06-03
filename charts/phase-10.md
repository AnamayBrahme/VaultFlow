# 🔵 Phase 10 — Resilience: Verification Manual

This document details the tasks executed to implement, test, and verify high availability, node maintenance protections, and native rolling updates for the `vaultflow-api` deployment.

***

## 🛠️ Step 1: Establish the Guardrails (PodDisruptionBudget)

We deployed a structural governance policy to ensure that during any voluntary cluster maintenance (e.g., node upgrades or drainage), at least one operational instance of the API remains alive to prevent application downtime.

### Manifest Created (`charts/vaultflow-api/templates/pdb.yaml`)

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: vaultflow-api-pdb
  namespace: vaultflow-team-a
spec:
  # Guarantees at least 1 replica stays online during voluntary disruptions
  minAvailable: 1
  selector:
    matchLabels:
      app: vaultflow-api
```

### Verification Command

Ensure the budget rule has been successfully parsed and registered by the cluster controller:

```bash
kubectl get pdb -n vaultflow-team-a
```

***

## 🧪 Step 2: The Maintenance Drill (`kubectl drain`)

We simulated an infrastructure maintenance sequence by completely evacuating workloads from the underlying host server.

**1. Locate the host node:**

```bash
kubectl get pods -n vaultflow-team-a -o wide
```

> **Result:** Target worker node identified as `desktop-worker`.

**2. Execute the safe node drain:**

```bash
kubectl drain desktop-worker --ignore-daemonsets --delete-emptydir-data --force
```

**3. Verify the budget status during eviction:**

```bash
kubectl get pdb -n vaultflow-team-a
```

> **Observation:** The `ALLOWED DISRUPTIONS` counter dropped directly to `0`. This confirmed that the PodDisruptionBudget layer stepped in, locking down remaining instances from being deleted concurrently to guard the API availability threshold.

***

## 🔓 Step 3: Restore Node Operations (`kubectl uncordon`)

Once infrastructure validation routines were complete, we re-enabled scheduling capacity on the host worker node.

**1. Bring the compute node back online:**

```bash
kubectl uncordon desktop-worker
```

**2. Confirm reconciliation and container health:**

```bash
kubectl get pods -n vaultflow-team-a
```

***

## 🔄 Step 4: Execute a Rolling Update

We analysed a configuration transition executed via Skaffold. Because the architecture maps configurations directly to the native API server instead of an abstract packaging tool state, we tracked pure Kubernetes deployment rollout behaviours.

**Watch the orchestration layer handle the live transition:**

```bash
kubectl get pods -n vaultflow-team-a -w
```

### Observed Rollout Log Stream Lifecycle

```plaintext
# 1. New pod version initialized alongside old versions
vaultflow-api-team-a-ff49c655-29xjl     0/1     Running       0          4s

# 2. Traffic hand-off triggers ONLY after readiness checks pass successfully
vaultflow-api-team-a-ff49c655-29xjl     1/1     Running       0          13s
vaultflow-api-team-a-7d45d98c4b-z7pxb   1/1     Terminating   0          3m32s
```

> **Observation:** A new pod variant (`ff49c655-...`) was completely built and reached a solid `READY` status before any older instance (`7d45d98c4b-...`) received a termination signal, securing clean zero-downtime container rotations.

***

## ⏪ Step 5: Execute an Emergency Rollback

Because the Skaffold setup deploys manifests directly via native tracking rather than an isolated Helm release structure, we bypassed package managers and triggered an instantaneous reverse-rollout directly via the control plane.

**1. Inspect the cluster's internal deployment version history:**

```bash
kubectl rollout history deployment/vaultflow-api-team-a -n vaultflow-team-a
```

**2. Instantly undo the last deployment to restore the original stable replicas:**

```bash
kubectl rollout undo deployment/vaultflow-api-team-a -n vaultflow-team-a
```

***

## 📊 Final Phase 10 Verification Check

The environment is confirmed stable, fully protected by an active PDB, and completely verified against deployment rollback procedures.

```bash
kubectl get pods -n vaultflow-team-a
```

### Final Environment State — Target Metrics

| Metric | Target State |
|--------|-------------|
| Pod status | All targets showing `1/1 Running` |
| Restart count | `0` unintended restarts across the ecosystem |