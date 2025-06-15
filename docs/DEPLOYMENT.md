# NAVO Deployment Guide

## Overview

This guide covers deploying NAVO in production environments, from single-server deployments to enterprise-scale Kubernetes clusters.

## Deployment Options

### 1. Single Server Deployment

**Best for:** Small teams, development, testing

#### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.11+
- Redis server
- 4GB+ RAM, 2+ CPU cores
- SSL certificate (recommended)

#### Installation Steps

```bash
# 1. System preparation
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-pip redis-server nginx -y

# 2. Create NAVO user
sudo useradd -m -s /bin/bash navo
sudo usermod -aG sudo navo

# 3. Clone and setup NAVO
sudo -u navo git clone <repository-url> /home/navo/navo
cd /home/navo/navo
sudo -u navo python3.11 -m pip install -r requirements.txt

# 4. Configure environment
sudo -u navo cp .env.example .env
sudo -u navo nano .env  # Edit with your configuration

# 5. Setup systemd service
sudo cp deployment/navo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable navo
sudo systemctl start navo

# 6. Configure NGINX
sudo cp deployment/nginx.conf /etc/nginx/sites-available/navo
sudo ln -s /etc/nginx/sites-available/navo /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 2. Docker Deployment

**Best for:** Consistent environments, easy scaling

#### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  navo:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    depends_on:
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - navo
    restart: unless-stopped

volumes:
  redis_data:
```

#### Deployment Commands

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f navo

# Scale NAVO instances
docker-compose up -d --scale navo=3

# Update deployment
docker-compose pull && docker-compose up -d
```

### 3. Kubernetes Deployment

**Best for:** Enterprise scale, high availability

#### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: navo

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: navo-config
  namespace: navo
data:
  config.yaml: |
    server:
      host: "0.0.0.0"
      port: 8000
    cache:
      redis_url: "redis://redis-service:6379"
    # ... rest of configuration
```

#### Secrets Management

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: navo-secrets
  namespace: navo
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  confluence-token: <base64-encoded-token>
  sharepoint-secret: <base64-encoded-secret>
```

#### NAVO Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: navo
  namespace: navo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: navo
  template:
    metadata:
      labels:
        app: navo
    spec:
      containers:
      - name: navo
        image: navo:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: navo-secrets
              key: openai-api-key
        - name: CONFLUENCE_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: navo-secrets
              key: confluence-token
        volumeMounts:
        - name: config
          mountPath: /app/config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: navo-config
```

#### Service and Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: navo-service
  namespace: navo
spec:
  selector:
    app: navo
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: navo-ingress
  namespace: navo
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - navo.yourdomain.com
    secretName: navo-tls
  rules:
  - host: navo.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: navo-service
            port:
              number: 80
```

#### Redis Deployment

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: navo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: navo
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

## Configuration Management

### Environment Variables

```bash
# Production environment variables
export OPENAI_API_KEY="your_enterprise_api_key"
export OPENAI_ORGANIZATION_ID="your_org_id"
export CONFLUENCE_BASE_URL="https://yourcompany.atlassian.net"
export CONFLUENCE_USERNAME="service_account"
export CONFLUENCE_API_TOKEN="your_api_token"
export SHAREPOINT_TENANT_ID="your_tenant_id"
export SHAREPOINT_CLIENT_ID="your_client_id"
export SHAREPOINT_CLIENT_SECRET="your_client_secret"
export REDIS_URL="redis://redis-cluster:6379"
export JWT_SECRET="your_production_jwt_secret"
```

### Configuration Files

#### Production Config (`config/production.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

openai:
  timeout: 120
  max_tokens: 4000
  temperature: 0.7

cache:
  redis_url: "${REDIS_URL}"
  default_ttl: 7200
  query_cache_ttl: 3600

integrations:
  confluence:
    max_results_per_request: 100
    sync_attachments: true
  sharepoint:
    max_file_size_mb: 100
    extract_metadata: true

logging:
  level: "INFO"
  structured: true
  json_format: true

monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090

rate_limiting:
  enabled: true
  requests_per_minute: 120
  burst_size: 20
