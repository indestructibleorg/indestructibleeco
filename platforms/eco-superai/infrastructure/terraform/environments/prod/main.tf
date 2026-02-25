# SuperAI Platform — Terraform: Production Environment
terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "superai-terraform-state"
    key            = "prod/terraform.tfstate"
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
      Environment = "prod"
      ManagedBy   = "terraform"
    }
  }
}

module "core" {
  source = "../../modules"

  project_name           = "superai-platform"
  environment            = "prod"
  region                 = "us-west-2"
  vpc_cidr               = "10.30.0.0/16"
  db_instance_class      = "db.r6g.large"
  db_allocated_storage   = 100
  redis_node_type        = "cache.r6g.large"
  eks_node_instance_type = "m5.xlarge"
  eks_desired_capacity   = 3
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