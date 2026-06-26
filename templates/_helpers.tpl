{{- define "starter-app.name" -}}
starter-app
{{- end }}

{{- define "starter-app.fullname" -}}
{{ include "starter-app.name" . }}
{{- end }}

{{- define "starter-app.labels" -}}
app.kubernetes.io/name: {{ include "starter-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
