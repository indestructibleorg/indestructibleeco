#!/bin/bash
# Create GKE cluster for IndestructibleEco Production

set -e

PROJECT_ID="my-project-ops-1991"
REGION="asia-east1"
CLUSTER_NAME="eco-production"
NETWORK="default"
SUBNET="default"

echo "Creating GKE cluster: ${CLUSTER_NAME}"

gcloud container clusters create ${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --network=${NETWORK} \
  --subnetwork=${SUBNET} \
  --machine-type=e2-medium \
  --num-nodes=1 \
  --min-nodes=1 \
  --max-nodes=3 \
  --enable-autoscaling \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-vertical-pod-autoscaling \
  --enable-master-authorized-networks \
  --master-authorized-networks=0.0.0.0/0 \
  --monitoring=SYSTEM \
  --logging=SYSTEM,WORKLOAD \
  --tags=eco-production \
  --labels=environment=production,team=platform

echo "Getting cluster credentials..."
gcloud container clusters get-credentials ${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID}

echo "Verifying cluster connection..."
kubectl cluster-info

echo "Creating namespace..."
kubectl create namespace eco-production --dry-run=client -o yaml | kubectl apply -f -

echo "GKE cluster created successfully!"