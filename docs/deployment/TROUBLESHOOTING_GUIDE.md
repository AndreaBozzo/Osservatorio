# 🔧 Troubleshooting Guide - Osservatorio Kubernetes

> **Per quando le cose si rompono**: Guida sistematica per risolvere problemi comuni

## 🚨 Diagnostic Framework

### Step 1: Quick Health Assessment
```bash
# 1. Check overall status
kubectl get pods -A | grep dataflow-analyzer

# 2. Check recent events
kubectl get events -A --sort-by='.lastTimestamp' | tail -10

# 3. Check system resources
kubectl top nodes
kubectl top pods -A | head -20
```

### Step 2: Identify Problem Category
- 🔴 **Pod Issues**: CrashLoopBackOff, ImagePull, Running but unhealthy
- 🔶 **Network Issues**: Service not reachable, DNS problems
- 🟡 **Storage Issues**: PVC not binding, disk space
- 🔵 **Resource Issues**: CPU/Memory limits, node pressure
- 🟣 **Config Issues**: Wrong environment variables, missing secrets

---

## 🔴 Pod Issues

### CrashLoopBackOff
```bash
# Symptom: Pod keeps restarting
kubectl get pods -n osservatorio-dev
# STATUS: CrashLoopBackOff

# Diagnosis:
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev --previous
kubectl describe pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# Common Causes & Solutions:
```

#### Cause 1: Database Connection Failed
```
# Log pattern: "Connection refused" or "Database error"
ERROR: Could not connect to database at sqlite:///data/db/osservatorio.db

# Solution:
# Check if PVC is mounted correctly
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A5 "Mounts:"

# Check PVC status
kubectl get pvc -n osservatorio-dev

# If PVC is "Pending", check storage class
kubectl get storageclass
kubectl describe storageclass osservatorio-fast-ssd
```

#### Cause 2: Redis Connection Failed
```
# Log pattern: "Redis connection error"
ERROR: Failed to connect to Redis at localhost:6379

# Solution:
# Check if Redis is running (if using external Redis)
kubectl get pods -l app=redis -A

# Or check if Redis config is correct in dev (should work without Redis)
kubectl edit configmap dataflow-analyzer-config -n osservatorio-dev
# Set DATAFLOW_REDIS_HOST to "" for dev
```

#### Cause 3: Memory/CPU Limits Too Low
```
# Log pattern: "Killed" or OOMKilled events
# Events: "Pod exceeded memory limit"

# Solution:
# Check current limits
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A5 "Limits:"

# Increase limits temporarily
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","resources":{"limits":{"memory":"1Gi","cpu":"1000m"}}}]}}}}'

# Or edit deployment
kubectl edit deployment dataflow-analyzer -n osservatorio-dev
```

### ImagePullBackOff
```bash
# Symptom: Can't pull container image
kubectl get pods -n osservatorio-dev
# STATUS: ImagePullBackOff

# Diagnosis:
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A10 "Events:"

# Common Solutions:
```

#### Solution 1: Image doesn't exist
```bash
# Check if image exists in registry
docker pull osservatorio/dataflow-analyzer:2.0.0

# If not, build and push image first
docker build -t osservatorio/dataflow-analyzer:2.0.0 .
docker push osservatorio/dataflow-analyzer:2.0.0

# Or use local image (for development)
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","imagePullPolicy":"Never"}]}}}}'
```

#### Solution 2: Registry authentication
```bash
# Check if image pull secrets exist
kubectl get secrets -n osservatorio-dev | grep regcred

# Create registry secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=YOUR_REGISTRY \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PASSWORD \
  -n osservatorio-dev

# Add to deployment
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"regcred"}]}}}}'
```

### Pod Running but Unhealthy
```bash
# Symptom: Pod is Running but health checks fail
kubectl get pods -n osservatorio-dev
# STATUS: Running, but READY shows 0/1

# Diagnosis:
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A10 "Conditions:"
kubectl logs POD_NAME -n osservatorio-dev | grep -i health
```

#### Health Check Failures
```bash
# Check health endpoints manually
kubectl port-forward POD_NAME 8000:8000 -n osservatorio-dev

# In another terminal:
curl http://localhost:8000/health/startup
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live

# Common issues:
# 1. App not listening on correct port
# 2. Health endpoint not implemented
# 3. App startup taking too long

# Quick fix: Disable health checks temporarily
kubectl patch deployment dataflow-analyzer -n osservatorio-dev --type='merge' -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","readinessProbe":null,"livenessProbe":null}]}}}}'
```

---

## 🔶 Network Issues

