{{/*
IndestructibleEco v1.0 — Helm Template Helpers
URI: indestructibleeco://helm/templates/helpers
*/}}

{{- define "eco.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "eco.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "eco.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: indestructibleeco
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
platform: indestructibleeco
managed-by: yaml-toolkit-v1
schema-version: v1
{{- end }}

{{- define "eco.selectorLabels" -}}
app.kubernetes.io/name: {{ include "eco.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "eco.namespace" -}}
{{- default "indestructibleeco" .Values.global.namespace }}
{{- end }}