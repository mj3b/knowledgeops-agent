# NAVO - Navigate + Ops
## "NAVO knows where it's written."

**Version:** 2.0.0  
**Built with:** T-Mobile Enterprise GPT Integration  
**Architecture:** Hybrid Cloud-Native  

## The Problem We Solve

Engineering teams within workstreams frequently lose time searching for documentation across multiple systems—primarily Confluence and SharePoint. Whether it's retry logic for synthetic scripts, VuGen vs. TruClient protocol notes, or onboarding SOPs, the challenge isn't that information doesn't exist—it's that it's hard to find, inconsistently tagged, and siloed across platforms.

This results in frequent Microsoft Teams interruptions, repeated context-switching, and growing reliance on "tribal knowledge." The productivity cost becomes even more apparent during sprint execution, where engineers pause development work to track down documents or wait for teammates to share links.

## The NAVO Solution

NAVO is an AI-powered knowledge agent designed to make documentation accessible through natural language conversations directly within MS Teams. Unlike a basic chatbot, NAVO uses advanced GPT-based models to understand context-rich engineering queries and return summarized, relevant documentation pulled from both Confluence and SharePoint.

**Real Engineering Queries:**
- "Where's the retry logic for QLAB02 scripts?"
- "What's the API versioning standard?"
- "Do we have a runbook for production incidents?"
- "How do I configure VuGen vs. TruClient protocols?"
- "What's our onboarding SOP for new engineers?"

NAVO responds with direct links, summaries, freshness ratings, and even flags outdated content—reducing noise and repetitive pings while promoting cleaner documentation practices.

**NAVO brings knowledge to where work happens.**

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- OpenAI Enterprise API access
- Confluence and/or SharePoint access (optional)

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd navo
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start Redis** (if not already running)
   ```bash
   redis-server
   ```

4. **Run NAVO**
   ```bash
   python main.py
   ```

5. **Access the Interface**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

## 🏗️ Architecture

NAVO implements a hybrid architecture that leverages:

### Core Components
- **NAVO Engine**: Central orchestrator for knowledge discovery
- **OpenAI Enterprise Client**: Unlimited GPT-4o access with enterprise security
- **Query Processor**: Intelligent query understanding and intent classification
- **Response Generator**: Context-aware response generation with source attribution
- **Cache Manager**: Multi-level caching for optimal performance
- **Permission Manager**: Fine-grained access control across integrated systems

### Integration Layer
- **Confluence Integration**: Deep integration with Atlassian Confluence
- **SharePoint Integration**: Microsoft Graph API integration for SharePoint
- **Extensible Framework**: Easy addition of new knowledge sources

### API & Web Interface
- **FastAPI Backend**: High-performance async API
- **Modern Web UI**: Responsive chat interface with real-time updates
- **RESTful APIs**: Comprehensive API for integration and automation

## 🔧 Features

### Enterprise AI Capabilities
- **T-Mobile Enterprise GPT Access** - Secure, compliant AI processing
- **Context-Rich Query Understanding** - Understands engineering terminology and project codes
- **Sprint-Aware Responses** - Recognizes project contexts like QLAB02, VuGen, TruClient
- **Source Attribution** - Always cite sources with freshness ratings
- **Outdated Content Detection** - Flags stale documentation automatically
- **Teams Integration Ready** - Built for Microsoft Teams adaptive cards

### Knowledge Integration
- **Multi-Source Search** - Confluence, SharePoint, and extensible to more
- **Permission Respect** - Honor source system permissions and access controls
- **Real-time Sync** - Keep knowledge base current with documentation changes
- **Intelligent Caching** - Optimize performance and reduce search latency
- **Content Freshness Tracking** - Monitor and flag outdated documentation

### Engineering Productivity Features
- **Sprint Context Awareness** - Understands project codes and workstream terminology
- **Runbook Discovery** - Quick access to operational procedures and SOPs
- **Protocol Documentation** - Easy access to VuGen, TruClient, and testing protocols
- **Onboarding Acceleration** - Streamlined access to new engineer resources
- **Tribal Knowledge Capture** - Reduces reliance on person-to-person knowledge transfer

## 📚 Documentation

### Core Documentation
- [Architecture Guide](docs/ARCHITECTURE.md) - Technical architecture and design patterns
- [API Documentation](docs/API.md) - Complete API reference with examples
- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions

### Integration Guides
- [Confluence Setup](docs/integrations/CONFLUENCE.md) - Confluence integration setup
- [SharePoint Setup](docs/integrations/SHAREPOINT.md) - SharePoint integration setup
- [OpenAI Enterprise](docs/integrations/OPENAI.md) - OpenAI Enterprise configuration

### Operations
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Monitoring](docs/MONITORING.md) - Performance monitoring and alerting
- [Security](docs/SECURITY.md) - Security best practices

## 🔧 Configuration

### Basic Configuration

Edit `config/config.yaml` or use environment variables:

