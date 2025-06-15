# NAVO - Navigate + Ops
## "NAVO knows where it's written."

**Version:** 2.0.0  
**Built for:** Enterprise GPT Integration  
**Architecture:** Hybrid Cloud-Native  

## 🚀 Enterprise Use Case

NAVO was developed with large-scale engineering teams in mind, where internal feedback and sprint challenges helped shape its capabilities for Confluence and SharePoint integration.

---

## 🎯 The Engineering Problem

Engineering teams within enterprise workstreams frequently lose time searching for documentation across multiple systems—primarily Confluence and SharePoint. Whether it's retry logic for synthetic scripts, VuGen vs. TruClient protocol notes, or onboarding SOPs, the challenge isn't that information doesn't exist—**it's that it's hard to find, inconsistently tagged, and siloed across platforms.**

### The Real Cost
- **Frequent Microsoft Teams interruptions** - "Where's the retry logic for QLAB02?"
- **Repeated context-switching** during sprint execution
- **Growing reliance on "tribal knowledge"** instead of documented processes
- **Engineers pausing development work** to track down documents
- **Waiting for teammates** to share links and explanations

This friction adds up—**delaying delivery, onboarding, and team efficiency.**

---

## 🚀 The NAVO Solution

**NAVO (Navigate + Ops)** is an AI-powered knowledge agent designed to make documentation accessible through natural language conversations directly within MS Teams. Unlike a basic chatbot, NAVO uses Enterprise GPT to understand context-rich engineering queries and return summarized, relevant documentation pulled from both Confluence and SharePoint.

### Real Engineering Queries NAVO Handles
```
"Where's the retry logic for QLAB02 scripts?"
"What's the API versioning standard?"
"Do we have a runbook for production incidents?"
"How do I configure VuGen vs. TruClient protocols?"
"What's our onboarding SOP for new engineers?"
"Show me the latest synthetic monitoring setup docs"
```

### NAVO's Intelligent Response
- **Direct links** to relevant Confluence pages and SharePoint documents
- **Summarized content** with key information extracted
- **Freshness ratings** - "updated 2 days ago" vs "updated 6 months ago"
- **Content flags** - automatically identifies outdated or conflicting information
- **Follow-up suggestions** - "You might also need the VuGen troubleshooting guide"

**NAVO brings knowledge to where work happens** - transforming documentation from a passive archive into an active partner in daily engineering operations.

---

## 🏗️ Architecture Philosophy

### NAVO vs. Traditional Knowledge Systems

**Traditional Approach:**
- Static knowledge bases with manual categorization
- Search-based discovery requiring exact keywords
- Separate systems for different document types
- Manual maintenance and updates

**NAVO's Hybrid Approach:**
- **AI-powered understanding** of natural language queries
- **Context-aware responses** that understand enterprise terminology and project codes
- **Multi-source integration** - seamlessly searches Confluence and SharePoint
- **Intelligent content management** - automatic freshness tracking and outdated content flagging
- **Sprint-aware context** - understands current project contexts and workstream needs

### Core Architecture Principles

1. **Knowledge Where Work Happens** - Integrate with Teams, not replace it
2. **Context-Rich Understanding** - Recognize enterprise systems, protocols, and project codes
3. **Source Attribution** - Always cite sources with confidence and freshness ratings
4. **Permission Respect** - Honor existing access controls from source systems
5. **Continuous Learning** - Improve responses based on usage patterns and feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- Enterprise GPT API access
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

## 🔧 Enterprise Engineering Features

### Sprint-Aware Intelligence
- **Project Code Recognition** - Understands project codes, testing frameworks, and enterprise systems
- **Workstream Context** - Recognizes engineering, quality, operations, and onboarding contexts
- **Current Sprint Awareness** - Provides relevant information for active development work
- **Protocol Documentation** - Easy access to VuGen vs. TruClient differences and configurations

### Content Intelligence
- **Freshness Tracking** - Monitors when documentation was last updated
- **Outdated Content Flagging** - Automatically identifies content older than 90 days
- **Conflicting Information Detection** - Flags when multiple sources provide different answers
- **Missing Documentation Alerts** - Identifies gaps in knowledge coverage

