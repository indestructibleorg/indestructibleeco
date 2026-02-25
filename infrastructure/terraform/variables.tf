variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "my-project-ops-1991"
}

variable "gcp_credentials_file" {
  description = "Path to GCP service account credentials JSON file"
  type        = string
  default     = ""
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-east1"
}

variable "machine_type" {
  description = "GKE node machine type"
  type        = string
  default     = "e2-standard-2"
}

variable "node_count" {
  description = "Initial number of GKE nodes"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of GKE nodes for autoscaling"
  type        = number
  default     = 5
}
