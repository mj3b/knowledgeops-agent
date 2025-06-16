# NAVO Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying NAVO (Navigate + Ops) Enterprise Knowledge Discovery Platform in production environments. NAVO v2.0 includes advanced Phase 3 (Multi-Source Orchestration) and Phase 4 (Proactive Knowledge Management) capabilities that transform reactive documentation search into proactive knowledge orchestration.

## Architecture Overview

NAVO v2.0 implements a sophisticated four-phase architecture designed for enterprise-scale deployment:

### Phase 1: Knowledge Discovery Foundation
- Multi-source search across Confluence and SharePoint
- Natural language query processing
- Source attribution and relevance scoring
- Basic caching and permission management

### Phase 2: Intelligent Memory & Reasoning
- Persistent memory layer with episodic, semantic, and procedural memory
- Transparent reasoning engine with multi-step analysis
- Continuous learning from user interactions
- Governance framework with audit trails

### Phase 3: Multi-Source Orchestration
- Unified cross-platform search with intelligent ranking
- Content fusion and cross-referencing capabilities
- Permission-aware orchestration across multiple sources
- Real-time source health monitoring and failover

### Phase 4: Proactive Knowledge Management
- Predictive content caching based on usage patterns
- Automated content lifecycle management
- Knowledge gap detection and recommendations
- Auto-organization and intelligent tagging

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores, 2.4 GHz
- RAM: 8 GB
- Storage: 100 GB SSD
- Network: 1 Gbps

**Recommended Production Requirements:**
- CPU: 8 cores, 3.0 GHz
- RAM: 16 GB
- Storage: 500 GB SSD
- Network: 10 Gbps

### Software Dependencies

**Core Dependencies:**
- Python 3.11+
- PostgreSQL 13+ (primary database)
- Redis 6+ (caching and session storage)
- Docker 20.10+ (containerization)
- Kubernetes 1.24+ (orchestration, optional)

**Optional Dependencies:**
- Nginx (reverse proxy and load balancing)
- Prometheus + Grafana (monitoring)
- ELK Stack (logging and analytics)

### External Service Requirements

**Required Integrations:**
- OpenAI Enterprise GPT API access
- Confluence Cloud or Server instance
- SharePoint Online or Server instance
- Microsoft Teams (for notifications)

**Authentication Requirements:**
- Azure Active Directory (recommended)
- OAuth 2.0 / OpenID Connect support
- JWT token validation capability

## Installation Methods

### Method 1: Docker Deployment (Recommended)

#### Step 1: Clone Repository
```bash
git clone https://github.com/mj3b/navo.git
cd navo
```

#### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
# Enterprise GPT Configuration
ENTERPRISE_GPT_API_KEY=your_openai_enterprise_key
ENTERPRISE_ORGANIZATION_ID=your_openai_org_id

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=navo
DB_USERNAME=navo
DB_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Integration Configuration
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
CONFLUENCE_USERNAME=service_account@yourcompany.com
CONFLUENCE_API_TOKEN=your_confluence_token

SHAREPOINT_TENANT_ID=your_azure_tenant_id
SHAREPOINT_CLIENT_ID=your_azure_app_id
SHAREPOINT_CLIENT_SECRET=your_azure_app_secret

# Security Configuration
JWT_SECRET=your_jwt_secret_key
```

#### Step 3: Deploy with Docker Compose
```bash
# Start all services
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs navo
```

#### Step 4: Initialize Database
```bash
# Run database migrations
docker-compose exec navo python -m alembic upgrade head

# Create initial admin user
docker-compose exec navo python scripts/create_admin.py
```

#### Step 5: Verify Installation
```bash
# Health check
curl http://localhost:8000/health

# Test query endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I configure API versioning?",
    "user_id": "test_user",
    "max_results": 5
  }'
```

### Method 2: Kubernetes Deployment

#### Step 1: Prepare Kubernetes Manifests
```bash
# Create namespace
kubectl create namespace navo

# Apply configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgresql.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/navo.yaml
```

#### Step 2: Configure Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: navo-ingress
  namespace: navo
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - navo.yourcompany.com
    secretName: navo-tls
  rules:
  - host: navo.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: navo-service
            port:
              number: 8000
```

