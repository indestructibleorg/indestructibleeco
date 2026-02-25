terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "sts.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Create VPC network
resource "google_compute_network" "eco_vpc" {
  name                    = "eco-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required_apis]
}

# Create subnet with secondary ranges for pods and services
resource "google_compute_subnetwork" "eco_subnet" {
  name          = "eco-subnet-${var.region}"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.eco_vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.4.0.0/14"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.0.16.0/20"
  }
}

# Create GKE cluster
resource "google_container_cluster" "eco_gke" {
  name     = "eco-base-gke"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.eco_vpc.name
  subnetwork = google_compute_subnetwork.eco_subnet.name

  # IP allocation policy for VPC-native cluster
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Network policy
  network_policy {
    enabled = true
  }

  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
  }

  # Logging and monitoring
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  depends_on = [
    google_project_service.required_apis,
    google_compute_subnetwork.eco_subnet
  ]
}

# Separately Managed Node Pool
resource "google_container_node_pool" "eco_nodes" {
  name       = "eco-node-pool"
  location   = var.region
  cluster    = google_container_cluster.eco_gke.name
  node_count = var.node_count

  autoscaling {
    min_node_count = var.node_count
    max_node_count = var.max_node_count
  }

  node_config {
    preemptible  = false
    machine_type = var.machine_type

    disk_size_gb = 50
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    labels = {
      environment = "production"
      managed_by  = "terraform"
    }

    tags = ["gke-node", "eco-base"]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Create Kubernetes namespace for infrastructure
resource "kubernetes_namespace_v1" "infra" {
  metadata {
    name = "infra"
    labels = {
      name = "infra"
    }
  }

  depends_on = [
    google_container_node_pool.eco_nodes,
    data.google_client_config.default
  ]
}

# Create Kubernetes namespace for platform-01
resource "kubernetes_namespace_v1" "platform_01" {
  metadata {
    name = "platform-01"
    labels = {
      name = "platform-01"
    }
  }

  depends_on = [
    google_container_node_pool.eco_nodes,
    data.google_client_config.default
  ]
}

# Create Kubernetes namespace for platform-02
resource "kubernetes_namespace_v1" "platform_02" {
  metadata {
    name = "platform-02"
    labels = {
      name = "platform-02"
    }
  }

  depends_on = [
    google_container_node_pool.eco_nodes,
    data.google_client_config.default
  ]
}

# Create Kubernetes namespace for platform-03
resource "kubernetes_namespace_v1" "platform_03" {
  metadata {
    name = "platform-03"
    labels = {
      name = "platform-03"
    }
  }

  depends_on = [
    google_container_node_pool.eco_nodes,
    data.google_client_config.default
  ]
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "eco_repo" {
  location      = var.region
  repository_id = "eco-base"
  description   = "Docker repository for eco-base images"
  format        = "DOCKER"

  docker_config {
    immutable_tags = false
  }

  depends_on = [google_project_service.required_apis]
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"
}

# IAM binding for GitHub Actions to push to Artifact Registry
resource "google_artifact_registry_repository_iam_member" "github_actions_writer" {
  location   = google_artifact_registry_repository.eco_repo.location
  repository = google_artifact_registry_repository.eco_repo.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.github_actions.email}"
}

# IAM binding for GitHub Actions to deploy to GKE
resource "google_project_iam_member" "github_actions_gke" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
