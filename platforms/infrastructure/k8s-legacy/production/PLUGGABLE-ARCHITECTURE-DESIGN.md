<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Pluggable Architecture Design
## Universal Deployment for Any Environment

---

## Executive Summary

This document defines a **pluggable, modular architecture** that enables deployment across any environment without modification. The system supports:
- **Cloud Providers**: AWS, GCP, Azure, DigitalOcean, Linode, OVH
- **Container Platforms**: Kubernetes, Docker Compose, Nomad, ECS, ACI, GKE Autopilot
- **Infrastructure**: On-premise, Bare Metal, Edge Computing, IoT
- **Database Services**: Managed (RDS, Cloud SQL, Azure SQL) or Self-hosted
- **Storage Backends**: Object Storage, Block Storage, Network File Systems

---

## 1. Architecture Principles

### 1.1 Core Design Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Provider Agnostic** | No hard dependency on any cloud provider | Abstraction layers, interface-based design |
| **Configuration Driven** | All provider differences in configuration files | YAML/JSON configurations, no code changes |
| **Environment Isolation** | Each environment fully independent | Separate config sets, overlay patterns |
| **Progressive Enhancement** | Works with basic config, enhanced with optional features | Feature flags, optional modules |
| **Zero Trust Security** | Security by default, provider-neutral | Mutual TLS, RBAC, secrets management |

### 1.2 Pluggable Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Business Logic, API Services, Workers, Monitoring)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Pluggable Adapters Layer                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │
│  │ Cloud      │ │ Database   │ │ Storage    │ │ Messaging │ │
│  │ Provider   │ │ Adapter    │ │ Adapter    │ │ Adapter   │ │
│  │ Interface  │ │            │ │            │ │           │ │
│  └────────────┘ └────────────┘ └────────────┘ └───────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │
│  │ Monitoring │ │ Security   │ │ Identity   │ │ Cache     │ │
│  │ Provider   │ │ Provider   │ │ Provider   │ │ Adapter   │ │
│  └────────────┘ └────────────┘ └────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Provider Implementations                    │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌─────────┐     │
│  │ AWS   │ │  GCP  │ │ Azure │ │ Digital│ │ On-Prem │     │
│  │       │ │       │ │       │ │ Ocean  │ │         │     │
│  └───────┘ └───────┘ └───────┘ └───────┘ └─────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Provider Abstraction Layer

### 2.1 Interface Definitions

#### Cloud Provider Interface
```python
class CloudProvider:
    """Abstract interface for all cloud providers"""
    
    async def deploy_infrastructure(self, config: dict) -> DeploymentResult:
        """Deploy infrastructure resources"""
        pass
    
    async def get_resource(self, resource_id: str) -> Resource:
        """Get resource details"""
        pass
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete resource"""
        pass
    
    async def get_metrics(self, resource_id: str) -> Metrics:
        """Get resource metrics"""
        pass
```

#### Database Provider Interface
```python
class DatabaseProvider:
    """Abstract interface for database providers"""
    
    async def create_database(self, config: DatabaseConfig) -> Database:
        """Create database instance"""
        pass
    
    async def execute_query(self, query: str) -> QueryResult:
        """Execute query"""
        pass
    
    async def backup_database(self) -> BackupResult:
        """Backup database"""
        pass
```

#### Storage Provider Interface
```python
class StorageProvider:
    """Abstract interface for storage providers"""
    
    async def upload_file(self, path: str, data: bytes) -> FileMetadata:
        """Upload file"""
        pass
    
    async def download_file(self, path: str) -> bytes:
        """Download file"""
        pass
    
    async def list_files(self, prefix: str) -> List[FileMetadata]:
        """List files"""
        pass
```

### 2.2 Provider Registry

```python
class ProviderRegistry:
    """Central registry for all providers"""
    
    def __init__(self):
        self.providers = {
            'cloud': {},
            'database': {},
            'storage': {},
            'monitoring': {},
            'security': {},
            'identity': {},
            'cache': {}
        }
    
    def register_provider(self, category: str, name: str, provider: Any):
        """Register a provider"""
        self.providers[category][name] = provider
    
    def get_provider(self, category: str, name: str) -> Any:
        """Get provider instance"""
        return self.providers[category].get(name)
```

---

## 3. Configuration Architecture

### 3.1 Configuration Hierarchy

```
config/
├── base/                          # Base configuration (provider-agnostic)
│   ├── application.yaml           # Application settings
│   ├── services.yaml              # Service definitions
│   ├── monitoring.yaml            # Monitoring configuration
│   └── security.yaml              # Security policies
│
├── providers/                     # Provider-specific configurations
│   ├── aws/                       # AWS configurations
│   │   ├── infrastructure.yaml    # AWS resources
│   │   ├── databases.yaml         # AWS RDS configurations
│   │   ├── storage.yaml           # AWS S3 configurations
│   │   └── monitoring.yaml        # AWS CloudWatch
│   │
│   ├── gcp/                       # GCP configurations
│   │   ├── infrastructure.yaml    # GCP resources
│   │   ├── databases.yaml         # Cloud SQL configurations
│   │   ├── storage.yaml           # GCS configurations
│   │   └── monitoring.yaml        # Cloud Monitoring
│   │
│   ├── azure/                     # Azure configurations
│   │   ├── infrastructure.yaml    # Azure resources
│   │   ├── databases.yaml         # Azure SQL configurations
│   │   ├── storage.yaml           # Azure Blob configurations
│   │   └── monitoring.yaml        # Azure Monitor
│   │
│   └── on-premise/                # On-premise configurations
│       ├── infrastructure.yaml    # Bare metal configurations
│       ├── databases.yaml         # Self-hosted databases
│       ├── storage.yaml           # Local storage configurations
│       └── monitoring.yaml        # Prometheus/Grafana
│
└── environments/                  # Environment-specific overlays
    ├── development/               # Development environment
    │   ├── config.yaml            # Development config
    │   └── overrides.yaml         # Development overrides
    │
    ├── staging/                   # Staging environment
    │   ├── config.yaml            # Staging config
    │   └── overrides.yaml         # Staging overrides
    │
    └── production/                # Production environment
        ├── config.yaml            # Production config
        └── overrides.yaml         # Production overrides
```

### 3.2 Configuration Merging Strategy

```yaml
# Example: Configuration merging for production on AWS
# Final config = base + providers/aws + environments/production + overrides

# config/base/application.yaml
application:
  name: machine-native-ops
  version: "1.0.0"
  replicas: 3
  
# config/providers/aws/infrastructure.yaml
infrastructure:
  provider: aws
  region: us-east-1
  vpc_cidr: 10.0.0.0/16
  
# config/environments/production/config.yaml
environment: production
replicas: 9
  
# config/environments/production/overrides.yaml
application:
  replicas: 15  # Override base config
  resources:
    requests:
      cpu: "1000m"
      memory: "2Gi"
```

### 3.3 Universal Configuration Schema

```yaml
# config/universal-config-schema.yaml
# Schema for all deployment configurations

schema:
  version: "1.0"
  
  provider:
    type: string
    enum: [aws, gcp, azure, digitalocean, linode, on-premise, kubernetes, docker-compose]
    required: true
    
  infrastructure:
    type: object
    properties:
      vpc:
        type: object
        properties:
          cidr:
            type: string
            pattern: ^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$
          subnets:
            type: array
            items:
              type: object
              properties:
                name:
                  type: string
                cidr:
                  type: string
                availability_zone:
                  type: string
      kubernetes:
        type: object
        properties:
          version:
            type: string
          node_pools:
            type: array
            items:
              type: object
              properties:
                name:
                  type: string
                instance_type:
                  type: string
                count:
                  type: integer
  
  database:
    type: object
    properties:
      type:
        type: string
        enum: [postgresql, mysql, mongodb, redis, elasticsearch]
      engine:
        type: string
      version:
        type: string
      instance_class:
        type: string
      storage:
        type: object
        properties:
          size:
            type: integer
            unit: GB
          encrypted:
            type: boolean
            default: true
  
  storage:
    type: object
    properties:
      type:
        type: string
        enum: [s3, gcs, azure-blob, minio, local]
      buckets:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            region:
              type: string
            versioning:
              type: boolean
            lifecycle:
              type: object
  
  monitoring:
    type: object
    properties:
      enabled:
        type: boolean
        default: true
      providers:
        type: array
        items:
          type: string
          enum: [prometheus, cloudwatch, cloud-monitoring, azure-monitor]
      retention:
        type: integer
        unit: days
  
  security:
    type: object
    properties:
      encryption:
        type: object
        properties:
          at_rest:
            type: boolean
            default: true
          in_transit:
            type: boolean
            default: true
      mTLS:
        type: boolean
        default: true
      rbac:
        type: boolean
        default: true
      secrets:
        type: object
        properties:
          provider:
            type: string
            enum: [aws-secrets-manager, azure-key-vault, gcp-secret-manager, vault, kubernetes-secrets]
```

---

## 4. Deployment Adapter Pattern

### 4.1 Adapter Factory

