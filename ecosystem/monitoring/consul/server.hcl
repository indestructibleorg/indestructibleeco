datacenter              = "dc1"
data_dir                = "/consul/data"
log_level               = "INFO"
server                  = true
bootstrap_expect        = 1

ui_config { enabled = true }
connect    { enabled = true }

ports {
  grpc  = 8502
  https = 8501
}

acl {
  enabled        = false
  default_policy = "allow"
}

telemetry {
  prometheus_retention_time = "60s"
  disable_hostname          = true
}
