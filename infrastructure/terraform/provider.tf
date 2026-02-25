provider "google" {
  project = var.project_id
  region  = var.region
  
  # Use service account key if available, otherwise use application default credentials
  credentials = try(file(var.gcp_credentials_file), null)
}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.eco_gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.eco_gke.master_auth[0].cluster_ca_certificate)
}

data "google_client_config" "default" {}