```python
class AdapterFactory:
    """Factory for creating provider adapters"""
    
    @staticmethod
    def create_cloud_adapter(provider: str, config: dict) -> CloudProvider:
        """Create cloud provider adapter"""
        adapters = {
            'aws': AWSAdapter,
            'gcp': GCPAdapter,
            'azure': AzureAdapter,
            'digitalocean': DigitalOceanAdapter,
            'on-premise': OnPremiseAdapter,
            'kubernetes': KubernetesAdapter,
            'docker-compose': DockerComposeAdapter
        }
        
        adapter_class = adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider}")
        
        return adapter_class(config)
    
    @staticmethod
    def create_database_adapter(provider: str, config: dict) -> DatabaseProvider:
        """Create database provider adapter"""
        adapters = {
            'aws-rds': AWSRDSAdapter,
            'gcp-cloud-sql': GCPCloudSQLAdapter,
            'azure-sql': AzureSQLAdapter,
            'postgresql': PostgreSQLAdapter,
            'mysql': MySQLAdapter,
            'mongodb': MongoDBAdapter,
            'redis': RedisAdapter
        }
        
        adapter_class = adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown database provider: {provider}")
        
        return adapter_class(config)
    
    @staticmethod
    def create_storage_adapter(provider: str, config: dict) -> StorageProvider:
        """Create storage provider adapter"""
        adapters = {
            'aws-s3': AWSS3Adapter,
            'gcp-gcs': GCPGCSAdapter,
            'azure-blob': AzureBlobAdapter,
            'minio': MinIOAdapter,
            'local': LocalStorageAdapter
        }
        
        adapter_class = adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown storage provider: {provider}")
        
        return adapter_class(config)
```

### 4.2 Provider Adapter Implementation Example

```python
class AWSAdapter(CloudProvider):
    """AWS provider adapter implementation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.ec2_client = boto3.client('ec2', region_name=config.get('region'))
        self.eks_client = boto3.client('eks', region_name=config.get('region'))
        self.rds_client = boto3.client('rds', region_name=config.get('region'))
        self.s3_client = boto3.client('s3', region_name=config.get('region'))
    
    async def deploy_infrastructure(self, config: dict) -> DeploymentResult:
        """Deploy AWS infrastructure"""
        # Create VPC
        vpc = await self._create_vpc(config['vpc'])
        
        # Create EKS cluster
        cluster = await self._create_eks_cluster(config['kubernetes'])
        
        # Create RDS instances
        databases = []
        for db_config in config.get('databases', []):
            db = await self._create_rds_instance(db_config)
            databases.append(db)
        
        # Create S3 buckets
        storage = []
        for storage_config in config.get('storage', []):
            bucket = await self._create_s3_bucket(storage_config)
            storage.append(bucket)
        
        return DeploymentResult(
            vpc_id=vpc.id,
            cluster_id=cluster.id,
            databases=databases,
            storage=storage
        )
    
    async def _create_vpc(self, vpc_config: dict) -> VPC:
        """Create VPC"""
        response = self.ec2_client.create_vpc(
            CidrBlock=vpc_config['cidr']
        )
        vpc = response['Vpc']
        
        # Enable DNS support
        self.ec2_client.modify_vpc_attribute(
            VpcId=vpc['VpcId'],
            EnableDnsSupport={'Value': True}
        )
        
        return VPC(id=vpc['VpcId'], cidr=vpc_config['cidr'])
    
    async def _create_eks_cluster(self, k8s_config: dict) -> Cluster:
        """Create EKS cluster"""
        response = self.eks_client.create_cluster(
            name=k8s_config['name'],
            roleArn=k8s_config['role_arn'],
            resourcesVpcConfig={
                'subnetIds': k8s_config['subnet_ids']
            },
            version=k8s_config['version']
        )
        
        return Cluster(id=response['cluster']['name'], version=k8s_config['version'])
```

---

## 5. Universal Deployment Manager

### 5.1 Deployment Manager

```python
class UniversalDeploymentManager:
    """Universal deployment manager for any environment"""
    
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get('provider')
        
        # Create adapters
        self.cloud_adapter = AdapterFactory.create_cloud_adapter(
            self.provider,
            config.get('cloud', {})
        )
        self.database_adapter = AdapterFactory.create_database_adapter(
            config.get('database_provider'),
            config.get('database', {})
        )
        self.storage_adapter = AdapterFactory.create_storage_adapter(
            config.get('storage_provider'),
            config.get('storage', {})
        )
    
    async def deploy(self) -> DeploymentResult:
        """Deploy to any environment"""
        logger.info(f"Deploying to provider: {self.provider}")
        
        # Deploy cloud infrastructure
        infrastructure = await self.cloud_adapter.deploy_infrastructure(
            self.config.get('infrastructure', {})
        )
        
        # Deploy databases
        databases = []
        for db_config in self.config.get('databases', []):
            db = await self.database_adapter.create_database(db_config)
            databases.append(db)
        
        # Deploy storage
        storage = []
        for storage_config in self.config.get('storage', []):
            await self.storage_adapter.create_bucket(storage_config)
        
        # Deploy applications
        applications = await self._deploy_applications()
        
        # Deploy monitoring
        await self._deploy_monitoring()
        
        return DeploymentResult(
            infrastructure=infrastructure,
            databases=databases,
            storage=storage,
            applications=applications
        )
    
    async def _deploy_applications(self) -> List[Application]:
        """Deploy applications"""
        applications = []
        
        for app_config in self.config.get('applications', []):
            app = await self.cloud_adapter.deploy_application(app_config)
            applications.append(app)
        
        return applications
```

---

## 6. Environment Detection and Auto-Configuration

### 6.1 Environment Detector

```python
class EnvironmentDetector:
    """Detect current deployment environment"""
    
    @staticmethod
    def detect() -> EnvironmentInfo:
        """Detect environment"""
        # Check for Kubernetes
        if EnvironmentDetector._is_kubernetes():
            return EnvironmentInfo(
                type='kubernetes',
                provider=EnvironmentDetector._detect_kubernetes_provider(),
                version=EnvironmentDetector._get_kubernetes_version()
            )
        
        # Check for Docker
        if EnvironmentDetector._is_docker():
            return EnvironmentInfo(
                type='docker-compose',
                provider='local'
            )
        
        # Check for cloud providers
        aws_metadata = EnvironmentDetector._check_aws_metadata()
        if aws_metadata:
            return EnvironmentInfo(
                type='aws',
                provider='aws',
                region=aws_metadata['region']
            )
        
        gcp_metadata = EnvironmentDetector._check_gcp_metadata()
        if gcp_metadata:
            return EnvironmentInfo(
                type='gcp',
                provider='gcp',
                zone=gcp_metadata['zone']
            )
        
        azure_metadata = EnvironmentDetector._check_azure_metadata()
        if azure_metadata:
            return EnvironmentInfo(
                type='azure',
                provider='azure',
                location=azure_metadata['location']
            )
        
        # Default to on-premise
        return EnvironmentInfo(
            type='on-premise',
            provider='bare-metal'
        )
    
    @staticmethod
    def _is_kubernetes() -> bool:
        """Check if running in Kubernetes"""
        try:
            with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
                return True
        except FileNotFoundError:
            return False
    
    @staticmethod
    def _is_docker() -> bool:
        """Check if running in Docker"""
        return os.path.exists('/.dockerenv')
    
    @staticmethod
    def _check_aws_metadata() -> Optional[dict]:
        """Check AWS metadata"""
        try:
            response = requests.get(
                '[EXTERNAL_URL_REMOVED]
                timeout=1
            )
            if response.status_code == 200:
                # Get region
                region_response = requests.get(
                    '[EXTERNAL_URL_REMOVED]
                    timeout=1
                )
                return {
                    'region': region_response.text
                }
        except:
            return None
```

### 6.2 Auto-Configuration Loader

```python
class AutoConfigurationLoader:
    """Load configuration based on detected environment"""
    
    def __init__(self):
        self.detector = EnvironmentDetector()
        self.environment_info = self.detector.detect()
    
    def load_config(self, environment: str = 'production') -> dict:
        """Load configuration for detected environment"""
        logger.info(f"Detected environment: {self.environment_info.type}")
        
        # Load base configuration
        config = self._load_yaml('config/base/application.yaml')
        
        # Load provider configuration
        provider_config = self._load_yaml(
            f'config/providers/{self.environment_info.type}/infrastructure.yaml'
        )
        config.update(provider_config)
        
        # Load environment configuration
        env_config = self._load_yaml(
            f'config/environments/{environment}/config.yaml'
        )
        config.update(env_config)
        
        return config
    
    def _load_yaml(self, path: str) -> dict:
        """Load YAML configuration file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
```

---

## 7. Deployment Scripts

### 7.1 Universal Deploy Command

