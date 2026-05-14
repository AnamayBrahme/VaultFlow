# VaultFlow 🔐

![Helm](https://img.shields.io/badge/Helm-3.x-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.29-blue)
![PSA](https://img.shields.io/badge/Pod%20Security-Restricted-green)
![Python](https://img.shields.io/badge/Python-Flask-yellow)
![Prometheus](https://img.shields.io/badge/Monitoring-Prometheus-orange)

> A secure, multi-team internal platform for managing application
> configurations and secrets in a Kubernetes-native way.

## Problem Statement

Engineering teams at fast-growing companies face a recurring problem:
configs and secrets are scattered across .env files, CI/CD variables,
and ad-hoc Kubernetes Secrets with no access control, no isolation
between teams, and no audit trail. VaultFlow solves this by giving
each team an isolated namespace, enforced resource boundaries, and a
hardened REST API — all deployed through versioned Helm charts.

## Namespaces

| Namespace            | Purpose                                        |
|----------------------|------------------------------------------------|
| vaultflow-system     | Core platform: Ingress, DB, Observability      |
| vaultflow-team-a     | Team A isolated namespace (PSA restricted)     |
| vaultflow-team-b     | Team B isolated namespace (PSA restricted)     |
| vaultflow-admin      | Admin-only namespace (ClusterRole access)      |

## Quick Start

```bash
bash scripts/setup-cluster.sh
bash scripts/install-all.sh dev
```
