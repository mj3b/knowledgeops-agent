# KnowledgeOps Agent - Enterprise Deployment Guide

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.enterprise .env

# Edit configuration with your values
nano .env
```

### 2. Docker Deployment (Recommended)
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f knowledgeops-agent
```

### 3. Manual Deployment
```bash
# Install dependencies
pip install -r requirements_enterprise.txt

# Set environment variables
export CONFLUENCE_BASE_URL="https://your-domain.atlassian.net"
export CONFLUENCE_USERNAME="your-email@company.com"
export CONFLUENCE_API_TOKEN="your-api-token"

# Run application
python knowledgeops_app.py
```

## Configuration

### Confluence Setup
1. Generate API token in Atlassian Account Settings
2. Configure spaces to sync in CONFLUENCE_SPACES
3. Test connection: `curl http://localhost:5000/api/health`

### SharePoint Setup
1. Register Azure AD application
2. Grant Microsoft Graph permissions
3. Configure tenant and client credentials
4. Test connection: `curl http://localhost:5000/api/health`

## API Usage

### Search Content
```bash
curl "http://localhost:5000/api/search?q=deployment+procedures&limit=10"
```

### Get Content by ID
```bash
curl "http://localhost:5000/api/content/confluence_12345"
```

### Trigger Sync
```bash
curl -X POST "http://localhost:5000/api/sync" \
  -H "Content-Type: application/json" \
  -d '{"force_full_sync": false}'
```

## Monitoring

- Health Check: http://localhost:5000/api/health
- Metrics: http://localhost:9090 (Prometheus)
- Dashboard: http://localhost:3000 (Grafana)

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Check API tokens and permissions
2. **Sync Failures**: Verify network connectivity and rate limits
3. **Search Issues**: Check embedding model and vector index

### Logs
```bash
# Docker logs
docker-compose logs knowledgeops-agent

# Application logs
tail -f logs/knowledgeops.log
```

## Security

- Use HTTPS in production
- Rotate API tokens regularly
- Implement proper access controls
- Monitor for suspicious activity

## Scaling

- Increase worker processes in docker-compose.yml
- Use external Redis and PostgreSQL for clustering
- Implement load balancing with multiple instances

