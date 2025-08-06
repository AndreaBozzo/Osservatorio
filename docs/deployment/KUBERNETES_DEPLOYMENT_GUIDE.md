# 🚀 Guida Deployment Kubernetes - Osservatorio ISTAT

> **Per Andrea del futuro**: Questa guida è pensata per te! Segui i passi nell'ordine e tutto funzionerà. 😊

## 📋 Quick Start (TL;DR)

```bash
# 1. Deploy ambiente development (più semplice)
cd k8s/environments/dev
kubectl apply -k .

# 2. Verifica che funzioni
kubectl get pods -n osservatorio-dev
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev
```

**Se tutto va bene, salta alla sezione [Verifica Deployment](#-verifica-deployment)**

---

## 🎯 Cosa abbiamo implementato

### ✅ Completamente Ready:
- **Kubernetes Service**: Versione enterprise con Redis, circuit breaker, health checks
- **Multi-Environment**: Dev, Staging, Production con configurazioni diverse
- **Storage**: Database + Cache + Backup automatici
- **Security**: RBAC, Network Policies, Secret management
- **Backup**: Automatico giornaliero + restore procedure
- **Helm Charts**: Deploy configurabile con valori per ambiente

### 🎛️ Ambienti Disponibili:
- **Development** (`osservatorio-dev`): 1 replica, resource minimi, debug attivo
- **Staging** (`osservatorio-staging`): 2 replica, resource medi, simile produzione
- **Production** (`osservatorio-prod`): 3 replica, HA, security strict

---

## 🚀 Deployment Step-by-Step

### Step 1: Pre-requisiti
```bash
# Verifica che kubectl funzioni
kubectl cluster-info

# Verifica che hai i permessi admin
kubectl auth can-i create namespace

# Se non hai permessi:
# Chiedi al cluster admin di darti cluster-admin role
```

### Step 2: Deploy Base Infrastructure
```bash
# Crea tutti i namespace
kubectl apply -f k8s/manifests/namespaces.yaml

# Verifica namespace creati
kubectl get namespaces | grep osservatorio
# Dovresti vedere: osservatorio-dev, osservatorio-staging, osservatorio-prod
```

### Step 3: Deploy Storage
```bash
# Crea storage classes e persistent volumes
kubectl apply -f k8s/manifests/storageclass.yaml
kubectl apply -f k8s/manifests/pv-pvc.yaml

# Verifica storage
kubectl get storageclass | grep osservatorio
kubectl get pv | grep osservatorio
```

### Step 4A: Deploy Development (Raccomandato per iniziare)
```bash
# Vai nella directory dev
cd k8s/environments/dev

# Deploy tutto l'ambiente dev
kubectl apply -k .

# Attendi che i pod siano ready (ci vogliono ~2 minuti)
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev --timeout=300s

# Verifica deployment
kubectl get all -n osservatorio-dev
```

### Step 4B: Deploy Production (Solo quando dev funziona)
```bash
# Prima assicurati che development funzioni!
cd k8s/environments/prod

# Deploy produzione
kubectl apply -k .

# Attendi deployment (HA setup richiede più tempo)
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-prod --timeout=600s

# Verifica che tutti i 3 pod siano running
kubectl get pods -n osservatorio-prod
```

---

## 📊 Verifica Deployment

### Quick Health Check
```bash
# Controlla che i pod siano healthy
kubectl get pods -n osservatorio-dev

# OUTPUT ATTESO:
# NAME                                READY   STATUS    RESTARTS   AGE
# dataflow-analyzer-xxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### Controlla i Logs
```bash
# Vedi gli ultimi logs
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev --tail=50

# OUTPUT ATTESO: Dovresti vedere:
# - "Starting dataflow analyzer service..."
# - "Database connection established"
# - "Redis cache connected"
# - "Health checks enabled"
# - Nessun "ERROR" o "CRITICAL"
```

### Test dell'Applicazione
```bash
# Port forward per testare localmente
kubectl port-forward svc/dataflow-analyzer 8000:80 -n osservatorio-dev

# In un altro terminale, testa l'endpoint
curl http://localhost:8000/health/ready
# OUTPUT ATTESO: {"status":"healthy","checks":{"database":"ok","redis":"ok"}}

# Testa l'endpoint principale
curl http://localhost:8000/api/v1/dataflows?limit=5
# OUTPUT ATTESO: Lista di dataflow ISTAT
```

---

## 🔧 Troubleshooting

### ❌ Pod non parte (CrashLoopBackOff)
```bash
# Vedi i logs dettagliati
kubectl logs -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev --previous

# Problemi comuni:
# 1. "No space left on device" → Aumenta storage o pulisci nodi
# 2. "Connection refused to Redis" → Verifica che Redis sia up
# 3. "Permission denied" → Controlla RBAC settings
```

### ❌ Persistent Volume non si attacca
```bash
# Controlla PV status
kubectl get pv | grep osservatorio
# Status deve essere "Bound", non "Available" o "Failed"

# Se è "Available", controlla PVC
kubectl get pvc -n osservatorio-dev
# Status deve essere "Bound"

# Fix comune:
kubectl delete pvc dataflow-analyzer-db-pvc -n osservatorio-dev
kubectl apply -k k8s/environments/dev/
```

### ❌ "ImagePullBackOff" Error
```bash
# Controlla l'immagine
kubectl describe pod -l app.kubernetes.io/name=dataflow-analyzer -n osservatorio-dev

# Fix: Usa immagine locale o build prima
# Nel deployment.yaml, cambia:
# image: osservatorio/dataflow-analyzer:2.0.0
# a:
# image: localhost:5000/dataflow-analyzer:latest  # Se hai registry locale
```

### ❌ Network Policy blocca connessioni
```bash
# Temporaneamente disabilita network policies
kubectl delete networkpolicy --all -n osservatorio-dev

# Testa se ora funziona
kubectl get pods -n osservatorio-dev

# Se funziona, il problema era network policy
# Riapplica con policy più permissive per debug
```

---

## 🛡️ Security & Production

### Per Production:
1. **Cambia le password di default** in `k8s/manifests/secret.yaml`
2. **Configura TLS** per gli endpoint esterni
3. **Abilita monitoring** (Prometheus + Grafana)
4. **Testa backup/restore** prima di andare live

### Security Checklist:
- [ ] Secrets non sono in plain text nel codice
- [ ] Network Policies sono attive in produzione
- [ ] RBAC limita accessi al minimo necessario
- [ ] Health checks configurati correttamente
- [ ] Backup testato almeno una volta

---

## 🔄 Operazioni Comuni

### Aggiornare l'applicazione
```bash
# Update dell'immagine
kubectl set image deployment/dataflow-analyzer dataflow-analyzer=osservatorio/dataflow-analyzer:2.1.0 -n osservatorio-dev

# Verifica rollout
kubectl rollout status deployment/dataflow-analyzer -n osservatorio-dev
```

### Scalare l'applicazione
```bash
# Scale manuale
kubectl scale deployment dataflow-analyzer --replicas=5 -n osservatorio-prod

# Verifica scaling
kubectl get pods -n osservatorio-prod
```

### Vedere metriche e status
```bash
# Top resource usage
kubectl top pods -n osservatorio-dev

# Eventi del cluster
kubectl get events -n osservatorio-dev --sort-by='.firstTimestamp'

# Status HPA (se abilitato)
kubectl get hpa -n osservatorio-prod
```

### Backup manuale
```bash
# Triggera backup immediato
kubectl create job --from=cronjob/dataflow-analyzer-backup manual-backup-$(date +%Y%m%d) -n osservatorio-dev

# Verifica backup
kubectl get jobs -n osservatorio-dev
kubectl logs job/manual-backup-YYYYMMDD -n osservatorio-dev
```

---

## 🎛️ Configurazioni Avanzate

### Usare Helm (Opzionale, più flessibile)
```bash
# Install da helm chart
cd k8s/helm-chart

# Development
helm install osservatorio-dev . -f values.yaml \
  --set app.environment=development \
  --set deployment.replicaCount=1 \
  --namespace osservatorio-dev

# Production
helm install osservatorio-prod . -f values.yaml \
  --set app.environment=production \
  --set deployment.replicaCount=3 \
  --namespace osservatorio-prod
```

### Configurare diversi database
```bash
# Edit del ConfigMap per DB diversi
kubectl edit configmap dataflow-analyzer-config -n osservatorio-dev

# Oppure usa kustomization patches specifiche per ambiente
```

---

## 📞 Quando Chiedere Aiuto

### 🚨 Situazioni di Emergenza:
- **Pod tutti down in produzione** → Rollback immediato
- **Storage pieno** → Scale down + cleanup
- **Memory leak** → Restart pod + investiga

### 🤔 Situazioni "Normali" ma Confuse:
- **Metriche strane** → Controlla Grafana dashboards
- **Performance lente** → Check resource limits
- **Errori intermittenti** → Analizza logs con pattern

### 💡 Pro Tips:
1. **Sempre testa prima in dev**, poi staging, poi prod
2. **Tieni logs di quello che fai** (kubectl commands)
3. **Fai backup prima di cambi major**
4. **Usa namespace per isolamento** (non mixare ambienti)

---

## 📚 File di Riferimento Rapido

```
k8s/
├── manifests/           # YAML base per tutti gli ambienti
│   ├── deployment.yaml  # Container definition
│   ├── service.yaml     # Service discovery
│   ├── pv-pvc.yaml     # Storage
│   └── secret.yaml      # Passwords (CAMBIALE!)
├── environments/        # Configurazioni per ambiente
│   ├── dev/            # 1 replica, debug ON
│   ├── staging/        # 2 replica, production-like
│   └── prod/           # 3 replica, HA, strict security
└── helm-chart/         # Deploy flessibile con Helm
    ├── Chart.yaml      # Metadata
    ├── values.yaml     # Configurazione default
    └── templates/      # Template Kubernetes
```

**Remember**: Se qualcosa non funziona, parte sempre da `osservatorio-dev` e sale gradualmente! 🚀
