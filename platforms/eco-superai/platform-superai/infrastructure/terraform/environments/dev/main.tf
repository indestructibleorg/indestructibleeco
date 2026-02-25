# SuperAI Platform — Terraform: Development Environment
terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "superai-terraform-state"
    key            = "dev/terraform.tfstate"
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
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

module "core" {
  source = "../../modules"

  project_name           = "superai-platform"
  environment            = "dev"
  region                 = "us-west-2"
  vpc_cidr               = "10.10.0.0/16"
  db_instance_class      = "db.t3.micro"
  db_allocated_storage   = 20
  redis_node_type        = "cache.t3.micro"
  eks_node_instance_type = "t3.large"
  eks_desired_capacity   = 1
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