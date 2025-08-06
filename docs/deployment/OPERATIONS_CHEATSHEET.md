# 🚀 Kubernetes Operations - Cheat Sheet

> **Quick reference per Andrea**: Comandi copy-paste per operazioni comuni

## 🎯 Quick Status Check

```bash
# Status completo di tutti gli ambienti
kubectl get pods -A | grep dataflow-analyzer

# Health check rapido
kubectl get pods,svc,pvc -n osservatorio-dev -o wide

# Logs real-time
kubectl logs -f -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev
```

## 🚀 Deploy & Update

### Deploy Fresh Environment
```bash
# Development (start sempre da qui)
cd k8s/environments/dev && kubectl apply -k .

# Staging (dopo dev OK)
cd k8s/environments/staging && kubectl apply -k .

# Production (ultimo step)
cd k8s/environments/prod && kubectl apply -k .
```

### Update Application
```bash
# Update immagine (esempio 2.0.0 → 2.1.0)
kubectl set image deployment/dataflow-analyzer \
  dataflow-analyzer=osservatorio/dataflow-analyzer:2.1.0 \
  -n osservatorio-dev

# Verifica update
kubectl rollout status deployment/dataflow-analyzer -n osservatorio-dev

# Se va male, rollback
kubectl rollout undo deployment/dataflow-analyzer -n osservatorio-dev
```

## 🔧 Troubleshooting Commands

### Pod Problems
```bash
# Pod status dettagliato
kubectl describe pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# Logs pod precedente (se crashato)
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev --previous

# Entra nel pod per debug
kubectl exec -it $(kubectl get pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev -o jsonpath='{.items[0].metadata.name}') -n osservatorio-dev -- /bin/bash
```

### Network & Service Issues
```bash
# Test connettività interna
kubectl run test-pod --rm -i --tty --image=busybox -n osservatorio-dev -- /bin/sh
# Poi nel pod: wget -O- http://dataflow-analyzer:80/health/ready

# Port forward per test locale
kubectl port-forward svc/dataflow-analyzer 8000:80 -n osservatorio-dev

# Testa da locale: curl http://localhost:8000/health/ready
```

### Storage Issues
```bash
# Check PV/PVC status
kubectl get pv,pvc -A | grep osservatorio

# Storage usage nei pod
kubectl exec -it POD_NAME -n osservatorio-dev -- df -h

# Se storage pieno, cleanup:
kubectl exec -it POD_NAME -n osservatorio-dev -- du -sh /data/*
```

## 📊 Monitoring & Metrics

### Resource Usage
```bash
# Top pods (CPU/Memory)
kubectl top pods -n osservatorio-dev

# Top nodes
kubectl top nodes

# HPA status (se abilitato)
kubectl get hpa -n osservatorio-prod
```

### Events & Logs
```bash
# Eventi recenti (troubleshooting)
kubectl get events -n osservatorio-dev --sort-by='.firstTimestamp' | tail -20

# Logs con filtro
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev | grep ERROR

# Logs su file (per analisi offline)
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev > /tmp/app-logs.txt
```

## ⚖️ Scaling

### Manual Scaling
```bash
# Scale up
kubectl scale deployment dataflow-analyzer --replicas=5 -n osservatorio-dev

# Scale down (per manutenzione)
kubectl scale deployment dataflow-analyzer --replicas=0 -n osservatorio-dev

# Scale back to normal
kubectl scale deployment dataflow-analyzer --replicas=3 -n osservatorio-prod
```

### Auto-scaling Management
```bash
# Abilita HPA
kubectl autoscale deployment dataflow-analyzer --cpu-percent=70 --min=2 --max=10 -n osservatorio-prod

# Check HPA
kubectl get hpa -n osservatorio-prod -w
```

## 🛡️ Security & Secrets

### Secret Management
```bash
# Vedi secrets (senza valori)
kubectl get secrets -n osservatorio-dev

# Edit secret
kubectl edit secret dataflow-analyzer-secrets -n osservatorio-dev

# Create secret da command line
kubectl create secret generic my-secret --from-literal=key=value -n osservatorio-dev
```

### RBAC Debug
```bash
# Check permessi service account
kubectl auth can-i list pods --as=system:serviceaccount:osservatorio-dev:dataflow-analyzer

# Vedi roles
kubectl get roles,rolebindings -n osservatorio-dev
```

## 💾 Backup & Recovery

### Manual Backup
```bash
# Triggera backup ora
kubectl create job manual-backup-$(date +%Y%m%d-%H%M) \
  --from=cronjob/dataflow-analyzer-backup \
  -n osservatorio-dev

# Check backup status
kubectl get jobs -n osservatorio-dev
```