```bash
#!/bin/bash
# scripts/deploy-universal.sh

set -e

# Parse arguments
PROVIDER="${1:-kubernetes}"
ENVIRONMENT="${2:-production}"
CONFIG_FILE="${3:-config/deployment-config.yaml}"

echo "=========================================="
echo "Universal Deployment Manager"
echo "=========================================="
echo "Provider: $PROVIDER"
echo "Environment: $ENVIRONMENT"
echo "Config: $CONFIG_FILE"
echo "=========================================="

# Detect environment if not specified
if [ "$PROVIDER" == "auto" ]; then
    echo "Detecting environment..."
    PROVIDER=$(python3 -c "from scripts.env_detector import detect_environment; print(detect_environment())")
    echo "Detected provider: $PROVIDER"
fi

# Load configuration
echo "Loading configuration..."
python3 scripts/load_config.py --provider $PROVIDER --environment $ENVIRONMENT --config $CONFIG_FILE

# Deploy infrastructure
echo "Deploying infrastructure..."
python3 scripts/deploy_infrastructure.py --provider $PROVIDER --config $CONFIG_FILE

# Deploy databases
echo "Deploying databases..."
python3 scripts/deploy_databases.py --provider $PROVIDER --config $CONFIG_FILE

# Deploy storage
echo "Deploying storage..."
python3 scripts/deploy_storage.py --provider $PROVIDER --config $CONFIG_FILE

# Deploy applications
echo "Deploying applications..."
python3 scripts/deploy_applications.py --provider $PROVIDER --config $CONFIG_FILE

# Deploy monitoring
echo "Deploying monitoring..."
python3 scripts/deploy_monitoring.py --provider $PROVIDER --config $CONFIG_FILE

# Verify deployment
echo "Verifying deployment..."
python3 scripts/verify_deployment.py --config $CONFIG_FILE

echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
```

### 7.2 Provider-Specific Deployment Scripts

#### AWS Deployment
```bash
#!/bin/bash
# scripts/deploy-aws.sh

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_PROFILE="${AWS_PROFILE:-default}"

# Deploy AWS infrastructure
aws cloudformation deploy \
  --template-file infrastructure/aws/cloudformation.yaml \
  --stack-name machine-native-ops-${ENVIRONMENT} \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    Region=$AWS_REGION

# Deploy EKS cluster
eksctl create cluster \
  --name machine-native-ops-${ENVIRONMENT} \
  --region $AWS_REGION \
  --config-file infrastructure/aws/eks-cluster.yaml

# Deploy applications to EKS
kubectl apply -f k8s/production/deployment.yaml
```

#### GCP Deployment
```bash
#!/bin/bash
# scripts/deploy-gcp.sh

export GCP_PROJECT="${GCP_PROJECT:-your-project-id}"
export GCP_ZONE="${GCP_ZONE:-us-central1-a}"

# Deploy GCP infrastructure
gcloud deployment-manager deployments create machine-native-ops-${ENVIRONMENT} \
  --config infrastructure/gcp/deployment.yaml

# Deploy GKE cluster
gcloud container clusters create machine-native-ops-${ENVIRONMENT} \
  --zone $GCP_ZONE \
  --project $GCP_PROJECT \
  --num-nodes 3

# Deploy applications to GKE
kubectl apply -f k8s/production/deployment.yaml
```

#### Azure Deployment
```bash
#!/bin/bash
# scripts/deploy-azure.sh

export AZURE_RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-machine-native-ops}"
export AZURE_LOCATION="${AZURE_LOCATION:-eastus}"

# Create resource group
az group create \
  --name $AZURE_RESOURCE_GROUP \
  --location $AZURE_LOCATION

# Deploy Azure infrastructure
az deployment group create \
  --resource-group $AZURE_RESOURCE_GROUP \
  --template-file infrastructure/azure/main.bicep \
  --parameters environment=$ENVIRONMENT

# Deploy AKS cluster
az aks create \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name machine-native-ops-${ENVIRONMENT} \
  --node-count 3 \
  --generate-ssh-keys

# Deploy applications to AKS
kubectl apply -f k8s/production/deployment.yaml
```

#### On-Premise Deployment
```bash
#!/bin/bash
# scripts/deploy-on-premise.sh

# Deploy to local Kubernetes cluster
kubectl apply -f k8s/production/deployment.yaml

# Or deploy with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Deploy monitoring stack
helm install monitoring charts/prometheus-stack
```

---

## 8. Configuration Templates

### 8.1 AWS Configuration Template

```yaml
# config/providers/aws/production-config.yaml

provider:
  type: aws
  region: us-east-1
  
infrastructure:
  vpc:
    cidr: 10.0.0.0/16
    enable_dns_support: true
    enable_dns_hostnames: true
    subnets:
      - name: public-subnet-1
        cidr: 10.0.1.0/24
        availability_zone: us-east-1a
        type: public
      - name: private-subnet-1
        cidr: 10.0.2.0/24
        availability_zone: us-east-1a
        type: private
  
  kubernetes:
    type: eks
    name: machine-native-ops
    version: "1.28"
    node_pools:
      - name: general-purpose
        instance_type: t3.medium
        min_nodes: 3
        max_nodes: 10
        desired_nodes: 3
      - name: memory-optimized
        instance_type: r5.large
        min_nodes: 1
        max_nodes: 5
        desired_nodes: 1
  
  database:
    type: rds
    instances:
      - name: main-db
        engine: postgresql
        engine_version: "15.4"
        instance_class: db.t3.medium
        storage: 100
        storage_type: gp3
        multi_az: true
        backup_retention: 30
        parameter_group: default.postgres15
  
  storage:
    type: s3
    buckets:
      - name: machine-native-ops-data
        versioning: true
        lifecycle:
          rules:
            - id: archive-old-objects
              status: enabled
              transitions:
                - days: 30
                  storage_class: GLACIER
            - id: delete-old-objects
              status: enabled
              expiration:
                days: 365
  
  monitoring:
    enabled: true
    cloudwatch:
      logs:
        retention_days: 30
      metrics:
        namespace: MachineNativeOps
      alarms:
        - name: HighErrorRate
          metric: ErrorRate
          threshold: 5
          comparison: GreaterThanThreshold
  
  security:
    encryption:
      at_rest: true
      in_transit: true
    secrets:
      provider: aws-secrets-manager
    rbac:
      enabled: true
    network:
      security_groups:
        - name: web-server
          rules:
            - type: ingress
              protocol: tcp
              port: 443
              source: 0.0.0.0/0
```

### 8.2 GCP Configuration Template

```yaml
# config/providers/gcp/production-config.yaml

provider:
  type: gcp
  project: your-gcp-project-id
  region: us-central1
  zone: us-central1-a
  
infrastructure:
  vpc:
    name: machine-native-ops-vpc
    auto_create_subnetworks: false
    subnets:
      - name: subnet-1
        region: us-central1
        ip_cidr_range: 10.0.1.0/24
        private: false
      - name: subnet-2
        region: us-central1
        ip_cidr_range: 10.0.2.0/24
        private: true
  
  kubernetes:
    type: gke
    name: machine-native-ops
    version: "1.28"
    node_pools:
      - name: general-purpose
        machine_type: e2-medium
        node_count: 3
        autoscaling:
          min_nodes: 3
          max_nodes: 10
  
  database:
    type: cloud-sql
    instances:
      - name: main-db
        engine: postgresql
        engine_version: POSTGRES_15
        tier: db-f1-micro
        storage_gb: 100
        availability_type: REGIONAL
        backup_retention_days: 30
  
  storage:
    type: gcs
    buckets:
      - name: machine-native-ops-data
        location: us-central1
        storage_class: STANDARD
        versioning:
          enabled: true
        lifecycle:
          rules:
            - action:
                type: SetStorageClass
                storage_class: NEARLINE
              condition:
                age: 30
            - action:
                type: Delete
              condition:
                age: 365
  
  monitoring:
    enabled: true
    cloud-monitoring:
      metrics:
        project: your-gcp-project-id
      alerts:
        - name: HighErrorRate
          condition:
            filter: 'metric.type="custom.googleapis.com/error_rate"'
            threshold: 5
  
  security:
    encryption:
      at_rest: true
      in_transit: true
    secrets:
      provider: gcp-secret-manager
    rbac:
      enabled: true
    iam:
      roles:
        - role: roles/cloudsql.admin
          service_accounts:
            - service-account@project.iam.gserviceaccount.com
```

### 8.3 Azure Configuration Template

```yaml
# config/providers/azure/production-config.yaml

provider:
  type: azure
  resource_group: machine-native-ops-rg
  location: eastus
  
infrastructure:
  vpc:
    name: machine-native-ops-vnet
    address_space: 10.0.0.0/16
    subnets:
      - name: subnet-1
        address_prefix: 10.0.1.0/24
      - name: subnet-2
        address_prefix: 10.0.2.0/24
  
  kubernetes:
    type: aks
    name: machine-native-ops
    version: "1.28"
    node_pools:
      - name: general-purpose
        vm_size: Standard_DS2_v2
        node_count: 3
        enable_auto_scaling: true
        min_count: 3
        max_count: 10
  
  database:
    type: azure-sql
    instances:
      - name: main-db
        engine: sql
        version: "12.0"
        tier: GeneralPurpose
        sku_name: GP_Gen5_2
        storage_gb: 100
        geo_redundant_backup: true
  
  storage:
    type: azure-blob
    accounts:
      - name: machinenativeopsstorage
        sku: Standard_LRS
        kind: StorageV2
        containers:
          - name: data
            access_level: private
          - name: logs
            access_level: private
  
  monitoring:
    enabled: true
    azure-monitor:
      metrics:
        resource_id: /subscriptions/{subscription-id}/resourceGroups/{resource-group}
      alerts:
        - name: HighErrorRate
          condition:
            operator: GreaterThan
            threshold: 5
            time_aggregation: Average
  
  security:
    encryption:
      at_rest: true
      in_transit: true
    secrets:
      provider: azure-key-vault
    rbac:
      enabled: true
    network:
      security_groups:
        - name: web-server
          rules:
            - name: AllowHTTPS
              protocol: Tcp
              source_port_range: "*"
              destination_port_range: 443
              source_address_prefix: "*"
              access: Allow
```