#### Step 3: Deploy and Scale
```bash
# Apply ingress
kubectl apply -f k8s/ingress.yaml

# Scale deployment
kubectl scale deployment navo --replicas=3 -n navo

# Verify deployment
kubectl get pods -n navo
kubectl logs -f deployment/navo -n navo
```

### Method 3: Manual Installation

#### Step 1: System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Nginx
sudo apt install nginx
```

#### Step 2: Database Setup
```bash
# Create database user
sudo -u postgres createuser --interactive navo

# Create database
sudo -u postgres createdb navo -O navo

# Set password
sudo -u postgres psql -c "ALTER USER navo PASSWORD 'secure_password';"
```

#### Step 3: Application Setup
```bash
# Create application user
sudo useradd -m -s /bin/bash navo

# Switch to application user
sudo su - navo

# Clone repository
git clone https://github.com/mj3b/navo.git
cd navo

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env
```

#### Step 4: Service Configuration
```bash
# Create systemd service
sudo nano /etc/systemd/system/navo.service
```

Service file content:
```ini
[Unit]
Description=NAVO Enterprise Knowledge Discovery Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=navo
Group=navo
WorkingDirectory=/home/navo/navo
Environment=PATH=/home/navo/navo/venv/bin
ExecStart=/home/navo/navo/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 5: Start Services
```bash
# Enable and start services
sudo systemctl enable navo
sudo systemctl start navo

# Check status
sudo systemctl status navo
```

## Configuration

### Core Configuration

The main configuration file is `config/config.yaml`. Key sections include:

#### OpenAI Enterprise Configuration
```yaml
openai:
  api_key: "${ENTERPRISE_GPT_API_KEY}"
  organization_id: "${ENTERPRISE_ORGANIZATION_ID}"
  base_url: "https://api.openai.com/v1"
  default_model: "gpt-4o"
  max_tokens: 4000
  temperature: 0.7
  timeout: 60
```

#### Advanced Features Configuration
```yaml
advanced_features:
  source_orchestration:
    enabled: true
    cross_platform_search: true
    content_fusion: true
    cross_referencing: true
    intelligent_ranking: true
    
  proactive_management:
    enabled: true
    predictive_caching: true
    lifecycle_monitoring: true
    gap_detection: true
    auto_recommendations: true
```

#### Memory and Reasoning Configuration
```yaml
memory:
  enabled: true
  database_path: "data/navo_memory.db"
  max_memory_entries: 100000
  retention_days: 365

reasoning:
  enabled: true
  reasoning_model: "gpt-4o"
  max_reasoning_steps: 5
  confidence_threshold: 0.6
```

### Integration Configuration

#### Confluence Integration
```yaml
integrations:
  confluence:
    enabled: true
    base_url: "${CONFLUENCE_BASE_URL}"
    username: "${CONFLUENCE_USERNAME}"
    api_token: "${CONFLUENCE_API_TOKEN}"
    spaces_to_sync:
      - "ENG"
      - "DOCS"
      - "RUNBOOKS"
    track_freshness: true
    enable_cross_referencing: true
```

#### SharePoint Integration
```yaml
integrations:
  sharepoint:
    enabled: true
    tenant_id: "${SHAREPOINT_TENANT_ID}"
    client_id: "${SHAREPOINT_CLIENT_ID}"
    client_secret: "${SHAREPOINT_CLIENT_SECRET}"
    site_url: "https://yourcompany.sharepoint.com/sites/engineering"
    respect_permissions: true
    enable_cross_referencing: true
```

### Security Configuration

#### Authentication and Authorization
```yaml
security:
  jwt_secret: "${JWT_SECRET}"
  session_timeout: 3600
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10
  
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
  
  audit_logging:
    enabled: true
    retention_days: 365
```

#### Permission Management
NAVO implements role-based access control (RBAC) with the following roles:

- **Admin**: Full system access, configuration management
- **Power User**: Advanced features, analytics access
- **User**: Standard query and search capabilities
- **Read-Only**: View-only access to public content

### Performance Configuration

