# 🚀 Kubernetes Deployment Documentation

> **Everything you need to deploy and manage Osservatorio on Kubernetes**

## 📚 Documentation Overview

### 🎯 Start Here
- **[Kubernetes Deployment Guide](KUBERNETES_DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment guide
- **[Operations Cheat Sheet](OPERATIONS_CHEATSHEET.md)** - Quick reference for daily operations
- **[Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Systematic problem-solving guide

### 🏗️ What We've Built

This Kubernetes infrastructure includes:

#### ✅ **Production-Ready Features**
- **Multi-Environment Support**: Dev, Staging, Production with different configurations
- **Persistent Storage**: Database, cache, and backup storage with different performance tiers
- **High Availability**: Pod disruption budgets, anti-affinity rules, health checks
- **Auto-Scaling**: Horizontal Pod Autoscaler based on CPU/Memory
- **Security**: RBAC, Network Policies, Secret management
- **Backup & Recovery**: Automated daily backups with restore procedures

#### 🛠️ **Architecture Components**
- **Application Service**: Kubernetes-ready dataflow analysis service
- **Distributed Caching**: Redis integration with connection pooling
- **Circuit Breakers**: Resilience patterns for external dependencies
- **Health Monitoring**: Startup/liveness/readiness probes
- **Observability**: Metrics, logging, tracing support

## 🚀 Quick Start

### For First-Time Deployment
```bash
# 1. Deploy development environment
cd k8s/environments/dev
kubectl apply -k .

# 2. Verify it's working
kubectl get pods -n osservatorio-dev
kubectl port-forward svc/dataflow-analyzer 8000:80 -n osservatorio-dev

# 3. Test the application
curl http://localhost:8000/health/ready
```

### For Daily Operations
```bash
# Check application status
kubectl get pods,svc -n osservatorio-dev

# View logs
kubectl logs -f -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# Scale application
kubectl scale deployment dataflow-analyzer --replicas=3 -n osservatorio-prod
```

## 📁 File Structure

```
k8s/
├── manifests/              # Base Kubernetes manifests
│   ├── deployment.yaml     # Application deployment
│   ├── service.yaml        # Service discovery
│   ├── configmap.yaml      # Configuration
│   ├── secret.yaml         # Secrets (passwords, API keys)
│   ├── storageclass.yaml   # Storage classes for different tiers
│   ├── pv-pvc.yaml        # Persistent volumes and claims
│   ├── backup-cronjob.yaml # Automated backup jobs
│   ├── networkpolicy.yaml  # Network security policies
│   └── namespaces.yaml     # Multi-environment namespaces
│
├── environments/           # Environment-specific configurations
│   ├── dev/               # Development (1 replica, debug enabled)
│   │   ├── kustomization.yaml
│   │   └── deployment-patch.yaml
│   ├── staging/           # Staging (2 replicas, production-like)
│   │   ├── kustomization.yaml
│   │   └── deployment-patch.yaml
│   └── prod/              # Production (3 replicas, HA, strict security)
│       ├── kustomization.yaml
│       ├── deployment-patch.yaml
│       └── networkpolicy.yaml
│
├── helm-chart/            # Helm chart for flexible deployment
│   ├── Chart.yaml         # Chart metadata
│   ├── values.yaml        # Default configuration values
│   └── templates/         # Kubernetes resource templates
│       ├── _helpers.tpl   # Template helpers
│       ├── deployment.yaml
│       ├── service.yaml
│       └── pvc.yaml
│
└── examples/
    └── deploy-all.yaml    # Single-file deployment (for testing)
```

## 🌍 Environment Configurations

### Development (`osservatorio-dev`)
- **Purpose**: Feature development and testing
- **Replicas**: 1
- **Resources**: Minimal (256Mi RAM, 100m CPU)
- **Features**: Debug logging, relaxed health checks, no network policies
- **Storage**: 20Gi database, 10Gi cache

### Staging (`osservatorio-staging`)
- **Purpose**: Pre-production testing
- **Replicas**: 2
- **Resources**: Medium (1Gi RAM, 250m CPU)
- **Features**: Production-like config, monitoring enabled
- **Storage**: 20Gi database, 10Gi cache, 100Gi backup

### Production (`osservatorio-prod`)
- **Purpose**: Live production service
- **Replicas**: 3 (with auto-scaling)
- **Resources**: High (2Gi RAM, 500m CPU)
- **Features**: Strict security, monitoring, backups, HA
- **Storage**: 50Gi database, 20Gi cache, 500Gi backup

## 🛡️ Security Features

### RBAC (Role-Based Access Control)
- Service accounts with minimal required permissions
- Separate roles for different components
- No cluster-admin privileges for application pods

### Network Policies
- Default deny-all ingress/egress
- Selective allow rules for necessary communication
- Environment-specific policies (stricter in production)
- Microsegmentation between services

### Secrets Management
- All passwords and API keys stored in Kubernetes secrets
- Base64 encoded (not plain text in manifests)
- Mounted as files (not environment variables)
- Environment-specific secrets

## 💾 Storage Strategy

### Storage Classes
- **osservatorio-fast-ssd**: High-performance SSD for database and cache
- **osservatorio-standard**: Standard HDD for general use
- **osservatorio-backup**: Cold storage for backups and archives

### Backup Strategy
- **Automated Daily Backups**: CronJob at 2 AM local time
- **Retention**: 30 days for regular backups
- **Backup Types**: Full backup (database + cache + application data)
- **Restore Procedure**: Automated restore job with scaling coordination

## 📊 Monitoring & Observability

### Health Checks
- **Startup Probe**: Ensures application is fully initialized
- **Liveness Probe**: Detects if application is stuck and needs restart
- **Readiness Probe**: Controls traffic routing to healthy pods

### Metrics & Monitoring
- Application metrics exposed on port 8001
- Prometheus-compatible format
- Grafana dashboard ready (templates in monitoring namespace)
- Resource usage tracking (CPU, memory, storage)

## 🎯 Deployment Strategies

### Using Kustomize (Recommended)
```bash
# Deploy specific environment
kubectl apply -k k8s/environments/dev/
kubectl apply -k k8s/environments/staging/
kubectl apply -k k8s/environments/prod/
```

### Using Helm (Advanced)
```bash
# Install with custom values
helm install osservatorio k8s/helm-chart/ \
  --set app.environment=production \
  --set deployment.replicaCount=3 \
  --namespace osservatorio-prod
```

### Using Raw Manifests (Simple)
```bash
# Apply all base manifests
kubectl apply -f k8s/manifests/
```

## ⚡ Performance Tuning

### Resource Optimization
- **Development**: Minimal resources for cost savings
- **Staging**: Realistic resource allocation for testing
- **Production**: Generous limits with auto-scaling

### Horizontal Pod Autoscaling
- **Target**: 70% CPU, 80% Memory utilization
- **Min Replicas**: 3 (production), 2 (staging), 1 (development)
- **Max Replicas**: 10 (production), 5 (staging), 2 (development)

## 🆘 Support & Troubleshooting

### Common Issues
1. **Pod not starting** → Check [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md#pod-issues)
2. **Service not reachable** → Check [Network Issues](TROUBLESHOOTING_GUIDE.md#network-issues)
3. **Storage problems** → Check [Storage Issues](TROUBLESHOOTING_GUIDE.md#storage-issues)
4. **Performance problems** → Check [Resource Issues](TROUBLESHOOTING_GUIDE.md#resource-issues)

### Getting Help
- **Logs**: `kubectl logs -f -l app.kubernetes.io/name=dataflow-analyzer -n NAMESPACE`
- **Status**: `kubectl get pods,svc,pvc -n NAMESPACE -o wide`
- **Events**: `kubectl get events -n NAMESPACE --sort-by='.lastTimestamp'`

### Emergency Contacts
- **Development Issues**: Check logs first, then restart pods
- **Production Issues**: Follow incident response procedure
- **Security Issues**: Immediate escalation required

---

## 📝 Next Steps

### For New Deployments
1. ✅ Read the [Deployment Guide](KUBERNETES_DEPLOYMENT_GUIDE.md)
2. ✅ Start with development environment
3. ✅ Test all functionality before promoting to staging
4. ✅ Run backup/restore test
5. ✅ Configure monitoring and alerts
6. ✅ Document any customizations

### For Ongoing Operations
1. ✅ Bookmark the [Operations Cheat Sheet](OPERATIONS_CHEATSHEET.md)
2. ✅ Set up monitoring dashboards
3. ✅ Schedule regular backup tests
4. ✅ Plan capacity upgrades
5. ✅ Review and update security policies

### For Troubleshooting
1. ✅ Keep the [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) handy
2. ✅ Set up log aggregation
3. ✅ Configure alerting rules
4. ✅ Practice incident response procedures

---

**Remember**: Start small (dev), test thoroughly (staging), deploy confidently (production)! 🚀
