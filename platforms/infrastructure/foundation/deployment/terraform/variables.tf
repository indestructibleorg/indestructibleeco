# Terraform Variables

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "machine-native-ops"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "cloud_provider" {
  description = "Cloud provider (aws, gcp, azure)"
  type        = string
  default     = "aws"
  validation {
    condition     = contains(["aws", "gcp", "azure"], var.cloud_provider)
    error_message = "Cloud provider must be aws, gcp, or azure."
  }
}

# AWS Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS profile name"
  type        = string
  default     = "default"
}

# GCP Variables
variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

# Azure Variables
variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = ""
}

variable "azure_region" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

# Network Variables
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN gateway"
  type        = bool
  default     = false
}

# Kubernetes Variables
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28.0"
}

variable "node_instance_type" {
  description = "Node instance type"
  type        = string
  default     = "t3.medium"
}

variable "node_count" {
  description = "Number of nodes"
  type        = number
  default     = 3
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

# Monitoring Variables
variable "enable_prometheus" {
  description = "Enable Prometheus"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana"
  type        = bool
  default     = true
}

variable "enable_alertmanager" {
  description = "Enable AlertManager"
  type        = bool
  default     = true
}

variable "enable_thanos" {
  description = "Enable Thanos for long-term storage"
  type        = bool
  default     = true
}

variable "monitoring_retention_days" {
  description = "Monitoring data retention days"
  type        = number
  default     = 15
}

variable "monitoring_storage_size" {
  description = "Monitoring storage size"
  type        = string
  default     = "50Gi"
}

# Logging Variables
variable "enable_elasticsearch" {
  description = "Enable Elasticsearch"
  type        = bool
  default     = true
}

variable "enable_kibana" {
  description = "Enable Kibana"
  type        = bool
  default     = true
}

variable "enable_logstash" {
  description = "Enable Logstash"
  type        = bool
  default     = true
}

variable "logging_storage_size" {
  description = "Logging storage size"
  type        = string
  default     = "100Gi"
}

# Security Variables
variable "enable_secrets_manager" {
  description = "Enable secrets manager"
  type        = bool
  default     = true
}

variable "enable_kms" {
  description = "Enable KMS"
  type        = bool
  default     = true
}

variable "enable_iam" {
  description = "Enable IAM"
  type        = bool
  default     = true
}

# Backup Variables
variable "backup_enabled" {
  description = "Enable backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention days"
  type        = number
  default     = 90
}

variable "backup_schedule" {
  description = "Backup schedule (cron format)"
  type        = string
  default     = "0 2 * * *"
}

# Tags
variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}