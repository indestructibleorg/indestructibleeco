#!/usr/bin/env python3
"""
OAuth 2.0 Configuration Setup Script for IndestructibleEco

This script automates the setup of OAuth 2.0 configuration for GKE/IAP integration.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google.cloud import secretmanager
    from google.auth import default
except ImportError:
    print("Error: google-cloud-secret-manager not installed")
    print("Install with: pip install google-cloud-secret-manager")
    sys.exit(1)


class OAuthSetup:
    """OAuth 2.0 Configuration Setup"""
    
    def __init__(self, project_id: str, environment: str):
        self.project_id = project_id
        self.environment = environment
        self.client = secretmanager.SecretManagerServiceClient()
        
    def create_oauth_config(self, client_id: str, client_secret: str) -> dict:
        """Create OAuth configuration"""
        config = {
            "oauth": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [
                    f"https://{self.environment}.autoecoops.io/auth/callback",
                    "http://localhost:3000/auth/callback"
                ],
                "scopes": [
                    "openid",
                    "email",
                    "profile"
                ]
            }
        }
        return config
    
    def update_secret(self, secret_name: str, data: dict) -> bool:
        """Update secret in Secret Manager"""
        try:
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}"
            payload = json.dumps(data).encode("utf-8")
            
            # Check if secret exists
            try:
                self.client.get_secret(name=secret_path)
                # Update existing secret
                self.client.add_secret_version(
                    name=secret_path,
                    payload={"data": payload}
                )
            except Exception:
                # Create new secret
                self.client.create_secret(
                    parent=f"projects/{self.project_id}",
                    secret_id=secret_name,
                    secret={"replication": {"automatic": {}}}
                )
                self.client.add_secret_version(
                    name=secret_path,
                    payload={"data": payload}
                )
            
            print(f"✓ Updated secret: {secret_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to update secret {secret_name}: {e}")
            return False
    
    def generate_k8s_manifest(self, config: dict) -> str:
        """Generate Kubernetes manifest for OAuth configuration"""
        manifest = f"""apiVersion: v1
kind: Secret
metadata:
  name: oauth-secrets
  namespace: indestructibleeco
type: Opaque
stringData:
  ECO_OAUTH_CLIENT_ID: {config['oauth']['client_id']}
  ECO_OAUTH_CLIENT_SECRET: {config['oauth']['client_secret']}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: oauth-config
  namespace: indestructibleeco
data:
  oauth-config.json: |
    {json.dumps(config, indent=2)}
"""
        return manifest
    
    def save_manifest(self, manifest: str, output_path: str) -> bool:
        """Save Kubernetes manifest to file"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(manifest)
            print(f"✓ Saved manifest: {output_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to save manifest: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Setup OAuth 2.0 configuration for IndestructibleEco'
    )
    parser.add_argument(
        '--environment',
        choices=['staging', 'production'],
        required=True,
        help='Target environment'
    )
    parser.add_argument(
        '--action',
        choices=['create-client', 'update-secrets', 'verify-config'],
        required=True,
        help='Action to perform'
    )
    parser.add_argument(
        '--project-id',
        default=os.getenv('GCP_PROJECT', 'my-project-ops-1991'),
        help='GCP project ID'
    )
    parser.add_argument(
        '--client-id',
        default=os.getenv('ECO_OAUTH_CLIENT_ID', ''),
        help='OAuth client ID'
    )
    parser.add_argument(
        '--client-secret',
        default=os.getenv('ECO_OAUTH_CLIENT_SECRET', ''),
        help='OAuth client secret'
    )
    parser.add_argument(
        '--output-dir',
        default='k8s',
        help='Output directory for manifests'
    )
    
    args = parser.parse_args()
    
    # Initialize OAuth setup
    oauth_setup = OAuthSetup(args.project_id, args.environment)
    
    if args.action == 'create-client':
        print("Creating OAuth client configuration...")
        if not args.client_id or not args.client_secret:
            print("Error: ECO_OAUTH_CLIENT_ID and ECO_OAUTH_CLIENT_SECRET must be provided")
            print("Set them as environment variables or pass as arguments")
            sys.exit(1)
        
        config = oauth_setup.create_oauth_config(args.client_id, args.client_secret)
        
        # Update secrets
        secret_name = f"oauth-{args.environment}-config"
        oauth_setup.update_secret(secret_name, config)
        
        # Generate and save manifest
        manifest = oauth_setup.generate_k8s_manifest(config)
        output_path = f"{args.output_dir}/{args.environment}/oauth-config.qyaml"
        oauth_setup.save_manifest(manifest, output_path)
        
        print(f"\n✓ OAuth configuration created for {args.environment}")
        print(f"  Manifest: {output_path}")
        print(f"  Secret: {secret_name}")
    
    elif args.action == 'update-secrets':
        print("Updating OAuth secrets...")
        if not args.client_id or not args.client_secret:
            print("Error: ECO_OAUTH_CLIENT_ID and ECO_OAUTH_CLIENT_SECRET must be provided")
            sys.exit(1)
        
        config = oauth_setup.create_oauth_config(args.client_id, args.client_secret)
        secret_name = f"oauth-{args.environment}-config"
        oauth_setup.update_secret(secret_name, config)
        
        print(f"\n✓ OAuth secrets updated for {args.environment}")
    
    elif args.action == 'verify-config':
        print("Verifying OAuth configuration...")
        secret_name = f"oauth-{args.environment}-config"
        secret_path = f"projects/{args.project_id}/secrets/{secret_name}"
        
        try:
            response = oauth_setup.client.access_secret_version(name=f"{secret_path}/versions/latest")
            config = json.loads(response.payload.data.decode("utf-8"))
            print(f"\n✓ OAuth configuration verified for {args.environment}")
            print(f"  Client ID: {config['oauth']['client_id']}")
            print(f"  Redirect URIs: {', '.join(config['oauth']['redirect_uris'])}")
        except Exception as e:
            print(f"✗ Failed to verify configuration: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()