```yaml
openai:
  api_key: "${TMOBILE_ENTERPRISE_GPT_API_KEY}"
  organization_id: "${TMOBILE_ORGANIZATION_ID}"
  default_model: "gpt-4o"

integrations:
  confluence:
    enabled: true
    base_url: "${CONFLUENCE_BASE_URL}"
    username: "${CONFLUENCE_USERNAME}"
    api_token: "${CONFLUENCE_API_TOKEN}"
    # T-Mobile specific spaces
    spaces_to_sync:
      - "ENG"      # Engineering documentation
      - "QLAB"     # Quality lab procedures
      - "RUNBOOKS" # Operational runbooks
      - "ONBOARD"  # Onboarding materials
  
  sharepoint:
    enabled: true
    tenant_id: "${SHAREPOINT_TENANT_ID}"
    client_id: "${SHAREPOINT_CLIENT_ID}"
    client_secret: "${SHAREPOINT_CLIENT_SECRET}"
    # T-Mobile engineering sites
    site_urls:
      - "https://tmobile.sharepoint.com/sites/Engineering"
      - "https://tmobile.sharepoint.com/sites/QualityLab"
      - "https://tmobile.sharepoint.com/sites/Documentation"

query_processing:
  # T-Mobile specific entities
  organizational_entities:
    systems:
      - "qlab02"
      - "vugen"
      - "truclient"
      - "confluence"
      - "sharepoint"
    protocols:
      - "vugen"
      - "truclient"
      - "synthetic"
      - "loadrunner"
    workstreams:
      - "engineering"
      - "quality"
      - "operations"
      - "onboarding"
```

### Environment Variables

```bash
# Required - T-Mobile Enterprise GPT
TMOBILE_ENTERPRISE_GPT_API_KEY=your_enterprise_gpt_api_key
TMOBILE_ORGANIZATION_ID=your_organization_id

# T-Mobile Confluence
CONFLUENCE_BASE_URL=https://tmobile.atlassian.net
CONFLUENCE_USERNAME=your_service_account
CONFLUENCE_API_TOKEN=your_api_token

# T-Mobile SharePoint
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret

# Infrastructure
REDIS_URL=redis://localhost:6379
```

## 🚀 API Usage

### Query Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Where is the retry logic for QLAB02 synthetic scripts?",
    "user_id": "engineer123",
    "context": {"workstream": "quality_lab", "sprint": "current"},
    "filters": {"source": "confluence", "space": "QLAB"}
  }'
```

### Response Format

```json
{
  "query_id": "navo_1703123456789",
  "answer": "The retry logic for QLAB02 synthetic scripts is documented in the Quality Lab Confluence space. Here's what I found:\n\n**Retry Configuration:**\n- Default retry count: 3 attempts\n- Backoff strategy: Exponential (2s, 4s, 8s)\n- Timeout per attempt: 30 seconds\n\n**Implementation:**\nThe retry logic is implemented in the `synthetic_runner.py` module using the `@retry` decorator...",
  "sources": [
    {
      "title": "QLAB02 Synthetic Script Configuration",
      "source": "confluence",
      "space": "QLAB",
      "url": "https://tmobile.atlassian.net/wiki/spaces/QLAB/pages/123456/Synthetic+Scripts",
      "relevance_score": 0.95,
      "freshness": "updated_2_days_ago",
      "freshness_score": 0.9
    },
    {
      "title": "Retry Patterns and Best Practices",
      "source": "confluence", 
      "space": "ENG",
      "url": "https://tmobile.atlassian.net/wiki/spaces/ENG/pages/789012/Retry+Patterns",
      "relevance_score": 0.87,
      "freshness": "updated_1_week_ago",
      "freshness_score": 0.8
    }
  ],
  "confidence": 0.92,
  "processing_time": 1.23,
  "follow_up_questions": [
    "How do I configure custom retry parameters for QLAB02?",
    "What are the VuGen vs TruClient differences for retry handling?",
    "Are there any known issues with retry logic in the current sprint?"
  ],
  "content_flags": {
    "outdated_content": false,
    "missing_documentation": false,
    "conflicting_information": false
  },
  "timestamp": "2024-12-21T10:30:45Z"
}
```

## 🛠️ Development

### Project Structure

```
navo/
├── src/navo/
│   ├── core/                 # Core NAVO engine
│   ├── integrations/         # Integration modules
│   ├── api/                  # FastAPI application
│   └── web/                  # Web interface
├── config/                   # Configuration files
├── docs/                     # Documentation
├── tests/                    # Test suite
├── main.py                   # Application entry point
└── requirements.txt          # Dependencies
```

### Running Tests

```bash
pytest tests/ -v --cov=src/navo
```

### Development Mode

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
python main.py --reload

# Run tests with coverage
pytest --cov=src/navo --cov-report=html
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f navo

# Stop services
docker-compose down
```

### Environment Configuration

Create `.env` file with your configuration:

```bash
OPENAI_API_KEY=your_key_here
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
# ... other variables
```

## 📊 Monitoring

### Health Checks

```bash
# System health
curl http://localhost:8000/api/v1/health

# Integration status
curl http://localhost:8000/api/v1/integrations/status

# Performance metrics
curl http://localhost:8000/api/v1/metrics
```

### Prometheus Metrics

NAVO exposes Prometheus metrics at `/metrics`:

- `navo_queries_total` - Total queries processed
- `navo_query_duration_seconds` - Query processing time
- `navo_cache_hits_total` - Cache hit/miss statistics
- `navo_integration_requests_total` - Integration API calls

## 🔒 Security

### Authentication

NAVO supports multiple authentication methods:

- **API Keys** - For service-to-service communication
- **JWT Tokens** - For user authentication
- **OAuth 2.0** - Microsoft/Google SSO integration

### Permissions

- **Source System Permissions** - Respects Confluence/SharePoint permissions
- **Role-Based Access** - Admin, user, and custom roles
- **Audit Logging** - All queries and actions are logged

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

Copyright (c) 2025 NAVO Team. All rights reserved.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: Create an issue in the repository
- **Email**: navo-support@tmobile.com

---

**NAVO knows where it's written.** ™

*Navigate your knowledge, optimize your operations.*