### Service Not Reachable
```bash
# Symptom: Can't reach service from inside cluster
kubectl run test-pod --rm -i --tty --image=busybox -n osservatorio-dev -- /bin/sh
# Inside pod: wget -O- http://dataflow-analyzer/health/ready
# Result: connection refused or timeout

# Diagnosis:
kubectl get svc -n osservatorio-dev
kubectl get endpoints dataflow-analyzer -n osservatorio-dev
```

#### No Endpoints
```bash
# If endpoints is empty, selector might be wrong
kubectl describe svc dataflow-analyzer -n osservatorio-dev
kubectl get pods -n osservatorio-dev --show-labels

# Check if labels match
kubectl edit svc dataflow-analyzer -n osservatorio-dev
# Ensure selector matches pod labels
```

#### DNS Issues
```bash
# Test DNS resolution
kubectl run test-dns --rm -i --tty --image=busybox -n osservatorio-dev -- /bin/sh
# Inside: nslookup dataflow-analyzer
# Should resolve to service IP

# If DNS fails, check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### Network Policies Blocking Traffic
```bash
# Symptom: Service works without network policies but fails with them
kubectl get networkpolicies -n osservatorio-dev

# Quick test: Temporarily remove network policies
kubectl delete networkpolicy --all -n osservatorio-dev

# Test if service works now
# If yes, network policy is too restrictive

# Debug network policy:
kubectl describe networkpolicy POLICY_NAME -n osservatorio-dev

# Common fix: Add missing ingress rules
kubectl edit networkpolicy POLICY_NAME -n osservatorio-dev
```

---

## 🟡 Storage Issues

### PVC Not Binding
```bash
# Symptom: PVC stuck in "Pending" status
kubectl get pvc -n osservatorio-dev

# Diagnosis:
kubectl describe pvc dataflow-analyzer-db-pvc -n osservatorio-dev
kubectl get pv | grep osservatorio
```

#### No Available PV
```bash
# If no PV available, create one
kubectl apply -f k8s/manifests/pv-pvc.yaml

# Check if PV was created
kubectl get pv | grep dataflow-analyzer

# If still issues, check storage class
kubectl get storageclass
kubectl describe storageclass osservatorio-fast-ssd
```

#### Node Affinity Issues
```bash
# Check node labels
kubectl get nodes --show-labels
kubectl describe pv PV_NAME | grep -A5 "Node Affinity"

# Fix: Ensure node has required labels
kubectl label node NODE_NAME kubernetes.io/arch=amd64
```

### Disk Space Issues
```bash
# Symptom: Pod logs show "No space left on device"
kubectl exec -it POD_NAME -n osservatorio-dev -- df -h