### 8.4 On-Premise Configuration Template

```yaml
# config/providers/on-premise/production-config.yaml

provider:
  type: on-premise
  datacenter: main-datacenter
  
infrastructure:
  servers:
    - name: server-1
      ip: 10.0.1.10
      role: kubernetes-control-plane
      cpu_cores: 8
      memory_gb: 32
      disk_gb: 500
    - name: server-2
      ip: 10.0.1.11
      role: kubernetes-worker
      cpu_cores: 16
      memory_gb: 64
      disk_gb: 1000
    - name: server-3
      ip: 10.0.1.12
      role: database
      cpu_cores: 8
      memory_gb: 64
      disk_gb: 2000
  
  kubernetes:
    type: self-hosted
    version: "1.28"
    control_plane:
      replicas: 3
    workers:
      replicas: 3
  
  database:
    type: self-hosted
    instances:
      - name: main-db
        engine: postgresql
        engine_version: "15.4"
        cpu_cores: 4
        memory_gb: 16
        storage_gb: 500
        replication:
          enabled: true
          replicas: 2
        backup:
          enabled: true
          retention_days: 30
  
  storage:
    type: local
    volumes:
      - name: data
        path: /mnt/data
        size_gb: 1000
        type: ssd
      - name: logs
        path: /var/log
        size_gb: 100
        type: ssd
  
  monitoring:
    enabled: true
    prometheus:
      version: "2.48"
      retention_days: 30
    grafana:
      version: "10.2"
      dashboards:
        - name: application
        - name: infrastructure
        - name: database
  
  security:
    encryption:
      at_rest: true
      in_transit: true
    secrets:
      provider: vault
      vault_address: [EXTERNAL_URL_REMOVED]
      # NOTE: Production deployments MUST use properly configured TLS certificates
      # and enforce strict TLS verification for all Vault connections.
    rbac:
      enabled: true
    network:
      firewall:
        rules:
          - name: AllowHTTPS
            protocol: tcp
            port: 443
            source: 0.0.0.0/0
            action: accept
```

---

## 9. Provider Adapters Implementation

### 9.1 AWS Adapter Implementation

```python
# ns-root/namespaces-adk/adk/plugins/deployment/adapters/aws_adapter.py

import boto3
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AWSConfig:
    """AWS configuration"""
    region: str
    profile: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None


class AWSAdapter:
    """AWS cloud provider adapter"""
    
    def __init__(self, config: AWSConfig):
        self.config = config
        
        # Initialize AWS clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AWS clients"""
        session_kwargs = {}
        
        if self.config.profile:
            session_kwargs['profile_name'] = self.config.profile
        elif self.config.access_key and self.config.secret_key:
            session_kwargs['aws_access_key_id'] = self.config.access_key
            session_kwargs['aws_secret_access_key'] = self.config.secret_key
        
        session = boto3.Session(**session_kwargs, region_name=self.config.region)
        
        self.ec2 = session.client('ec2')
        self.eks = session.client('eks')
        self.rds = session.client('rds')
        self.s3 = session.client('s3')
        self.elb = session.client('elbv2')
        self.iam = session.client('iam')
        self.route53 = session.client('route53')
        self.cloudwatch = session.client('cloudwatch')
        self.secrets_manager = session.client('secretsmanager')
    
    async def deploy_infrastructure(self, infra_config: dict) -> dict:
        """Deploy infrastructure"""
        logger.info(f"Deploying AWS infrastructure in {self.config.region}")
        
        # Deploy VPC
        vpc = await self.deploy_vpc(infra_config.get('vpc', {}))
        
        # Deploy EKS cluster
        cluster = await self.deploy_eks_cluster(infra_config.get('kubernetes', {}))
        
        # Deploy databases
        databases = []
        for db_config in infra_config.get('database', {}).get('instances', []):
            db = await self.deploy_rds_instance(db_config)
            databases.append(db)
        
        # Deploy storage
        storage = []
        for storage_config in infra_config.get('storage', {}).get('buckets', []):
            bucket = await self.deploy_s3_bucket(storage_config)
            storage.append(bucket)
        
        return {
            'vpc': vpc,
            'cluster': cluster,
            'databases': databases,
            'storage': storage
        }
    
    async def deploy_vpc(self, vpc_config: dict) -> dict:
        """Deploy VPC"""
        logger.info("Deploying VPC")
        
        # Create VPC
        vpc_response = self.ec2.create_vpc(
            CidrBlock=vpc_config.get('cidr', '10.0.0.0/16'),
            AmazonProvidedIPv6CidrBlock=vpc_config.get('enable_ipv6', False)
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        
        # Enable DNS support
        self.ec2.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsSupport={'Value': vpc_config.get('enable_dns_support', True)}
        )
        
        self.ec2.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsHostnames={'Value': vpc_config.get('enable_dns_hostnames', True)}
        )
        
        # Create subnets
        subnets = []
        for subnet_config in vpc_config.get('subnets', []):
            subnet = await self._create_subnet(vpc_id, subnet_config)
            subnets.append(subnet)
        
        # Create internet gateway
        igw_response = self.ec2.create_internet_gateway()
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        self.ec2.attach_internet_gateway(
            InternetGatewayId=igw_id,
            VpcId=vpc_id
        )
        
        # Create route tables
        await self._create_route_tables(vpc_id, subnets, igw_id)
        
        # Create security groups
        security_groups = []
        for sg_config in vpc_config.get('security_groups', []):
            sg = await self._create_security_group(vpc_id, sg_config)
            security_groups.append(sg)
        
        return {
            'vpc_id': vpc_id,
            'subnets': subnets,
            'internet_gateway': igw_id,
            'security_groups': security_groups
        }
    
    async def _create_subnet(self, vpc_id: str, subnet_config: dict) -> dict:
        """Create subnet"""
        response = self.ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=subnet_config['cidr'],
            AvailabilityZone=subnet_config.get('availability_zone'),
            MapPublicIpOnLaunch=(subnet_config.get('type') == 'public')
        )
        
        subnet_id = response['Subnet']['SubnetId']
        
        # Tag subnet
        self.ec2.create_tags(
            Resources=[subnet_id],
            Tags=[{'Key': 'Name', 'Value': subnet_config['name']}]
        )
        
        return {
            'subnet_id': subnet_id,
            'name': subnet_config['name'],
            'cidr': subnet_config['cidr']
        }
    
    async def _create_route_tables(self, vpc_id: str, subnets: List[dict], igw_id: str):
        """Create route tables"""
        # Create main route table
        route_table_response = self.ec2.create_route_table(VpcId=vpc_id)
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        
        # Add route to internet gateway for public subnets
        for subnet in subnets:
            if subnet.get('type') == 'public':
                self.ec2.create_route(
                    RouteTableId=route_table_id,
                    DestinationCidrBlock='0.0.0.0/0',
                    GatewayId=igw_id
                )
        
        # Associate route tables with subnets
        for subnet in subnets:
            self.ec2.associate_route_table(
                RouteTableId=route_table_id,
                SubnetId=subnet['subnet_id']
            )
    
    async def _create_security_group(self, vpc_id: str, sg_config: dict) -> dict:
        """Create security group"""
        response = self.ec2.create_security_group(
            GroupName=sg_config['name'],
            Description=sg_config.get('description', ''),
            VpcId=vpc_id
        )
        
        sg_id = response['GroupId']
        
        # Add ingress rules
        for rule in sg_config.get('rules', []):
            if rule.get('type') == 'ingress':
                self.ec2.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpProtocol=rule['protocol'],
                    FromPort=rule['port'],
                    ToPort=rule['port'],
                    CidrIp=rule['source']
                )
        
        # Add egress rules
        for rule in sg_config.get('rules', []):
            if rule.get('type') == 'egress':
                self.ec2.authorize_security_group_egress(
                    GroupId=sg_id,
                    IpProtocol=rule['protocol'],
                    FromPort=rule['port'],
                    ToPort=rule['port'],
                    CidrIp=rule['destination']
                )
        
        return {
            'security_group_id': sg_id,
            'name': sg_config['name']
        }
    
    async def deploy_eks_cluster(self, k8s_config: dict) -> dict:
        """Deploy EKS cluster"""
        logger.info(f"Deploying EKS cluster: {k8s_config.get('name')}")
        
        # Create IAM role for EKS
        role_name = f"{k8s_config['name']}-cluster-role"
        role_arn = await self._create_eks_cluster_role(role_name)
        
        # Create EKS cluster
        response = self.eks.create_cluster(
            name=k8s_config['name'],
            roleArn=role_arn,
            resourcesVpcConfig={
                'subnetIds': [s['subnet_id'] for s in k8s_config.get('subnet_ids', [])],
                'securityGroupIds': k8s_config.get('security_group_ids', [])
            },
            version=k8s_config.get('version', '1.28')
        )
        
        cluster_name = response['cluster']['name']
        
        # Wait for cluster to be ready
        import time
        time.sleep(30)
        
        # Create node groups
        node_groups = []
        for node_pool in k8s_config.get('node_pools', []):
            ng = await self._create_node_group(cluster_name, node_pool)
            node_groups.append(ng)
        
        return {
            'cluster_name': cluster_name,
            'cluster_arn': response['cluster']['arn'],
            'endpoint': response['cluster']['endpoint'],
            'node_groups': node_groups
        }
    
    async def _create_eks_cluster_role(self, role_name: str) -> str:
        """Create IAM role for EKS cluster"""
        # Create trust policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "eks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create role
        response = self.iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        role_arn = response['Role']['Arn']
        
        # Attach policies
        self.iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy'
        )
        
        return role_arn
    
    async def _create_node_group(self, cluster_name: str, node_pool: dict) -> dict:
        """Create node group"""
        response = self.eks.create_nodegroup(
            clusterName=cluster_name,
            nodegroupName=node_pool['name'],
            scalingConfig={
                'minSize': node_pool.get('min_nodes', 1),
                'maxSize': node_pool.get('max_nodes', 5),
                'desiredSize': node_pool.get('desired_nodes', 1)
            },
            subnets=node_pool.get('subnet_ids', []),
            instanceTypes=[node_pool['instance_type']],
            nodeRole=node_pool['role_arn']
        )
        
        return {
            'nodegroup_name': node_pool['name'],
            'nodegroup_arn': response['nodegroup']['nodegroupArn']
        }
    
    async def deploy_rds_instance(self, db_config: dict) -> dict:
        """Deploy RDS instance"""
        logger.info(f"Deploying RDS instance: {db_config['name']}")
        
        response = self.rds.create_db_instance(
            DBInstanceIdentifier=db_config['name'],
            DBInstanceClass=db_config['instance_class'],
            Engine=db_config['engine'],
            EngineVersion=db_config.get('engine_version'),
            AllocatedStorage=db_config['storage'],
            StorageType=db_config.get('storage_type', 'gp2'),
            MasterUsername=db_config['leader_username'],
            MasterUserPassword=db_config['leader_password'],
            VpcSecurityGroupIds=db_config.get('security_group_ids', []),
            DBSubnetGroupName=db_config.get('subnet_group_name'),
            MultiAZ=db_config.get('multi_az', False),
            BackupRetentionPeriod=db_config.get('backup_retention', 7),
            StorageEncrypted=db_config.get('encryption', True),
            PubliclyAccessible=False
        )
        
        return {
            'db_instance_id': db_config['name'],
            'endpoint': response['DBInstance']['Endpoint']['Address'],
            'port': response['DBInstance']['Endpoint']['Port']
        }
    
    async def deploy_s3_bucket(self, bucket_config: dict) -> dict:
        """Deploy S3 bucket"""
        logger.info(f"Creating S3 bucket: {bucket_config['name']}")
        
        # Create bucket
        location = self.config.region
        bucket_args = {'Bucket': bucket_config['name']}
        
        if location != 'us-east-1':
            bucket_args['CreateBucketConfiguration'] = {
                'LocationConstraint': location
            }
        
        self.s3.create_bucket(**bucket_args)
        
        # Enable versioning
        if bucket_config.get('versioning', False):
            self.s3.put_bucket_versioning(
                Bucket=bucket_config['name'],
                VersioningConfiguration={
                    'Status': 'Enabled'
                }
            )
        
        # Set lifecycle configuration
        if bucket_config.get('lifecycle'):
            self.s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_config['name'],
                LifecycleConfiguration=bucket_config['lifecycle']
            )
        
        return {
            'bucket_name': bucket_config['name'],
            'region': location
        }
    
    async def get_cluster_credentials(self, cluster_name: str) -> dict:
        """Get EKS cluster credentials"""
        response = self.eks.get_cluster_credentials(
            clusterName=cluster_name
        )
        
        return {
            'token': response['token'],
            'certificate': response['certificate']
        }
```

