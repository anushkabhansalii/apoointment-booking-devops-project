{{- define "slotsync.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "slotsync.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Labels shared by every object. */}}
{{- define "slotsync.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: {{ include "slotsync.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: slotsync
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Selector labels for one component: include "slotsync.selectorLabels" (dict "ctx" . "component" "backend") */}}
{{- define "slotsync.selectorLabels" -}}
app.kubernetes.io/name: {{ include "slotsync.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/* Image tag: component tag > global tag (the Git SHA from CI) > appVersion. */}}
{{- define "slotsync.tag" -}}
{{- .image.tag | default .ctx.Values.global.imageTag | default .ctx.Chart.AppVersion -}}
{{- end -}}

{{- define "slotsync.image" -}}
{{- $tag := include "slotsync.tag" . -}}
{{- with .ctx.Values.global.imageRegistry -}}
{{ printf "%s/%s:%s" . $.image.repository $tag }}
{{- else -}}
{{ printf "%s:%s" .image.repository $tag }}
{{- end -}}
{{- end -}}

{{- define "slotsync.dbSecretName" -}}
{{- .Values.database.existingSecret | default (printf "%s-db" (include "slotsync.fullname" .)) -}}
{{- end -}}

{{- define "slotsync.postgresHost" -}}
{{- printf "%s-postgres" (include "slotsync.fullname" .) -}}
{{- end -}}