# Check what's using space
kubectl exec -it POD_NAME -n osservatorio-dev -- du -sh /data/*

# Clean up old data if needed
kubectl exec -it POD_NAME -n osservatorio-dev -- find /data -name "*.log" -mtime +7 -delete
```

---

## 🔵 Resource Issues

### CPU/Memory Pressure
```bash
# Symptom: Pods being evicted or throttled
kubectl top nodes
kubectl top pods -A | sort -k3 -nr  # Sort by CPU
kubectl describe nodes | grep -A5 "Non-terminated Pods"
```

#### Node Pressure
```bash
# Check node conditions
kubectl describe nodes | grep -A5 "Conditions:"

# Look for: MemoryPressure, DiskPressure, PIDPressure

# If pressure detected:
# 1. Scale down non-essential workloads
kubectl scale deployment dataflow-analyzer --replicas=1 -n osservatorio-dev

# 2. Clean up evicted pods
kubectl get pods -A | grep Evicted | awk '{print $1, $2}' | xargs -n2 kubectl delete pod -n

# 3. Add more nodes (if using managed cluster)
```

#### Pod Resource Limits
```bash
# Check if pods are hitting limits
kubectl top pods -A | grep dataflow-analyzer
kubectl describe pod POD_NAME -n osservatorio-dev | grep -A5 "State:"

# If CPU throttling:
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","resources":{"limits":{"cpu":"2000m"}}}]}}}}'

# If memory issues:
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

---

## 🟣 Configuration Issues

### Wrong Environment Variables
```bash
# Check current environment variables
kubectl exec -it POD_NAME -n osservatorio-dev -- env | grep DATAFLOW

# Check ConfigMap
kubectl get configmap dataflow-analyzer-config -n osservatorio-dev -o yaml

# Check Secrets
kubectl get secret dataflow-analyzer-secrets -n osservatorio-dev -o yaml
```

#### Database URL Issues
```bash
# Common problem: Database path not accessible
kubectl exec -it POD_NAME -n osservatorio-dev -- ls -la /data/db/

# Check if directory exists and has correct permissions
kubectl exec -it POD_NAME -n osservatorio-dev -- mkdir -p /data/db
kubectl exec -it POD_NAME -n osservatorio-dev -- chmod 755 /data/db
```

#### Redis Configuration
```bash
# Check if Redis is expected but not available
kubectl exec -it POD_NAME -n osservatorio-dev -- ping redis
# Should fail in dev (Redis not required)

# Ensure Redis is disabled in development
kubectl patch configmap dataflow-analyzer-config -n osservatorio-dev -p='{"data":{"DATAFLOW_ENABLE_DISTRIBUTED_CACHING":"false"}}'

# Restart deployment to pick up changes
kubectl rollout restart deployment/dataflow-analyzer -n osservatorio-dev
```

---

## 📊 Advanced Debugging

### Enable Debug Mode
```bash
# Temporarily enable debug logging
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","env":[{"name":"DATAFLOW_LOG_LEVEL","value":"DEBUG"}]}]}}}}'

# Watch logs in real-time
kubectl logs -f -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev
```

### Interactive Debugging
```bash
# Get shell inside running pod
kubectl exec -it $(kubectl get pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev -o jsonpath='{.items[0].metadata.name}') -n osservatorio-dev -- /bin/bash

# Inside the pod, check:
ps aux                           # Running processes
netstat -tulpn                   # Open ports
curl http://localhost:8000/health/ready  # Local health check
python -c "import sqlite3; print('DB OK')"  # Test dependencies
```

### Network Debugging
```bash
# Run network debug pod
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: network-debug
  namespace: osservatorio-dev
spec:
  containers:
  - name: debug
    image: nicolaka/netshoot
    command: ["sleep", "3600"]
  restartPolicy: Never
EOF

# Use debug pod for network testing
kubectl exec -it network-debug -n osservatorio-dev -- bash
# Inside: curl, dig, nslookup, tcpdump, etc. available
```

---

## 🚨 Emergency Procedures

### Complete Service Outage
```bash
# 1. Check if it's a cluster-wide issue
kubectl get nodes
kubectl get pods -A | grep -v Running | grep -v Completed

# 2. Scale up from backup environment
kubectl scale deployment dataflow-analyzer --replicas=3 -n osservatorio-staging

# 3. Redirect traffic (if using ingress)
kubectl patch ingress dataflow-analyzer-ingress -p '{"spec":{"rules":[{"host":"your-domain.com","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"dataflow-analyzer","port":{"number":80}}}}]}}]}}'

# 4. Investigate and fix primary environment
```

### Data Corruption
```bash
# 1. Immediately scale down to prevent further damage
kubectl scale deployment dataflow-analyzer --replicas=0 -n osservatorio-prod

# 2. Start restore process
cp k8s/manifests/backup-restore-job.yaml /tmp/restore.yaml
# Edit with latest backup timestamp
kubectl apply -f /tmp/restore.yaml

# 3. Monitor restore
kubectl logs -f job/dataflow-analyzer-restore-TIMESTAMP -n osservatorio-prod
```

### Memory Leak Detection
```bash
# Monitor memory usage over time
kubectl top pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# If memory keeps growing:
# 1. Restart pod immediately
kubectl delete pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# 2. Enable memory profiling (if supported by app)
kubectl patch deployment dataflow-analyzer -n osservatorio-dev -p='{"spec":{"template":{"spec":{"containers":[{"name":"dataflow-analyzer","env":[{"name":"DATAFLOW_ENABLE_PROFILING","value":"true"}]}]}}}}'

# 3. Collect memory dump for analysis
kubectl exec -it POD_NAME -n osservatorio-dev -- python -c "
import gc
import psutil
print(f'Memory: {psutil.Process().memory_info().rss / 1024 / 1024:.2f}MB')
print(f'Objects: {len(gc.get_objects())}')
"
```

---

## 📋 Post-Incident Checklist

After resolving an issue:

- [ ] **Document what happened** (symptoms, root cause, solution)
- [ ] **Update monitoring** to catch this issue earlier next time
- [ ] **Review resource limits** if resource-related
- [ ] **Update runbooks** with new troubleshooting steps
- [ ] **Test backup/restore** if data was involved
- [ ] **Plan preventive measures** (better health checks, alerts, etc.)

---

## 💡 Prevention Tips

1. **Always test in dev first** - Never deploy directly to production
2. **Monitor resource usage** - Set alerts at 70% CPU/Memory
3. **Regular backup tests** - Monthly restore drills
4. **Keep staging in sync** - Same config as prod
5. **Document changes** - Know what changed when issues occur
6. **Use health checks** - Proper startup/liveness/readiness probes
7. **Gradual rollouts** - Use rolling updates, never all at once

**Remember**: 90% of issues are configuration problems. Check configs first! 🔍