### 9.2 GCP Adapter Implementation

```python
# ns-root/namespaces-adk/adk/plugins/deployment/adapters/gcp_adapter.py

from google.cloud import storage
from google.cloud import container_v1
from google.cloud import sql
from google.cloud import monitoring_v3
from google.oauth2 import service_account
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class GCPAdapter:
    """GCP cloud provider adapter"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Initialize GCP clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize GCP clients"""
        credentials = None
        if 'service_account_key' in self.config:
            credentials = service_account.Credentials.from_service_account_info(
                self.config['service_account_key']
            )
        
        self.storage_client = storage.Client(
            project=self.config.get('project'),
            credentials=credentials
        )
        self.gke_client = container_v1.ClusterManagerClient(
            credentials=credentials
        )
        self.sql_client = sql.SqlInstancesServiceClient(
            credentials=credentials
        )
        self.monitoring_client = monitoring_v3.MetricServiceClient(
            credentials=credentials
        )
    
    async def deploy_infrastructure(self, infra_config: dict) -> dict:
        """Deploy infrastructure"""
        logger.info(f"Deploying GCP infrastructure in {self.config.get('region')}")
        
        # Deploy VPC
        vpc = await self.deploy_vpc(infra_config.get('vpc', {}))
        
        # Deploy GKE cluster
        cluster = await self.deploy_gke_cluster(infra_config.get('kubernetes', {}))
        
        # Deploy databases
        databases = []
        for db_config in infra_config.get('database', {}).get('instances', []):
            db = await self.deploy_cloud_sql_instance(db_config)
            databases.append(db)
        
        # Deploy storage
        storage = []
        for storage_config in infra_config.get('storage', {}).get('buckets', []):
            bucket = await self.deploy_gcs_bucket(storage_config)
            storage.append(bucket)
        
        return {
            'vpc': vpc,
            'cluster': cluster,
            'databases': databases,
            'storage': storage
        }
    
    async def deploy_vpc(self, vpc_config: dict) -> dict:
        """Deploy VPC"""
        logger.info("Deploying VPC")
        
        # Use Compute Engine API to create VPC
        # Implementation depends on GCP Compute Engine client
        # This is a simplified example
        
        return {
            'vpc_name': vpc_config.get('name'),
            'region': self.config.get('region')
        }
    
    async def deploy_gke_cluster(self, k8s_config: dict) -> dict:
        """Deploy GKE cluster"""
        logger.info(f"Deploying GKE cluster: {k8s_config.get('name')}")
        
        project_id = self.config['project']
        zone = self.config.get('zone')
        
        # Create cluster
        cluster = {
            'name': k8s_config['name'],
            'initial_cluster_version': k8s_config.get('version', '1.28'),
            'node_pools': []
        }
        
        for node_pool in k8s_config.get('node_pools', []):
            node_pool_config = {
                'name': node_pool['name'],
                'initial_node_count': node_pool.get('node_count', 3),
                'config': {
                    'machine_type': node_pool.get('machine_type', 'e2-medium')
                },
                'autoscaling': {
                    'enabled': node_pool.get('enable_auto_scaling', False),
                    'min_node_count': node_pool.get('min_count', 1),
                    'max_node_count': node_pool.get('max_count', 5)
                }
            }
            cluster['node_pools'].append(node_pool_config)
        
        # Create cluster request
        request = {
            'parent': f'projects/{project_id}/locations/{zone}',
            'cluster': cluster
        }
        
        operation = self.gke_client.create_cluster(request)
        
        return {
            'cluster_name': k8s_config['name'],
            'operation': operation.operation.name
        }
    
    async def deploy_cloud_sql_instance(self, db_config: dict) -> dict:
        """Deploy Cloud SQL instance"""
        logger.info(f"Deploying Cloud SQL instance: {db_config['name']}")
        
        project_id = self.config['project']
        instance_id = db_config['name']
        
        # Create instance
        instance = {
            'name': instance_id,
            'database_version': db_config.get('engine_version', 'POSTGRES_15'),
            'region': self.config.get('region'),
            'settings': {
                'tier': db_config.get('tier', 'db-f1-micro'),
                'data_disk_size_gb': db_config.get('storage_gb', 100),
                'availability_type': db_config.get('availability_type', 'ZONAL'),
                'backup_configuration': {
                    'enabled': True,
                    'backup_retention_settings': {
                        'retention_days': db_config.get('backup_retention_days', 7)
                    }
                }
            }
        }
        
        request = {
            'parent': f'projects/{project_id}',
            'instance': instance
        }
        
        operation = self.sql_client.create_instance(request)
        
        return {
            'instance_id': instance_id,
            'operation': operation.operation.name
        }
    
    async def deploy_gcs_bucket(self, bucket_config: dict) -> dict:
        """Deploy GCS bucket"""
        logger.info(f"Creating GCS bucket: {bucket_config['name']}")
        
        bucket = self.storage_client.bucket(bucket_config['name'])
        bucket.storage_class = bucket_config.get('storage_class', 'STANDARD')
        bucket.location = bucket_config.get('location', 'US')
        
        bucket.create()
        
        # Enable versioning
        if bucket_config.get('versioning', {}).get('enabled', False):
            bucket.versioning_enabled = True
            bucket.patch()
        
        # Set lifecycle rules
        if bucket_config.get('lifecycle'):
            bucket.lifecycle_rules = bucket_config['lifecycle']
            bucket.patch()
        
        return {
            'bucket_name': bucket_config['name'],
            'location': bucket.location
        }
```