### Recovery Process
```bash
# 1. Scale down app
kubectl scale deployment dataflow-analyzer --replicas=0 -n osservatorio-dev

# 2. List available backups
kubectl exec -it $(kubectl get pod -l job-name=manual-backup-* -n osservatorio-dev -o jsonpath='{.items[0].metadata.name}') -n osservatorio-dev -- ls -la /backup/osservatorio/

# 3. Start restore job (edit timestamp)
cp k8s/manifests/backup-restore-job.yaml /tmp/restore.yaml
# Edit /tmp/restore.yaml with correct timestamp
kubectl apply -f /tmp/restore.yaml

# 4. Wait for restore
kubectl wait --for=condition=complete job/dataflow-analyzer-restore-TIMESTAMP -n osservatorio-dev
```

## 🔄 Environment Management

### Switch Between Environments
```bash
# Set default namespace (evita di scrivere -n ogni volta)
kubectl config set-context --current --namespace=osservatorio-dev

# List all contexts
kubectl config get-contexts

# Switch cluster (se hai multi cluster)
kubectl config use-context production-cluster
```

### Environment Comparison
```bash
# Compare resources across environments
kubectl get pods -n osservatorio-dev -o wide
kubectl get pods -n osservatorio-staging -o wide
kubectl get pods -n osservatorio-prod -o wide

# Compare configurations
kubectl get configmap dataflow-analyzer-config -n osservatorio-dev -o yaml
kubectl get configmap dataflow-analyzer-config -n osservatorio-prod -o yaml
```

## 🚨 Emergency Commands

### Complete Environment Reset
```bash
# ⚠️  DANGER: Questo cancella TUTTO!
kubectl delete namespace osservatorio-dev

# Ricrea da zero
kubectl apply -f k8s/manifests/namespaces.yaml
cd k8s/environments/dev && kubectl apply -k .
```

### Emergency Scale Down (Save Resources)
```bash
# Scale down tutto in dev/staging (mantieni solo prod)
kubectl scale deployment dataflow-analyzer --replicas=0 -n osservatorio-dev
kubectl scale deployment dataflow-analyzer --replicas=0 -n osservatorio-staging
```

### Emergency Pod Restart
```bash
# Restart forzato (kill pod, k8s ne crea nuovo)
kubectl delete pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# Restart con zero downtime (rolling restart)
kubectl rollout restart deployment/dataflow-analyzer -n osservatorio-dev
```

## 📱 Useful Aliases

Aggiungi al tuo `.bashrc` o `.zshrc`:

```bash
# Kubernetes shortcuts
alias k='kubectl'
alias kdev='kubectl -n osservatorio-dev'
alias kstg='kubectl -n osservatorio-staging'
alias kprod='kubectl -n osservatorio-prod'

# App-specific
alias klogs='kubectl logs -f -l app.kubernetes.io/name=dataflow-analyzer'
alias kpods='kubectl get pods -l app.kubernetes.io/name=dataflow-analyzer'
alias kdesc='kubectl describe pod -l app.kubernetes.io/name=dataflow-analyzer'

# Quick status
alias kstatus='kubectl get pods,svc,pvc,hpa -o wide'
```

## 🆘 When Things Go Wrong

### Common Error Patterns
```bash
# "ImagePullBackOff" → Check image name/registry
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A5 "Events:"

# "CrashLoopBackOff" → Check application logs
kubectl logs POD_NAME -n osservatorio-dev --previous

# "Pending" status → Check resources/node capacity
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A10 "Events:"

# Storage issues → Check PVC binding
kubectl get pvc -n osservatorio-dev
```

### Get Help Information
```bash
# K8s resource documentation
kubectl explain pod.spec.containers
kubectl explain deployment.spec.template.spec

# Check cluster capacity
kubectl describe nodes | grep -A5 "Allocated resources"

# Network troubleshooting
kubectl get endpoints dataflow-analyzer -n osservatorio-dev
kubectl get networkpolicies -n osservatorio-dev
```

---

## 📋 Quick Checklist Before Going Home

- [ ] All pods `Running` in production
- [ ] No `CrashLoopBackOff` or `Error` states
- [ ] Recent backup completed successfully
- [ ] Resource usage < 80% (CPU/Memory)
- [ ] No critical alerts in monitoring
- [ ] Development environment can be safely scaled down

**Remember**: When in doubt, check logs first! 90% of issues are visible in the logs. 🔍
