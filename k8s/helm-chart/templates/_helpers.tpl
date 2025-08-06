{{/*
Expand the name of the chart.
*/}}
{{- define "osservatorio.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "osservatorio.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "osservatorio.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "osservatorio.labels" -}}
helm.sh/chart: {{ include "osservatorio.chart" . }}
{{ include "osservatorio.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: osservatorio-platform
{{- end }}

{{/*
Selector labels
*/}}
{{- define "osservatorio.selectorLabels" -}}
app.kubernetes.io/name: {{ include "osservatorio.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "osservatorio.serviceAccountName" -}}
{{- if .Values.rbac.serviceAccount.create }}
{{- default (include "osservatorio.fullname" .) .Values.rbac.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.rbac.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create image name
*/}}
{{- define "osservatorio.image" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) }}
{{- else }}
{{- printf "%s/%s:%s" .Values.image.registry .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) }}
{{- end }}
{{- end }}

{{/*
Create backup image name
*/}}
{{- define "osservatorio.backupImage" -}}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.backup.image.repository .Values.backup.image.tag }}
{{- else }}
{{- printf "%s/%s:%s" .Values.backup.image.registry .Values.backup.image.repository .Values.backup.image.tag }}
{{- end }}
{{- end }}

{{/*
Create storage class name
*/}}
{{- define "osservatorio.storageClass" -}}
{{- if .Values.global.storageClass }}
{{- .Values.global.storageClass }}
{{- else }}
{{- .storageClass | default "default" }}
{{- end }}
{{- end }}

{{/*
Environment-specific values
*/}}
{{- define "osservatorio.environmentValues" -}}
{{- $environment := .Values.app.environment | default "development" }}
{{- if hasKey .Values.environments $environment }}
{{- index .Values.environments $environment }}
{{- else }}
{{- dict }}
{{- end }}
{{- end }}

{{/*
Merge environment-specific resource values
*/}}
{{- define "osservatorio.resources" -}}
{{- $envValues := include "osservatorio.environmentValues" . | fromYaml }}
{{- if $envValues.resources }}
{{- toYaml $envValues.resources }}
{{- else }}
{{- toYaml .Values.resources }}
{{- end }}
{{- end }}

{{/*
Merge environment-specific replica count
*/}}
{{- define "osservatorio.replicaCount" -}}
{{- $envValues := include "osservatorio.environmentValues" . | fromYaml }}
{{- if $envValues.replicaCount }}
{{- $envValues.replicaCount }}
{{- else }}
{{- .Values.deployment.replicaCount }}
{{- end }}
{{- end }}

{{/*
Create environment variables
*/}}
{{- define "osservatorio.env" -}}
- name: DATAFLOW_ENVIRONMENT
  value: {{ .Values.app.environment | quote }}
- name: DATAFLOW_DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "osservatorio.fullname" . }}-secrets
      key: databaseUrl
- name: DATAFLOW_REDIS_HOST
  value: {{ .Values.env.redis.host | quote }}
- name: DATAFLOW_REDIS_PORT
  value: {{ .Values.env.redis.port | quote }}
- name: DATAFLOW_REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "osservatorio.fullname" . }}-secrets
      key: redisPassword
- name: DATAFLOW_JWT_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ include "osservatorio.fullname" . }}-secrets
      key: jwtSecret
- name: DATAFLOW_LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
- name: DATAFLOW_ENABLE_DEBUG
  value: {{ .Values.env.enableDebug | quote }}
- name: DATAFLOW_ENABLE_METRICS
  value: {{ .Values.env.enableMetrics | quote }}
- name: DATAFLOW_ENABLE_TRACING
  value: {{ .Values.env.enableTracing | quote }}
- name: DATAFLOW_ENABLE_CIRCUIT_BREAKER
  value: {{ .Values.env.enableCircuitBreaker | quote }}
- name: DATAFLOW_ENABLE_DISTRIBUTED_CACHING
  value: {{ .Values.env.enableDistributedCaching | quote }}
{{- end }}