### 9.3 Azure Adapter Implementation

```python
# ns-root/namespaces-adk/adk/plugins/deployment/adapters/azure_adapter.py

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class AzureAdapter:
    """Azure cloud provider adapter"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Initialize Azure clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize Azure clients"""
        credential = DefaultAzureCredential()
        
        self.resource_client = ResourceManagementClient(
            credential,
            self.config.get('subscription_id')
        )
        self.container_client = ContainerServiceClient(
            credential,
            self.config.get('subscription_id')
        )
        self.sql_client = SqlManagementClient(
            credential,
            self.config.get('subscription_id')
        )
        self.storage_client = StorageManagementClient(
            credential,
            self.config.get('subscription_id')
        )
        self.monitor_client = MonitorManagementClient(
            credential,
            self.config.get('subscription_id')
        )
    
    async def deploy_infrastructure(self, infra_config: dict) -> dict:
        """Deploy infrastructure"""
        logger.info(f"Deploying Azure infrastructure in {self.config.get('location')}")
        
        # Deploy resource group
        rg = await self._create_resource_group()
        
        # Deploy VNet
        vnet = await self.deploy_vnet(infra_config.get('vpc', {}))
        
        # Deploy AKS cluster
        cluster = await self.deploy_aks_cluster(infra_config.get('kubernetes', {}))
        
        # Deploy databases
        databases = []
        for db_config in infra_config.get('database', {}).get('instances', []):
            db = await self.deploy_azure_sql_instance(db_config)
            databases.append(db)
        
        # Deploy storage
        storage = []
        for storage_config in infra_config.get('storage', {}).get('accounts', []):
            account = await self.deploy_storage_account(storage_config)
            storage.append(account)
        
        return {
            'resource_group': rg,
            'vnet': vnet,
            'cluster': cluster,
            'databases': databases,
            'storage': storage
        }
    
    async def _create_resource_group(self) -> dict:
        """Create resource group"""
        rg_name = self.config.get('resource_group')
        location = self.config.get('location')
        
        rg_result = self.resource_client.resource_groups.create_or_update(
            rg_name,
            {'location': location}
        )
        
        return {
            'name': rg_name,
            'location': location
        }
    
    async def deploy_vnet(self, vnet_config: dict) -> dict:
        """Deploy Virtual Network"""
        logger.info(f"Deploying VNet: {vnet_config.get('name')}")
        
        vnet_params = {
            'location': self.config.get('location'),
            'address_space': {
                'address_prefixes': [vnet_config.get('address_space', '10.0.0.0/16')]
            },
            'subnets': []
        }
        
        # Create subnets
        for subnet_config in vnet_config.get('subnets', []):
            subnet = {
                'name': subnet_config['name'],
                'address_prefix': subnet_config['address_prefix']
            }
            vnet_params['subnets'].append(subnet)
        
        poller = self.resource_client.networks.begin_create_or_update(
            self.config.get('resource_group'),
            vnet_config['name'],
            vnet_params
        )
        
        vnet_result = poller.result()
        
        return {
            'vnet_name': vnet_config['name'],
            'vnet_id': vnet_result.id,
            'subnets': vnet_config.get('subnets', [])
        }
    
    async def deploy_aks_cluster(self, k8s_config: dict) -> dict:
        """Deploy AKS cluster"""
        logger.info(f"Deploying AKS cluster: {k8s_config.get('name')}")
        
        cluster_params = {
            'location': self.config.get('location'),
            'dns_prefix': k8s_config['name'],
            'kubernetes_version': k8s_config.get('version', '1.28'),
            'agent_pool_profiles': []
        }
        
        # Create node pools
        for node_pool in k8s_config.get('node_pools', []):
            pool_profile = {
                'name': node_pool['name'],
                'count': node_pool.get('node_count', 3),
                'vm_size': node_pool.get('vm_size', 'Standard_DS2_v2'),
                'os_type': 'Linux',
                'enable_auto_scaling': node_pool.get('enable_auto_scaling', False),
                'min_count': node_pool.get('min_count', 1),
                'max_count': node_pool.get('max_count', 10)
            }
            cluster_params['agent_pool_profiles'].append(pool_profile)
        
        poller = self.container_client.managed_clusters.begin_create_or_update(
            self.config.get('resource_group'),
            k8s_config['name'],
            cluster_params
        )
        
        cluster_result = poller.result()
        
        return {
            'cluster_name': k8s_config['name'],
            'cluster_id': cluster_result.id,
            'fqdn': cluster_result.fqdn
        }
    
    async def deploy_azure_sql_instance(self, db_config: dict) -> dict:
        """Deploy Azure SQL instance"""
        logger.info(f"Deploying Azure SQL instance: {db_config['name']}")
        
        server_params = {
            'location': self.config.get('location'),
            'administrator_login': db_config['admin_username'],
            'administrator_login_password': db_config['admin_password'],
            'version': db_config.get('version', '12.0')
        }
        
        poller = self.sql_client.servers.begin_create_or_update(
            self.config.get('resource_group'),
            db_config['name'],
            server_params
        )
        
        server_result = poller.result()
        
        # Create database
        db_params = {
            'location': self.config.get('location'),
            'sku': {
                'name': db_config.get('sku_name', 'GP_Gen5_2'),
                'tier': db_config.get('tier', 'GeneralPurpose')
            }
        }
        
        db_poller = self.sql_client.databases.begin_create_or_update(
            self.config.get('resource_group'),
            db_config['name'],
            'primary',
            db_params
        )
        
        db_result = db_poller.result()
        
        return {
            'server_name': db_config['name'],
            'database_name': 'primary',
            'server_id': server_result.id
        }
    
    async def deploy_storage_account(self, storage_config: dict) -> dict:
        """Deploy Storage Account"""
        logger.info(f"Creating Storage Account: {storage_config['name']}")
        
        storage_params = {
            'location': self.config.get('location'),
            'sku': {
                'name': storage_config.get('sku', 'Standard_LRS')
            },
            'kind': storage_config.get('kind', 'StorageV2'),
            'access_tier': 'Hot'
        }
        
        poller = self.storage_client.storage_accounts.begin_create(
            self.config.get('resource_group'),
            storage_config['name'],
            storage_params
        )
        
        storage_result = poller.result()
        
        # Create blob containers
        containers = []
        for container_config in storage_config.get('containers', []):
            container = await self._create_blob_container(
                storage_config['name'],
                container_config
            )
            containers.append(container)
        
        return {
            'account_name': storage_config['name'],
            'account_id': storage_result.id,
            'containers': containers
        }
    
    async def _create_blob_container(self, account_name: str, container_config: dict) -> dict:
        """Create blob container"""
        from azure.storage.blob import BlobServiceClient
        
        credential = DefaultAzureCredential()
        blob_service = BlobServiceClient(
            account_url=f"[EXTERNAL_URL_REMOVED]}.blob.core.windows.net",
            credential=credential
        )
        
        container_client = blob_service.get_container_client(container_config['name'])
        container_client.create_container()
        
        return {
            'name': container_config['name'],
            'access_level': container_config.get('access_level', 'private')
        }
```

### 9.4 Kubernetes Adapter Implementation