#### Caching Strategy
```yaml
cache:
  redis_url: "${REDIS_URL}"
  default_ttl: 3600
  max_memory: "512mb"
  
  levels:
    l1_memory:
      enabled: true
      max_size: 1000
      ttl: 300
    l2_redis:
      enabled: true
      ttl: 3600
    l3_predictive:
      enabled: true
      ttl: 7200
      max_entries: 10000
```

#### Database Optimization
```yaml
database:
  primary:
    type: "postgresql"
    pool_size: 10
    max_overflow: 20
  
performance:
  connection_pools:
    database: 20
    redis: 10
    http: 50
  
  async_workers: 4
  max_concurrent_requests: 100
  max_memory_usage_mb: 2048
```

## Monitoring and Observability

### Health Monitoring

NAVO provides comprehensive health monitoring through multiple endpoints:

#### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

Response includes:
- Overall system status
- Component health (database, cache, integrations)
- Performance metrics
- Uptime information

#### Performance Metrics
```bash
curl http://localhost:8000/performance/metrics
```

Metrics include:
- Query response times
- Source performance
- Cache hit rates
- Error rates

### Logging Configuration

#### Application Logging
```yaml
monitoring:
  enabled: true
  log_queries: true
  track_performance: true
  
  performance_tracking:
    track_response_times: true
    track_accuracy: true
    track_user_satisfaction: true
```

#### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

### Prometheus Integration

#### Metrics Export
NAVO exports metrics in Prometheus format at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `navo_queries_total`: Total number of queries processed
- `navo_query_duration_seconds`: Query processing time
- `navo_source_health`: Source health status
- `navo_cache_hit_rate`: Cache hit rate percentage

#### Grafana Dashboard

Import the provided Grafana dashboard (`monitoring/grafana-dashboard.json`) for comprehensive visualization:

- Query performance trends
- Source health monitoring
- User activity patterns
- System resource utilization

## Backup and Recovery

### Database Backup

#### Automated Backup
```yaml
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention_days: 30
  storage_type: "s3"
  s3_bucket: "${BACKUP_S3_BUCKET}"
  encryption: true
```

#### Manual Backup
```bash
# PostgreSQL backup
pg_dump -h localhost -U navo navo > navo_backup_$(date +%Y%m%d).sql

# Memory database backup
cp data/navo_memory.db backups/navo_memory_$(date +%Y%m%d).db

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/ .env
```

### Disaster Recovery

#### Recovery Procedures

1. **Database Recovery**:
```bash
# Restore PostgreSQL
psql -h localhost -U navo navo < navo_backup_20240615.sql

# Restore memory database
cp backups/navo_memory_20240615.db data/navo_memory.db
```

2. **Configuration Recovery**:
```bash
# Restore configuration
tar -xzf config_backup_20240615.tar.gz
```

3. **Service Restart**:
```bash
# Docker deployment
docker-compose down
docker-compose up -d

# Systemd deployment
sudo systemctl restart navo
```

#### Recovery Testing

Regular recovery testing should be performed:

1. **Monthly**: Test database restoration
2. **Quarterly**: Full system recovery simulation
3. **Annually**: Disaster recovery drill

## Scaling and High Availability

### Horizontal Scaling

#### Load Balancing
Configure Nginx for load balancing across multiple NAVO instances:

```nginx
upstream navo_backend {
    server navo1:8000;
    server navo2:8000;
    server navo3:8000;
}

server {
    listen 80;
    server_name navo.yourcompany.com;
    
    location / {
        proxy_pass http://navo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### Database Scaling
- **Read Replicas**: Configure PostgreSQL read replicas for query distribution
- **Connection Pooling**: Use PgBouncer for connection management
- **Partitioning**: Implement table partitioning for large datasets

#### Cache Scaling
- **Redis Cluster**: Deploy Redis in cluster mode for high availability
- **Cache Warming**: Implement predictive cache warming strategies
- **CDN Integration**: Use CloudFront or similar for static content

### Vertical Scaling

#### Resource Optimization
Monitor and adjust:
- CPU allocation based on query load
- Memory allocation for caching efficiency
- Storage I/O for database performance

#### Performance Tuning
```yaml
performance:
  async_workers: 8  # Increase for higher concurrency
  max_concurrent_requests: 200
  max_memory_usage_mb: 4096
  
  cache_warming: true
  preload_common_queries: true
