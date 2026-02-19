datacenter = "dc1"
data_dir = "/opt/consul"
log_level = "INFO"
server = true
bootstrap_expect = 1
ui_config { enabled = true }
connect { enabled = true }
ports { grpc = 8502 }
