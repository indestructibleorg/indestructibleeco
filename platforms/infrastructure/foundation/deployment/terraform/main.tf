# MachineNativeOps Enterprise Infrastructure
# Terraform configuration for cloud-agnostic infrastructure deployment

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "s3" {
    bucket         = "machine-native-ops-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "machine-native-ops-terraform-locks"
  }
}

# Provider configurations (select based on cloud provider)
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
  
  default_tags {
    tags = {
      Project     = "MachineNativeOps"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  
  default_tags {
    tags = {
      Project     = "MachineNativeOps"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
  
  default_tags {
    tags = {
      Project     = "MachineNativeOps"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# Local variables
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# VPC Module (AWS)
module "vpc" {
  source = "./modules/vpc"
  
  count   = var.cloud_provider == "aws" ? 1 : 0
  project_name = local.name_prefix
  environment = var.environment
  
  cidr_block           = var.vpc_cidr
  availability_zones   = var.availability_zones
  enable_nat_gateway   = var.enable_nat_gateway
  enable_vpn_gateway   = var.enable_vpn_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = local.common_tags
}

# EKS Cluster Module (AWS)
module "eks_cluster" {
  source = "./modules/eks"
  
  count = var.cloud_provider == "aws" ? 1 : 0
  
  project_name = local.name_prefix
  environment = var.environment
  
  vpc_id     = var.cloud_provider == "aws" ? module.vpc[0].vpc_id : ""
  subnet_ids = var.cloud_provider == "aws" ? module.vpc[0].private_subnet_ids : []
  
  cluster_version    = var.kubernetes_version
  node_instance_type = var.node_instance_type
  node_count         = var.node_count
  
  tags = local.common_tags
}

# GKE Cluster Module (GCP)
module "gke_cluster" {
  source = "./modules/gke"
  
  count = var.cloud_provider == "gcp" ? 1 : 0
  
  project_id  = var.gcp_project_id
  region      = var.gcp_region
  zone        = var.gcp_zone
  
  cluster_name = local.name_prefix
  node_count   = var.node_count
  machine_type = var.node_instance_type
  
  tags = local.common_tags
}

# AKS Cluster Module (Azure)
module "aks_cluster" {
  source = "./modules/aks"
  
  count = var.cloud_provider == "azure" ? 1 : 0
  
  resource_group_name = "${local.name_prefix}-rg"
  location            = var.azure_region
  cluster_name        = local.name_prefix
  
  node_count   = var.node_count
  node_size    = var.node_instance_type
  
  tags = local.common_tags
}

# Monitoring Stack Module
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name = local.name_prefix
  environment = var.environment
  
  depends_on = [
    module.eks_cluster,
    module.gke_cluster,
    module.aks_cluster
  ]
  
  enable_prometheus    = var.enable_prometheus
  enable_grafana       = var.enable_grafana
  enable_alertmanager  = var.enable_alertmanager
  enable_thanos        = var.enable_thanos
  
  retention_days     = var.monitoring_retention_days
  storage_size       = var.monitoring_storage_size
  
  tags = local.common_tags
}

# Logging Stack Module
module "logging" {
  source = "./modules/logging"
  
  project_name = local.name_prefix
  environment = var.environment
  
  enable_elasticsearch = var.enable_elasticsearch
  enable_kibana        = var.enable_kibana
  enable_logstash      = var.enable_logstash
  
  storage_size       = var.logging_storage_size
  
  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"
  
  project_name = local.name_prefix
  environment = var.environment
  
  enable_secrets_manager = var.enable_secrets_manager
  enable_kms           = var.enable_kms
  enable_iam           = var.enable_iam
  
  tags = local.common_tags
}

# Backup Module
module "backup" {
  source = "./modules/backup"
  
  project_name = local.name_prefix
  environment = var.environment
  
  backup_enabled     = var.backup_enabled
  retention_days     = var.backup_retention_days
  backup_schedule    = var.backup_schedule
  
  tags = local.common_tags
}

# Outputs
output "cluster_endpoint" {
  description = "Kubernetes cluster endpoint"
  value       = var.cloud_provider == "aws" ? module.eks_cluster[0].cluster_endpoint : 
                var.cloud_provider == "gcp" ? module.gke_cluster[0].cluster_endpoint :
                var.cloud_provider == "azure" ? module.aks_cluster[0].cluster_endpoint : ""
}

output "cluster_name" {
  description = "Kubernetes cluster name"
  value       = var.cloud_provider == "aws" ? module.eks_cluster[0].cluster_name : 
                var.cloud_provider == "gcp" ? module.gke_cluster[0].cluster_name :
                var.cloud_provider == "azure" ? module.aks_cluster[0].cluster_name : ""
}

output "vpc_id" {
  description = "VPC ID"
  value       = var.cloud_provider == "aws" ? module.vpc[0].vpc_id : ""
}

output "monitoring_grafana_url" {
  description = "Grafana dashboard URL"
  value       = module.monitoring.grafana_url
}

output "logging_kibana_url" {
  description = "Kibana dashboard URL"
  value       = module.logging.kibana_url
}