```python
# ns-root/namespaces-adk/adk/plugins/deployment/adapters/kubernetes_adapter.py

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class KubernetesAdapter:
    """Kubernetes deployment adapter"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Initialize Kubernetes adapter"""
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            config.load_incluster_config()
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
    
    async def deploy_namespace(self, namespace: str) -> dict:
        """Deploy namespace"""
        logger.info(f"Creating namespace: {namespace}")
        
        namespace_obj = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace)
        )
        
        try:
            result = self.core_v1.create_namespace(namespace_obj)
            return {
                'name': namespace,
                'status': 'created'
            }
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Namespace {namespace} already exists")
                return {
                    'name': namespace,
                    'status': 'exists'
                }
            raise
    
    async def deploy_deployment(self, deployment_config: dict) -> dict:
        """Deploy deployment"""
        logger.info(f"Deploying deployment: {deployment_config['name']}")
        
        namespace = deployment_config.get('namespace', 'default')
        
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=deployment_config['name'],
                namespace=namespace,
                labels=deployment_config.get('labels', {})
            ),
            spec=client.V1DeploymentSpec(
                replicas=deployment_config.get('replicas', 1),
                selector=client.V1LabelSelector(
                    match_labels=deployment_config.get('selector_labels', {})
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels=deployment_config.get('pod_labels', {})
                    ),
                    spec=await self._build_pod_spec(deployment_config)
                )
            )
        )
        
        result = self.apps_v1.create_namespaced_deployment(
            namespace=namespace,
            body=deployment
        )
        
        return {
            'name': deployment_config['name'],
            'namespace': namespace,
            'uid': result.metadata.uid
        }
    
    async def _build_pod_spec(self, deployment_config: dict) -> client.V1PodSpec:
        """Build pod spec"""
        containers = []
        
        for container_config in deployment_config.get('containers', []):
            container = client.V1Container(
                name=container_config['name'],
                image=container_config['image'],
                ports=[
                    client.V1ContainerPort(container_port=p)
                    for p in container_config.get('ports', [])
                ],
                env=[
                    client.V1EnvVar(
                        name=e['name'],
                        value=e.get('value'),
                        value_from=self._build_env_var_source(e.get('value_from'))
                    )
                    for e in container_config.get('env', [])
                ],
                resources=self._build_resource_requirements(
                    container_config.get('resources', {})
                )
            )
            containers.append(container)
        
        return client.V1PodSpec(
            containers=containers,
            service_account_name=deployment_config.get('service_account_name'),
            volumes=await self._build_volumes(deployment_config.get('volumes', []))
        )
    
    def _build_env_var_source(self, value_from: Optional[dict]) -> Optional[client.V1EnvVarSource]:
        """Build environment variable source"""
        if not value_from:
            return None
        
        if 'secret_key_ref' in value_from:
            return client.V1EnvVarSource(
                secret_key_ref=client.V1SecretKeySelector(
                    name=value_from['secret_key_ref']['name'],
                    key=value_from['secret_key_ref']['key']
                )
            )
        
        return None
    
    def _build_resource_requirements(self, resources: dict) -> Optional[client.V1ResourceRequirements]:
        """Build resource requirements"""
        if not resources:
            return None
        
        return client.V1ResourceRequirements(
            requests=resources.get('requests'),
            limits=resources.get('limits')
        )
    
    async def _build_volumes(self, volume_configs: List[dict]) -> List[client.V1Volume]:
        """Build volumes"""
        volumes = []
        
        for vol_config in volume_configs:
            volume = client.V1Volume(name=vol_config['name'])
            
            if 'persistent_volume_claim' in vol_config:
                volume.persistent_volume_claim = client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=vol_config['persistent_volume_claim']['claim_name']
                )
            
            volumes.append(volume)
        
        return volumes
    
    async def deploy_service(self, service_config: dict) -> dict:
        """Deploy service"""
        logger.info(f"Deploying service: {service_config['name']}")
        
        namespace = service_config.get('namespace', 'default')
        
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=service_config['name'],
                namespace=namespace,
                labels=service_config.get('labels', {})
            ),
            spec=client.V1ServiceSpec(
                type=service_config.get('type', 'ClusterIP'),
                selector=service_config.get('selector', {}),
                ports=[
                    client.V1ServicePort(
                        name=p.get('name', 'http'),
                        protocol=p.get('protocol', 'TCP'),
                        port=p['port'],
                        target_port=p.get('target_port', p['port'])
                    )
                    for p in service_config.get('ports', [])
                ]
            )
        )
        
        result = self.core_v1.create_namespaced_service(
            namespace=namespace,
            body=service
        )
        
        return {
            'name': service_config['name'],
            'namespace': namespace,
            'cluster_ip': result.spec.cluster_ip
        }
    
    async def deploy_config_map(self, config_map_config: dict) -> dict:
        """Deploy ConfigMap"""
        logger.info(f"Deploying ConfigMap: {config_map_config['name']}")
        
        namespace = config_map_config.get('namespace', 'default')
        
        config_map = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=config_map_config['name'],
                namespace=namespace
            ),
            data=config_map_config.get('data', {})
        )
        
        result = self.core_v1.create_namespaced_config_map(
            namespace=namespace,
            body=config_map
        )
        
        return {
            'name': config_map_config['name'],
            'namespace': namespace
        }
    
    async def deploy_secret(self, secret_config: dict) -> dict:
        """Deploy secret"""
        logger.info(f"Deploying secret: {secret_config['name']}")
        
        namespace = secret_config.get('namespace', 'default')
        
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(
                name=secret_config['name'],
                namespace=namespace
            ),
            data=secret_config.get('data', {})
        )
        
        result = self.core_v1.create_namespaced_secret(
            namespace=namespace,
            body=secret
        )
        
        return {
            'name': secret_config['name'],
            'namespace': namespace
        }
    
    async def deploy_ingress(self, ingress_config: dict) -> dict:
        """Deploy ingress"""
        logger.info(f"Deploying ingress: {ingress_config['name']}")
        
        namespace = ingress_config.get('namespace', 'default')
        
        ingress = client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=ingress_config['name'],
                namespace=namespace,
                annotations=ingress_config.get('annotations', {})
            ),
            spec=client.V1IngressSpec(
                rules=[
                    client.V1IngressRule(
                        host=rule.get('host'),
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path=path.get('path', '/'),
                                    path_type=path.get('path_type', 'Prefix'),
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name=path['service_name'],
                                            port=client.V1ServiceBackendPort(
                                                number=path['service_port']
                                            )
                                        )
                                    )
                                )
                                for path in rule.get('paths', [])
                            ]
                        )
                    )
                    for rule in ingress_config.get('rules', [])
                ],
                tls=[
                    client.V1IngressTLS(
                        hosts=tls.get('hosts', []),
                        secret_name=tls.get('secret_name')
                    )
                    for tls in ingress_config.get('tls', [])
                ]
            )
        )
        
        result = self.networking_v1.create_namespaced_ingress(
            namespace=namespace,
            body=ingress
        )
        
        return {
            'name': ingress_config['name'],
            'namespace': namespace
        }
    
    async def wait_for_deployment_ready(self, namespace: str, name: str, timeout: int = 300) -> bool:
        """Wait for deployment to be ready"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
                
                if deployment.status.ready_replicas == deployment.spec.replicas:
                    logger.info(f"Deployment {name} is ready")
                    return True
                
                logger.info(f"Waiting for deployment {name}: {deployment.status.ready_replicas}/{deployment.spec.replicas} replicas ready")
                time.sleep(5)
            except ApiException as e:
                logger.error(f"Error checking deployment {name}: {e}")
                time.sleep(5)
        
        logger.error(f"Timeout waiting for deployment {name}")
        return False
```

### 9.5 Docker Compose Adapter Implementation

