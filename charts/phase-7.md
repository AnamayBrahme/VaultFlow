# VaultFlow Infrastructure (Phase 7)

## Overview
This repository manages the deployment of the VaultFlow application on Kubernetes. It features a hardened security posture using Network Policies, path-based Ingress routing, and TLS termination.

## 🛠 Infrastructure Highlights
- **Hardened Networking:** Zero-trust architecture using `NetworkPolicy` objects.
- **Traffic Routing:** Path-based ingress routing (/ui, /api, /admin) via NGINX.
- **TLS Security:** Self-signed certificates managed via K8s Secrets.

## 🧪 Verification Methodology
### 1. Application UI Verification
The application is running successfully on the root path `/` over HTTPS.
![Application Running](![alt text](<Screenshot 2026-05-21 at 3.06.06 PM.png>))

### 2. Debugging Logs
If connection issues arise, we utilize our documented debugging workflow:
- **DNS check:** `kubectl run net-diag --image=busybox ... -- nslookup <service>`
- **Direct TCP check:** `kubectl exec -it <pod> -- /bin/sh -c "</dev/tcp/<host>/<port>"`

## 🚀 Quick Start
1. **Initialize:** `skaffold dev`
2. **Access:** Navigate to `https://vaultflow.local:8443/ui`
3. **Verify:** Check the `INFRA_LOG.md` for detailed configuration history.

---
## 📜 Changelog / Infrastructure Log
*See [INFRA_LOG.md](INFRA_LOG.md) for the full history of our infrastructure adjustments.*