```

## Security Hardening

### Network Security

#### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8000/tcp   # Block direct app access
sudo ufw enable
```

#### SSL/TLS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name navo.yourcompany.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### Application Security

#### Input Validation
- Query length limits (1000 characters)
- Content type validation
- SQL injection prevention
- XSS protection

#### Authentication Security
- JWT token validation
- Session timeout enforcement
- Rate limiting per user
- Failed login attempt monitoring

#### Data Protection
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- PII data masking
- Audit trail maintenance

## Troubleshooting

### Common Issues

#### Issue 1: High Memory Usage
**Symptoms**: System becomes slow, out of memory errors
**Diagnosis**:
```bash
# Check memory usage
docker stats navo
ps aux | grep python

# Check cache size
redis-cli info memory
```
**Resolution**:
- Reduce cache size in configuration
- Increase system memory
- Optimize query patterns

#### Issue 2: Slow Query Performance
**Symptoms**: Queries taking longer than 5 seconds
**Diagnosis**:
```bash
# Check query logs
docker logs navo | grep "Query processing"

# Check database performance
psql -c "SELECT * FROM pg_stat_activity;"
```
**Resolution**:
- Optimize database indexes
- Increase cache TTL
- Review integration timeouts

#### Issue 3: Integration Failures
**Symptoms**: Source health checks failing
**Diagnosis**:
```bash
# Check source health
curl http://localhost:8000/sources/health

# Check integration logs
docker logs navo | grep "Integration"
```
**Resolution**:
- Verify API credentials
- Check network connectivity
- Review rate limiting settings

### Log Analysis

#### Key Log Patterns
```bash
# Query performance issues
grep "Query processing.*[5-9][0-9][0-9][0-9]ms" navo.log

# Integration errors
grep "ERROR.*Integration" navo.log

# Memory warnings
grep "Memory usage.*90%" navo.log

# Authentication failures
grep "Authentication failed" navo.log
```

#### Performance Monitoring
```bash
# Response time analysis
awk '/Query processing/ {print $NF}' navo.log | sort -n | tail -10

# Error rate calculation
grep -c "ERROR" navo.log
grep -c "INFO" navo.log
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks
- Monitor system health and performance
- Review error logs for issues
- Check backup completion status
- Verify integration connectivity

#### Weekly Tasks
- Analyze query performance trends
- Review user feedback and ratings
- Update knowledge gap reports
- Clean up temporary files

#### Monthly Tasks
- Update dependencies and security patches
- Review and optimize database performance
- Analyze usage patterns and capacity planning
- Test backup and recovery procedures

#### Quarterly Tasks
- Security audit and penetration testing
- Performance benchmarking and optimization
- Documentation review and updates
- Disaster recovery testing

### Update Procedures

#### Application Updates
```bash
# Docker deployment
docker-compose pull
docker-compose up -d

# Manual deployment
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart navo
```

#### Database Migrations
```bash
# Run migrations
python -m alembic upgrade head

# Verify migration
python -m alembic current
```

#### Configuration Updates
```bash
# Backup current configuration
cp config/config.yaml config/config.yaml.backup

# Apply new configuration
# Edit config/config.yaml

# Restart service
docker-compose restart navo
```

## Support and Documentation

### Getting Help

#### Community Support
- GitHub Issues: https://github.com/mj3b/navo/issues
- Documentation: https://github.com/mj3b/navo/docs
- Wiki: https://github.com/mj3b/navo/wiki

#### Enterprise Support
For enterprise deployments, consider:
- Professional services for implementation
- Custom integration development
- 24/7 support and monitoring
- Training and knowledge transfer

### Additional Resources

#### Documentation
- [Architecture Guide](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Configuration Guide](CONFIGURATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

#### Training Materials
- Administrator training guide
- User training materials
- Integration best practices
- Performance optimization guide

This deployment guide provides comprehensive instructions for implementing NAVO in production environments. For specific deployment scenarios or custom requirements, consult the additional documentation or seek professional services support.

