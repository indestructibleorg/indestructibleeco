# SuperAI Platform — Terraform: Staging Environment
terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "superai-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "superai-terraform-locks"
  }
}

provider "aws" {
  region = "us-west-2"

  default_tags {
    tags = {
      Project     = "superai-platform"
      Environment = "staging"
      ManagedBy   = "terraform"
    }
  }
}

module "core" {
  source = "../../modules"

  project_name           = "superai-platform"
  environment            = "staging"
  region                 = "us-west-2"
  vpc_cidr               = "10.20.0.0/16"
  db_instance_class      = "db.t3.medium"
  db_allocated_storage   = 50
  redis_node_type        = "cache.t3.medium"
  eks_node_instance_type = "m5.large"
  eks_desired_capacity   = 2
}

output "vpc_id" {
  value = module.core.vpc_id
}

output "database_endpoint" {
  value     = module.core.database_endpoint
  sensitive = true
}

output "redis_endpoint" {
  value = module.core.redis_endpoint
}