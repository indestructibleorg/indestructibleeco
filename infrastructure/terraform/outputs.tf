output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.eco_gke.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.eco_gke.endpoint
  sensitive   = true
}

output "gke_region" {
  description = "GKE cluster region"
  value       = google_container_cluster.eco_gke.location
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.eco_repo.repository_id}"
}

output "github_actions_service_account_email" {
  description = "GitHub Actions service account email"
  value       = google_service_account.github_actions.email
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.eco_gke.name} --region ${google_container_cluster.eco_gke.location} --project ${var.project_id}"
}