```python
# ns-root/namespaces-adk/adk/plugins/deployment/adapters/docker_compose_adapter.py

import docker
from docker.errors import DockerException
from typing import Dict, List
import yaml
import logging

logger = logging.getLogger(__name__)


class DockerComposeAdapter:
    """Docker Compose deployment adapter"""
    
    def __init__(self, compose_file: str = 'docker-compose.yml'):
        """Initialize Docker Compose adapter"""
        self.compose_file = compose_file
        self.docker_client = docker.from_env()
    
    async def deploy(self) -> dict:
        """Deploy services using Docker Compose"""
        logger.info(f"Deploying services from {self.compose_file}")
        
        # Load compose file
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Deploy services
        services = []
        for service_name, service_config in compose_config.get('services', {}).items():
            service = await self._deploy_service(service_name, service_config)
            services.append(service)
        
        # Deploy networks
        networks = []
        for network_name, network_config in compose_config.get('networks', {}).items():
            network = await self._deploy_network(network_name, network_config)
            networks.append(network)
        
        # Deploy volumes
        volumes = []
        for volume_name, volume_config in compose_config.get('volumes', {}).items():
            volume = await self._deploy_volume(volume_name, volume_config)
            volumes.append(volume)
        
        return {
            'services': services,
            'networks': networks,
            'volumes': volumes
        }
    
    async def _deploy_service(self, name: str, config: dict) -> dict:
        """Deploy service"""
        logger.info(f"Deploying service: {name}")
        
        # Build image if needed
        if 'build' in config:
            logger.info(f"Building image for service {name}")
            self.docker_client.images.build(
                path=config['build'],
                tag=config.get('image', f"{name}:latest")
            )
        
        # Pull image if specified
        elif 'image' in config:
            logger.info(f"Pulling image: {config['image']}")
            self.docker_client.images.pull(config['image'])
        
        # Create container
        container_config = {
            'image': config.get('image'),
            'detach': True,
            'ports': self._format_ports(config.get('ports', [])),
            'environment': config.get('environment', {}),
            'volumes': self._format_volumes(config.get('volumes', [])),
            'networks': list(config.get('networks', {}).keys()),
            'restart': config.get('restart', 'always')
        }
        
        container = self.docker_client.containers.run(
            name=name,
            **container_config
        )
        
        return {
            'name': name,
            'container_id': container.id,
            'status': 'running'
        }
    
    def _format_ports(self, ports: List[str]) -> Dict[str, str]:
        """Format ports for Docker API"""
        port_mapping = {}
        for port in ports:
            if ':' in port:
                host_port, container_port = port.split(':')
                port_mapping[container_port] = host_port
            else:
                port_mapping[port] = None
        return port_mapping
    
    def _format_volumes(self, volumes: List[str]) -> List[str]:
        """Format volumes for Docker API"""
        return volumes
    
    async def _deploy_network(self, name: str, config: dict) -> dict:
        """Deploy network"""
        logger.info(f"Creating network: {name}")
        
        try:
            network = self.docker_client.networks.create(
                name=name,
                driver=config.get('driver', 'bridge'),
                ipam=config.get('ipam')
            )
            return {
                'name': name,
                'id': network.id
            }
        except DockerException as e:
            if 'already exists' in str(e):
                return {
                    'name': name,
                    'status': 'exists'
                }
            raise
    
    async def _deploy_volume(self, name: str, config: dict) -> dict:
        """Deploy volume"""
        logger.info(f"Creating volume: {name}")
        
        try:
            volume = self.docker_client.volumes.create(
                name=name,
                driver=config.get('driver', 'local')
            )
            return {
                'name': name,
                'id': volume.id
            }
        except DockerException as e:
            if 'already exists' in str(e):
                return {
                    'name': name,
                    'status': 'exists'
                }
            raise
    
    async def stop(self, service_name: Optional[str] = None) -> dict:
        """Stop services"""
        if service_name:
            logger.info(f"Stopping service: {service_name}")
            container = self.docker_client.containers.get(service_name)
            container.stop()
            return {'name': service_name, 'status': 'stopped'}
        else:
            logger.info("Stopping all services")
            for container in self.docker_client.containers.list(all=True):
                container.stop()
            return {'status': 'all_stopped'}
    
    async def remove(self, service_name: Optional[str] = None) -> dict:
        """Remove services"""
        if service_name:
            logger.info(f"Removing service: {service_name}")
            container = self.docker_client.containers.get(service_name)
            container.remove()
            return {'name': service_name, 'status': 'removed'}
        else:
            logger.info("Removing all services")
            for container in self.docker_client.containers.list(all=True):
                container.remove()
            return {'status': 'all_removed'}
```

---

## 10. Testing and Validation

### 10.1 Provider Validation Tests

```python
# ns-root/namespaces-adk/adk/plugins/deployment/tests/test_providers.py

import pytest
from deployment.adapters.aws_adapter import AWSAdapter
from deployment.adapters.gcp_adapter import GCPAdapter
from deployment.adapters.azure_adapter import AzureAdapter
from deployment.adapters.kubernetes_adapter import KubernetesAdapter
from deployment.adapters.docker_compose_adapter import DockerComposeAdapter


class TestProviderAdapters:
    """Test provider adapters"""
    
    @pytest.mark.asyncio
    async def test_aws_adapter_initialization(self):
        """Test AWS adapter initialization"""
        config = {
            'region': 'us-east-1',
            'profile': 'default'
        }
        adapter = AWSAdapter(config)
        assert adapter.config.region == 'us-east-1'
        assert adapter.ec2 is not None
    
    @pytest.mark.asyncio
    async def test_gcp_adapter_initialization(self):
        """Test GCP adapter initialization"""
        config = {
            'project': 'test-project',
            'region': 'us-central1'
        }
        adapter = GCPAdapter(config)
        assert adapter.config['project'] == 'test-project'
        assert adapter.storage_client is not None
    
    @pytest.mark.asyncio
    async def test_azure_adapter_initialization(self):
        """Test Azure adapter initialization"""
        config = {
            'subscription_id': 'test-subscription-id',
            'location': 'eastus'
        }
        adapter = AzureAdapter(config)
        assert adapter.config['subscription_id'] == 'test-subscription-id'
        assert adapter.resource_client is not None
    
    @pytest.mark.asyncio
    async def test_kubernetes_adapter_initialization(self):
        """Test Kubernetes adapter initialization"""
        adapter = KubernetesAdapter()
        assert adapter.core_v1 is not None
        assert adapter.apps_v1 is not None
    
    @pytest.mark.asyncio
    async def test_docker_compose_adapter_initialization(self):
        """Test Docker Compose adapter initialization"""
        adapter = DockerComposeAdapter('docker-compose.yml')
        assert adapter.compose_file == 'docker-compose.yml'
        assert adapter.docker_client is not None
```

### 10.2 Integration Tests

```python
# ns-root/namespaces-adk/adk/plugins/deployment/tests/test_integration.py

import pytest
import tempfile
import os


class TestDeploymentIntegration:
    """Test deployment integration"""
    
    @pytest.mark.asyncio
    async def test_kubernetes_deployment_flow(self):
        """Test complete Kubernetes deployment flow"""
        # This test requires a running Kubernetes cluster
        # Skip if cluster not available
        
        adapter = KubernetesAdapter()
        
        # Deploy namespace
        namespace_result = await adapter.deploy_namespace('test-namespace')
        assert namespace_result['status'] in ['created', 'exists']
        
        # Deploy ConfigMap
        config_map_result = await adapter.deploy_config_map({
            'name': 'test-config',
            'namespace': 'test-namespace',
            'data': {
                'key1': 'value1',
                'key2': 'value2'
            }
        })
        assert config_map_result['name'] == 'test-config'
        
        # Deploy deployment
        deployment_result = await adapter.deploy_deployment({
            'name': 'test-deployment',
            'namespace': 'test-namespace',
            'replicas': 1,
            'containers': [{
                'name': 'test-container',
                'image': 'nginx:latest',
                'ports': [80]
            }]
        })
        assert deployment_result['name'] == 'test-deployment'
        
        # Deploy service
        service_result = await adapter.deploy_service({
            'name': 'test-service',
            'namespace': 'test-namespace',
            'type': 'ClusterIP',
            'selector': {'app': 'test'},
            'ports': [{'port': 80, 'target_port': 80}]
        })
        assert service_result['name'] == 'test-service'
    
    @pytest.mark.asyncio
    async def test_docker_compose_deployment_flow(self):
        """Test Docker Compose deployment flow"""
        # Create temporary compose file
        compose_content = """
version: '3.8'
services:
  nginx:
    image: nginx:latest
    ports:
      - "8080:80"
  
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(compose_content)
            temp_file = f.name
        
        try:
            adapter = DockerComposeAdapter(temp_file)
            result = await adapter.deploy()
            
            assert len(result['services']) == 2
            assert any(s['name'] == 'nginx' for s in result['services'])
            assert any(s['name'] == 'redis' for s in result['services'])
            
            # Cleanup
            await adapter.stop()
            await adapter.remove()
        finally:
            os.unlink(temp_file)
```

---

## 11. Documentation and Examples

### 11.1 Quick Start Guides

#### AWS Deployment Quick Start
```bash
# Quick start for AWS deployment
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
export ENVIRONMENT=production

# Deploy
./scripts/deploy-universal.sh aws $ENVIRONMENT
```

#### GCP Deployment Quick Start
```bash
# Quick start for GCP deployment
export GCP_PROJECT=your-project-id
export GCP_ZONE=us-central1-a
export ENVIRONMENT=production

# Deploy
./scripts/deploy-universal.sh gcp $ENVIRONMENT
```

#### Azure Deployment Quick Start
```bash
# Quick start for Azure deployment
export AZURE_SUBSCRIPTION_ID=your-subscription-id
export AZURE_RESOURCE_GROUP=your-rg
export AZURE_LOCATION=eastus
export ENVIRONMENT=production

# Deploy
./scripts/deiversal.sh azure $ENVIRONMENT
```

#### On-Premise Deployment Quick Start
```bash
# Quick start for on-premise deployment
export ENVIRONMENT=production

# Deploy to Kubernetes
./scripts/deploy-universal.sh kubernetes $ENVIRONMENT

# Or deploy with Docker Compose
./scripts/deploy-universal.sh docker-compose $ENVIRONMENT
```

---

## 12. Conclusion

This pluggable architecture design provides:

### Key Benefits
- **Zero Lock-in**: Deploy to any cloud provider without code changes
- **Configuration Driven**: All provider differences in YAML files
- **Easy Migration**: Switch providers by changing configuration
- **Consistent API**: Same deployment interface for all environments
- **Progressive Enhancement**: Basic deployment works, advanced features optional

### Supported Environments
- Cloud: AWS, GCP, Azure, DigitalOcean, Linode, OVH
- Container: Kubernetes, Docker Compose, Nomad
- On-Premise: Bare Metal, Virtual Machines
- Hybrid: Multi-cloud, cloud + on-premise

### Next Steps
1. Implement remaining provider adapters (DigitalOcean, Linode, OVH, Nomad)
2. Add more comprehensive validation tests
3. Create migration guides between providers
4. Implement cost optimization recommendations
5. Add provider-specific best practices documentation

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-27  
**Status**: Design Complete