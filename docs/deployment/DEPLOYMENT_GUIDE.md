# AutoPR Engine - Production Deployment Guide

## **Table of Contents**
1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Options](#deployment-options)
4. [AWS Deployment](#aws-deployment)
5. [Google Cloud Platform Deployment](#gcp-deployment)
6. [Azure Deployment](#azure-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Docker Compose Deployment](#docker-compose-deployment)
9. [Configuration Management](#configuration-management)
10. [Database Setup](#database-setup)
11. [Monitoring & Logging](#monitoring--logging)
12. [Backup & Disaster Recovery](#backup--disaster-recovery)
13. [Scaling Considerations](#scaling-considerations)
14. [Troubleshooting](#troubleshooting)

---

## **Prerequisites**

### **Required**
- Python 3.12+ runtime
- PostgreSQL 15+ database
- Redis 7+ cache
- GitHub account with appropriate permissions
- At least one AI provider API key (OpenAI, Anthropic, etc.)

### **Recommended**
- Domain name with SSL certificate
- Secrets management service (Vault, AWS Secrets Manager, etc.)
- Monitoring stack (Prometheus, Grafana)
- Log aggregation service (ELK, Loki)
- Container orchestration (Kubernetes, ECS, etc.)

### **System Requirements**

#### **Minimum (Development/Staging)**
- CPU: 2 vCPUs
- RAM: 4 GB
- Storage: 20 GB SSD
- Network: 100 Mbps

#### **Recommended (Production)**
- CPU: 4 vCPUs
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 1 Gbps
- Load Balancer: Yes

---

## **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer (HTTPS)                  │
│                    (SSL Termination)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│  AutoPR Engine  │            │  AutoPR Engine  │
│   (Primary)     │            │   (Replica)     │
└────────┬────────┘            └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   PostgreSQL    │            │     Redis       │
│   (Primary)     │            │   (Primary)     │
│                 │            │                 │
│   (Replica) ────┤            │   (Replica) ────┤
└─────────────────┘            └─────────────────┘
```

**Components**:
- **Load Balancer**: Nginx or cloud provider LB
- **Application**: AutoPR Engine (stateless)
- **Database**: PostgreSQL for persistent data
- **Cache**: Redis for session/temporary data
- **Workers**: Background task processors

---

## **Deployment Options**

### **Comparison Matrix**

| Feature | Docker Compose | Kubernetes | AWS ECS | GCP Cloud Run | Azure Container Apps |
|---------|---------------|------------|---------|---------------|---------------------|
| **Ease of Setup** | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ |
| **Scalability** | ★★☆☆☆ | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| **Cost (Small)** | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ |
| **Complexity** | Low | High | Medium | Low | Medium |
| **Best For** | Dev/Staging | Large Scale | AWS Users | Serverless | Azure Users |

---

## **AWS Deployment**

### **Architecture**

```
Internet Gateway
      ↓
Application Load Balancer (ALB)
      ↓
ECS Fargate Tasks (AutoPR Engine)
      ↓
┌─────────────────┬─────────────────┐
RDS PostgreSQL    ElastiCache Redis
```

### **Step-by-Step Deployment**

#### **1. Setup VPC and Networking**

```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=autopr-vpc}]'

# Create public subnets (for ALB)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b

# Create private subnets (for ECS tasks)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.20.0/24 \
  --availability-zone us-east-1b
```

#### **2. Setup RDS PostgreSQL**

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier autopr-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username autopr_admin \
  --master-user-password "$(openssl rand -base64 32)" \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --multi-az \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name autopr-db-subnet

# Wait for instance to be available
aws rds wait db-instance-available \
  --db-instance-identifier autopr-db
```

#### **3. Setup ElastiCache Redis**

```bash
# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id autopr-redis \
  --replication-group-description "AutoPR Engine Cache" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.medium \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --cache-subnet-group-name autopr-cache-subnet \
  --security-group-ids sg-xxxxx
```

#### **4. Store Secrets in AWS Secrets Manager**

```bash
# Store database credentials
aws secretsmanager create-secret \
  --name autopr/prod/database \
  --secret-string '{
    "username":"autopr_admin",
    "password":"<strong-password>",
    "host":"autopr-db.xxxxx.us-east-1.rds.amazonaws.com",
    "port":5432,
    "database":"autopr"
  }'

# Store GitHub token
aws secretsmanager create-secret \
  --name autopr/prod/github-token \
  --secret-string "ghp_xxxxx"

# Store OpenAI API key
aws secretsmanager create-secret \
  --name autopr/prod/openai-api-key \
  --secret-string "sk-xxxxx"
```

#### **5. Create ECS Task Definition**

```json
{
  "family": "autopr-engine",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::xxxxx:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::xxxxx:role/autoprTaskRole",
  "containerDefinitions": [
    {
      "name": "autopr-engine",
      "image": "xxxxx.dkr.ecr.us-east-1.amazonaws.com/autopr-engine:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "AUTOPR_ENV", "value": "production"},
        {"name": "AUTOPR_LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "GITHUB_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxxxx:secret:autopr/prod/github-token"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxxxx:secret:autopr/prod/openai-api-key"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxxxx:secret:autopr/prod/database:url::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/autopr-engine",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### **6. Create ECS Service**

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name autopr-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
    capacityProvider=FARGATE_SPOT,weight=4

# Create ECS service
aws ecs create-service \
  --cluster autopr-cluster \
  --service-name autopr-engine \
  --task-definition autopr-engine:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-xxxxx,subnet-yyyyy],
    securityGroups=[sg-xxxxx],
    assignPublicIp=DISABLED
  }" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:xxxxx:targetgroup/autopr-tg/xxxxx,containerName=autopr-engine,containerPort=8080" \
  --health-check-grace-period-seconds 60
```

#### **7. Setup Application Load Balancer**

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name autopr-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create target group
aws elbv2 create-target-group \
  --name autopr-tg \
  --protocol HTTP \
  --port 8080 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-enabled \
  --health-check-path /api/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:xxxxx:loadbalancer/app/autopr-alb/xxxxx \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-1:xxxxx:certificate/xxxxx \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:xxxxx:targetgroup/autopr-tg/xxxxx
```

#### **8. Configure Auto Scaling**

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/autopr-cluster/autopr-engine \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/autopr-cluster/autopr-engine \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 75.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }'
```

---

## **GCP Deployment**

### **Using Cloud Run (Serverless)**

#### **1. Build and Push Container**

```bash
# Build image
docker build -t gcr.io/PROJECT_ID/autopr-engine:latest .

# Push to GCR
docker push gcr.io/PROJECT_ID/autopr-engine:latest
```

#### **2. Setup Cloud SQL (PostgreSQL)**

```bash
# Create instance
gcloud sql instances create autopr-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-7680 \
  --region=us-central1 \
  --network=projects/PROJECT_ID/global/networks/default \
  --availability-type=REGIONAL \
  --backup \
  --enable-bin-log

# Create database
gcloud sql databases create autopr \
  --instance=autopr-db

# Create user
gcloud sql users create autopr_app \
  --instance=autopr-db \
  --password="$(openssl rand -base64 32)"
```

#### **3. Setup Memorystore (Redis)**

```bash
# Create Redis instance
gcloud redis instances create autopr-redis \
  --size=5 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=standard
```

#### **4. Deploy to Cloud Run**

```bash
# Deploy service
gcloud run deploy autopr-engine \
  --image gcr.io/PROJECT_ID/autopr-engine:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 2 \
  --memory 4Gi \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars AUTOPR_ENV=production \
  --set-secrets GITHUB_TOKEN=github-token:latest,OPENAI_API_KEY=openai-key:latest \
  --add-cloudsql-instances PROJECT_ID:us-central1:autopr-db \
  --vpc-connector projects/PROJECT_ID/locations/us-central1/connectors/autopr-connector
```

---

## **Kubernetes Deployment**

### **Complete Kubernetes Manifests**

#### **1. Namespace**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: autopr
  labels:
    name: autopr
    environment: production
```

#### **2. Secrets**

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: autopr-secrets
  namespace: autopr
type: Opaque
stringData:
  github-token: "ghp_xxxxx"
  openai-api-key: "sk-xxxxx"
  database-url: "postgresql://user:pass@postgres:5432/autopr"
  redis-url: "redis://:pass@redis:6379/0"
```

#### **3. ConfigMap**

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: autopr-config
  namespace: autopr
data:
  AUTOPR_ENV: "production"
  AUTOPR_LOG_LEVEL: "INFO"
  AUTOPR_HOST: "0.0.0.0"
  AUTOPR_PORT: "8080"
  MAX_CONCURRENT_WORKFLOWS: "10"
  WORKFLOW_TIMEOUT: "300"
```

#### **4. Deployment**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autopr-engine
  namespace: autopr
  labels:
    app: autopr-engine
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: autopr-engine
  template:
    metadata:
      labels:
        app: autopr-engine
        version: v1
    spec:
      containers:
      - name: autopr-engine
        image: ghcr.io/YOUR_USERNAME/autopr-engine:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: autopr-secrets
              key: github-token
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: autopr-secrets
              key: openai-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: autopr-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: autopr-secrets
              key: redis-url
        envFrom:
        - configMapRef:
            name: autopr-config
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      imagePullSecrets:
      - name: ghcr-secret
```

#### **5. Service**

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: autopr-engine
  namespace: autopr
  labels:
    app: autopr-engine
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: autopr-engine
```

#### **6. Ingress**

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autopr-ingress
  namespace: autopr
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - autopr.example.com
    secretName: autopr-tls
  rules:
  - host: autopr.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: autopr-engine
            port:
              number: 80
```

#### **7. HorizontalPodAutoscaler**

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: autopr-engine-hpa
  namespace: autopr
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: autopr-engine
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 15
      selectPolicy: Max
```

#### **Deploy to Kubernetes**

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Verify deployment
kubectl get pods -n autopr
kubectl get svc -n autopr
kubectl get ingress -n autopr

# Check logs
kubectl logs -n autopr -l app=autopr-engine --tail=100 -f
```

---

## **Configuration Management**

### **Environment-Specific Configurations**

Create separate configuration files:

```bash
configs/
├── development.yaml
├── staging.yaml
└── production.yaml
```

### **Production Configuration Example**

```yaml
# configs/production.yaml
environment: production

github:
  timeout: 30
  base_url: https://api.github.com

llm:
  default_provider: openai
  fallback_order: [openai, anthropic, mistral]
  max_tokens: 4000
  temperature: 0.7
  timeout: 60
  max_retries: 3

workflow:
  max_concurrent: 10
  timeout: 300
  retry_attempts: 3
  retry_delay: 5
  enable_parallel_execution: true

database:
  pool_size: 20
  max_overflow: 40
  pool_timeout: 30
  pool_recycle: 3600
  echo: false

redis:
  timeout: 5
  max_connections: 50
  ssl: true

monitoring:
  enable_metrics: true
  metrics_port: 9090
  enable_tracing: true

logging:
  level: INFO
  format: json
  enable_audit: true
```

---

## **Database Setup**

### **Initial Database Migration**

```bash
# TODO: Implement with Alembic (see TASK-7)

# Initialize Alembic
poetry run alembic init alembic

# Create initial migration
poetry run alembic revision --autogenerate -m "Initial schema"

# Apply migrations
poetry run alembic upgrade head
```

### **Database Schema (POC)**

```sql
-- workflows table
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    config JSONB
);

-- workflow_executions table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    execution_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT
);

-- Create indexes
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_started_at ON workflow_executions(started_at DESC);
```

---

## **Monitoring & Logging**

### **Prometheus Metrics**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'autopr-engine'
    static_configs:
      - targets: ['autopr-engine:9090']
    metrics_path: '/metrics'
```

### **Grafana Dashboard**

Import the provided dashboard JSON from `docs/monitoring/grafana-dashboard.json`

Key metrics to monitor:
- Request rate and latency
- Workflow execution times
- Error rates
- Database connection pool usage
- Redis cache hit ratio
- LLM API call rates and costs

---

## **Backup & Disaster Recovery**

### **Database Backups**

```bash
# Automated daily backups
0 2 * * * pg_dump -h $DB_HOST -U $DB_USER -d autopr | gzip > /backups/autopr-$(date +\%Y\%m\%d).sql.gz

# Retention: Keep last 30 days
find /backups -name "autopr-*.sql.gz" -mtime +30 -delete
```

### **Disaster Recovery Plan**

1. **RPO (Recovery Point Objective)**: 1 hour
2. **RTO (Recovery Time Objective)**: 4 hours

**Recovery Steps**:
1. Provision new infrastructure
2. Restore database from latest backup
3. Deploy application from last known good image
4. Verify health checks
5. Update DNS/load balancer
6. Monitor for issues

---

## **Troubleshooting**

### **Common Issues**

#### **Application Won't Start**
```bash
# Check logs
kubectl logs -n autopr -l app=autopr-engine --tail=100

# Verify secrets
kubectl get secret -n autopr autopr-secrets -o yaml

# Check database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql $DATABASE_URL
```

#### **High Memory Usage**
```bash
# Check memory metrics
kubectl top pods -n autopr

# Review workflow history size (should be limited to 1000)
# Restart pods if needed
kubectl rollout restart deployment/autopr-engine -n autopr
```

#### **Slow Performance**
- Check database connection pool settings
- Verify Redis connectivity
- Review LLM API response times
- Check for blocking I/O operations

---

## **Post-Deployment Checklist**

- [ ] SSL certificates installed and auto-renewing
- [ ] All secrets stored in secrets manager
- [ ] Database backups running and tested
- [ ] Monitoring dashboards configured
- [ ] Alerts set up for critical metrics
- [ ] Health checks responding
- [ ] Auto-scaling tested
- [ ] Disaster recovery plan documented
- [ ] Team trained on operations
- [ ] Runbook created for common issues

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-20  
**Maintained by**: DevOps Team