```

## Security Configuration

### SSL/TLS Setup

#### NGINX SSL Configuration

```nginx
# /etc/nginx/sites-available/navo
server {
    listen 80;
    server_name navo.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name navo.yourdomain.com;

    ssl_certificate /etc/ssl/certs/navo.crt;
    ssl_certificate_key /etc/ssl/private/navo.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to NAVO
sudo ufw deny 6379/tcp  # Block direct access to Redis
sudo ufw enable
```

### API Security

#### Rate Limiting

```python
# Custom rate limiting configuration
rate_limiting:
  enabled: true
  storage_uri: "redis://redis:6379"
  strategies:
    - name: "per_user"
      requests: 100
      window: 3600  # 1 hour
    - name: "per_ip"
      requests: 1000
      window: 3600
    - name: "burst"
      requests: 10
      window: 60
```

#### Authentication

```yaml
# JWT authentication
authentication:
  enabled: true
  jwt_secret: "${JWT_SECRET}"
  token_expiry_hours: 8
  refresh_token_expiry_days: 30
  
  # OAuth providers
  oauth:
    microsoft:
      enabled: true
      client_id: "${MICROSOFT_CLIENT_ID}"
      client_secret: "${MICROSOFT_CLIENT_SECRET}"
      tenant_id: "${MICROSOFT_TENANT_ID}"
```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'navo'
    static_configs:
      - targets: ['navo:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboard

Key metrics to monitor:

- **Query Volume**: Requests per second
- **Response Time**: P50, P95, P99 latencies
- **Error Rate**: 4xx and 5xx responses
- **Cache Performance**: Hit rate, eviction rate
- **Integration Health**: API response times
- **Resource Usage**: CPU, memory, disk

### Log Aggregation

#### ELK Stack Configuration

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/navo/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "navo-logs-%{+yyyy.MM.dd}"
```

#### Structured Logging

```python
# NAVO logging configuration
logging:
  version: 1
  formatters:
    json:
      format: '%(asctime)s %(name)s %(levelname)s %(message)s'
      class: pythonjsonlogger.jsonlogger.JsonFormatter
  handlers:
    file:
      class: logging.handlers.RotatingFileHandler
      filename: /var/log/navo/navo.log
      maxBytes: 10485760  # 10MB
      backupCount: 5
      formatter: json
  loggers:
    navo:
      level: INFO
      handlers: [file]
```

## Backup and Recovery

### Data Backup Strategy

#### Redis Backup

```bash
# Automated Redis backup script
#!/bin/bash
BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
redis-cli BGSAVE
sleep 10
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "redis_backup_*.rdb" -mtime +7 -delete
```

#### Configuration Backup

```bash
# Backup configuration and secrets
#!/bin/bash
BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup archive
tar -czf $BACKUP_DIR/navo_config_$DATE.tar.gz \
  /home/navo/navo/config/ \
  /home/navo/navo/.env \
  /etc/nginx/sites-available/navo

# Cleanup old backups
find $BACKUP_DIR -name "navo_config_*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery

#### Recovery Procedures

1. **Service Recovery**
   ```bash
   # Restore from backup
   sudo systemctl stop navo
   cd /home/navo && rm -rf navo
   git clone <repository-url> navo
   tar -xzf /backup/config/navo_config_latest.tar.gz
   sudo systemctl start navo
   ```

2. **Data Recovery**
   ```bash
   # Restore Redis data
   sudo systemctl stop redis
   cp /backup/redis/redis_backup_latest.rdb /var/lib/redis/dump.rdb
   sudo chown redis:redis /var/lib/redis/dump.rdb
   sudo systemctl start redis
   ```

## Performance Optimization

### Application Tuning

#### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 120
keepalive = 5
```

#### Redis Optimization

```conf
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 0
```

### Infrastructure Scaling

#### Horizontal Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: navo-hpa
  namespace: navo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: navo
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Troubleshooting

### Common Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats navo
kubectl top pods -n navo

# Optimize cache settings
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Slow Response Times

```bash
# Check integration latency
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/api/v1/health

# Monitor query processing
tail -f /var/log/navo/navo.log | grep "processing_time"
```

#### Integration Failures

```bash
# Test Confluence connectivity
curl -u username:token https://yourcompany.atlassian.net/rest/api/content

# Test SharePoint connectivity
curl -H "Authorization: Bearer $TOKEN" \
  https://graph.microsoft.com/v1.0/sites
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/api/v1/health

# Integration status
curl http://localhost:8000/api/v1/integrations/status

# Cache statistics
curl http://localhost:8000/api/v1/cache/stats

# Metrics endpoint
curl http://localhost:8000/metrics
```

This deployment guide provides comprehensive instructions for deploying NAVO in various environments, from development to enterprise production systems.