### Enterprise Integration Ready
- **Teams Adaptive Cards** - Rich, interactive responses within Microsoft Teams
- **Enterprise SSO** - Seamless authentication with existing enterprise credentials
- **Confluence Spaces** - Pre-configured for engineering, documentation, runbooks, and onboarding spaces
- **SharePoint Sites** - Integrated with enterprise engineering SharePoint sites
- **Audit Logging** - Enterprise-grade logging for compliance and monitoring

## 🎯 Why NAVO vs. Traditional Knowledge Systems?

### The JUNO Problem
Traditional knowledge management systems like JUNO work well for **structured, categorized information** but fall short for **dynamic engineering workflows**:

- **Static Organization** - Information is filed away in rigid categories
- **Search Dependency** - Requires knowing exact keywords or document titles  
- **Context Blindness** - Doesn't understand current sprint work or project contexts
- **Manual Maintenance** - Relies on humans to keep information current and organized
- **Siloed Access** - Each system (Confluence, SharePoint, etc.) requires separate searches

### NAVO's Engineering-First Approach

**NAVO is built specifically for how enterprise engineers actually work:**

1. **Conversational Discovery** - Ask questions in natural language, get intelligent answers
2. **Context Awareness** - Understands your current project and provides relevant documentation
3. **Multi-Source Intelligence** - Searches Confluence and SharePoint simultaneously
4. **Freshness Intelligence** - Automatically flags outdated content and suggests current alternatives
5. **Teams Integration** - Brings answers directly into your workflow, no context switching

### Real-World Impact

**Before NAVO:**
```
Engineer: "Hey team, where's the retry logic for QLAB02?"
[5 minutes of Teams back-and-forth]
[Someone shares a link to outdated documentation]
[Another 10 minutes finding the current version]
```

**With NAVO:**
```
Engineer: "@NAVO where's the retry logic for QLAB02?"
NAVO: "Found current retry logic documentation for QLAB02:
• Retry Configuration Guide (updated 2 days ago)
• Implementation examples in synthetic_runner.py
• VuGen vs TruClient retry differences
[Direct links + summary + follow-up suggestions]"
```

**Result: 15 minutes saved per query, reduced Teams interruptions, always current information.**

---

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
  api_key: "${ENTERPRISE_GPT_API_KEY}"
  organization_id: "${ENTERPRISE_ORGANIZATION_ID}"
  default_model: "gpt-4o"

integrations:
  confluence:
    enabled: true
    base_url: "${CONFLUENCE_BASE_URL}"
    username: "${CONFLUENCE_USERNAME}"
    api_token: "${CONFLUENCE_API_TOKEN}"
    # Enterprise spaces for engineering teams
    spaces_to_sync:
      - "ENG"        # Engineering documentation
      - "DOCS"       # General documentation  
      - "RUNBOOKS"   # Operational runbooks
      - "ONBOARD"    # Onboarding materials
  
  sharepoint:
    enabled: true
    tenant_id: "${SHAREPOINT_TENANT_ID}"
    client_id: "${SHAREPOINT_CLIENT_ID}"
    client_secret: "${SHAREPOINT_CLIENT_SECRET}"
    # Enterprise engineering sites
    sites:
      - "https://yourcompany.sharepoint.com/sites/Engineering"
      - "https://yourcompany.sharepoint.com/sites/QualityLab"
      - "https://yourcompany.sharepoint.com/sites/Documentation"

query_processing:
  # Enterprise specific entities
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
# Required - Enterprise GPT
ENTERPRISE_GPT_API_KEY=your_enterprise_gpt_api_key
ENTERPRISE_ORGANIZATION_ID=your_organization_id

# Confluence
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
CONFLUENCE_USERNAME=your_username
CONFLUENCE_API_TOKEN=your_api_token

# SharePoint
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret
```

### Infrastructure
```bash
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
      "url": "https://yourcompany.atlassian.net/wiki/spaces/ENG/pages/123456/Synthetic+Scripts",
      "relevance_score": 0.95,
      "freshness": "updated_2_days_ago",
      "freshness_score": 0.9
    },
    {
      "title": "Retry Patterns and Best Practices",
      "source": "confluence", 
      "space": "ENG",
      "url": "https://yourcompany.atlassian.net/wiki/spaces/ENG/pages/789012/Retry+Patterns",
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

MIT License

Copyright (c) 2025 mj3b

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: Create an issue in the repository
- **Email**: navo-support@yourcompany.com

---

**NAVO knows where it's written.** ™

*Navigate your knowledge, optimize your operations.*

