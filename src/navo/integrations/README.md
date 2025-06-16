# NAVO Integrations

This directory contains all external system integrations that enable NAVO to connect with various knowledge sources and enterprise systems.

## Directory Structure

```
integrations/
├── __init__.py                 # Package initialization
├── base.py                     # Base integration interface
├── openai/                     # Enterprise GPT integration
│   ├── __init__.py
│   └── enterprise_client.py    # OpenAI Enterprise client
├── confluence/                 # Atlassian Confluence integration
│   ├── __init__.py
│   └── client.py               # Confluence API client
└── sharepoint/                 # Microsoft SharePoint integration
    ├── __init__.py
    └── client.py               # SharePoint Graph API client
```

## Integration Overview

### Base Integration (`base.py`)
Defines the common interface that all integrations must implement, ensuring consistency and interoperability across different knowledge sources.

**Key Interface Methods:**
- `search()` - Search for content within the system
- `get_content()` - Retrieve specific content by ID
- `check_permissions()` - Validate user access to content
- `get_metadata()` - Extract content metadata
- `health_check()` - Verify integration health

### Enterprise GPT Integration (`openai/enterprise_client.py`)
Secure integration with OpenAI Enterprise that provides unlimited GPT-4o access with enterprise-grade security and compliance.

**Features:**
- Unlimited GPT-4o API access
- Enterprise security and compliance
- Custom prompt engineering for knowledge discovery
- Response optimization and caching
- Cost monitoring and usage analytics
- Automatic retry and error handling

**Key Methods:**
- `generate_response()` - Generate AI responses
- `analyze_query()` - Query intent analysis
- `summarize_content()` - Content summarization
- `get_usage_stats()` - Usage analytics

### Confluence Integration (`confluence/client.py`)
Deep integration with Atlassian Confluence that provides comprehensive access to organizational knowledge stored in Confluence spaces.

**Features:**
- Space-aware search with permission inheritance
- Content freshness tracking and metadata extraction
- Attachment handling and link resolution
- Real-time content updates and notifications
- Advanced search with CQL (Confluence Query Language)
- Bulk content operations and synchronization

**Key Methods:**
- `search_content()` - Search across Confluence spaces
- `get_page_content()` - Retrieve page content and metadata
- `get_space_permissions()` - Check space-level permissions
- `track_content_freshness()` - Monitor content updates
- `resolve_links()` - Resolve internal Confluence links

### SharePoint Integration (`sharepoint/client.py`)
Microsoft Graph API integration that provides seamless access to SharePoint documents and libraries with full permission inheritance.

**Features:**
- Site and library traversal with access control
- Document metadata and content extraction
- Version tracking and collaboration features
- Teams integration for seamless workflow
- Advanced search across SharePoint content
- Real-time change notifications

**Key Methods:**
- `search_documents()` - Search SharePoint documents
- `get_document_content()` - Retrieve document content
- `get_site_permissions()` - Check site-level permissions
- `track_document_versions()` - Monitor document changes
- `get_collaboration_data()` - Extract collaboration metadata

## Integration Configuration

### Enterprise GPT Configuration
```yaml
# config/config.yaml
integrations:
  openai:
    api_key: "${ENTERPRISE_GPT_API_KEY}"
    organization_id: "${ORGANIZATION_ID}"
    model: "gpt-4o"
    max_tokens: 4000
    temperature: 0.1
    timeout: 30
    retry_attempts: 3
    enable_caching: true
    cache_ttl: 3600
```

### Confluence Configuration
```yaml
integrations:
  confluence:
    base_url: "${CONFLUENCE_BASE_URL}"
    username: "${CONFLUENCE_USERNAME}"
    api_token: "${CONFLUENCE_API_TOKEN}"
    spaces: ["ENG", "DOCS", "RUNBOOKS", "ONBOARDING"]
    max_results: 50
    include_attachments: true
    track_freshness: true
    freshness_threshold: 90  # days
```

### SharePoint Configuration
```yaml
integrations:
  sharepoint:
    tenant_id: "${SHAREPOINT_TENANT_ID}"
    client_id: "${SHAREPOINT_CLIENT_ID}"
    client_secret: "${SHAREPOINT_CLIENT_SECRET}"
    sites: ["engineering", "documentation", "procedures"]
    max_results: 50
    include_metadata: true
    track_versions: true
```

## Authentication and Security

### Enterprise GPT Authentication
- **API Key**: Secure API key management with rotation support
- **Organization ID**: Enterprise organization identification
- **Rate Limiting**: Automatic rate limit handling and backoff
- **Data Privacy**: No training on customer data guarantee

### Confluence Authentication
- **API Token**: Personal access token or app password
- **Basic Auth**: Username and API token combination
- **Permission Inheritance**: Respects Confluence space and page permissions
- **Audit Logging**: Complete access audit trail

### SharePoint Authentication
- **OAuth 2.0**: Microsoft Graph API authentication
- **Client Credentials**: Service-to-service authentication
- **Permission Inheritance**: Respects SharePoint site and document permissions
- **Conditional Access**: Support for conditional access policies

## Error Handling and Resilience

### Common Error Patterns
All integrations implement consistent error handling:

```python
from navo.integrations.base import IntegrationError, AuthenticationError, PermissionError

try:
    results = await integration.search(query, context)
except AuthenticationError:
    # Handle authentication failures
    await integration.refresh_credentials()
except PermissionError:
    # Handle permission denials
    logger.warning(f"Permission denied for user {user_id}")
except IntegrationError as e:
    # Handle general integration errors
    logger.error(f"Integration error: {e}")
```

### Retry and Backoff
- **Exponential Backoff**: Automatic retry with exponential backoff
- **Circuit Breaker**: Prevent cascading failures
- **Fallback Mechanisms**: Graceful degradation when integrations fail
- **Health Monitoring**: Continuous health checks and alerting

## Performance Optimization

### Caching Strategies
- **Response Caching**: Cache API responses to reduce latency
- **Content Caching**: Cache processed content for faster retrieval
- **Permission Caching**: Cache permission checks to improve performance
- **Metadata Caching**: Cache document metadata for quick access

### Batch Operations
- **Bulk Search**: Process multiple queries in batches
- **Parallel Requests**: Concurrent API calls where possible
- **Connection Pooling**: Reuse HTTP connections for efficiency
- **Request Optimization**: Minimize API calls through intelligent batching

## Integration Testing

### Unit Tests
```bash
# Test individual integrations
pytest tests/unit/integrations/test_confluence_client.py -v
pytest tests/unit/integrations/test_sharepoint_client.py -v
pytest tests/unit/integrations/test_enterprise_gpt_client.py -v
```

### Integration Tests
```bash
# Test with real APIs (requires credentials)
pytest tests/integration/integrations/ -v --integration

# Test specific integration
pytest tests/integration/integrations/test_confluence_integration.py -v
```

### Mock Testing
```python
# Example mock test
from unittest.mock import AsyncMock, patch
from navo.integrations.confluence.client import ConfluenceClient

@patch('navo.integrations.confluence.client.aiohttp.ClientSession')
async def test_confluence_search(mock_session):
    mock_response = AsyncMock()
    mock_response.json.return_value = {"results": []}
    mock_session.return_value.__aenter__.return_value.get.return_value = mock_response
    
    client = ConfluenceClient(config)
    results = await client.search("test query")
    
    assert isinstance(results, list)
```

## Adding New Integrations

### Step 1: Implement Base Interface
```python
from navo.integrations.base import BaseIntegration

class NewIntegration(BaseIntegration):
    def __init__(self, config):
        super().__init__(config)
        self.client = NewAPIClient(config)
    
    async def search(self, query, context=None):
        # Implement search functionality
        pass
    
    async def get_content(self, content_id):
        # Implement content retrieval
        pass
    
    async def check_permissions(self, user_id, content_id):
        # Implement permission checking
        pass
```

### Step 2: Add Configuration
```yaml
integrations:
  new_system:
    api_url: "${NEW_SYSTEM_API_URL}"
    api_key: "${NEW_SYSTEM_API_KEY}"
    # Add system-specific configuration
```

### Step 3: Register Integration
```python
# In navo/integrations/__init__.py
from .new_system.client import NewIntegration

AVAILABLE_INTEGRATIONS = {
    'confluence': ConfluenceClient,
    'sharepoint': SharePointClient,
    'enterprise_gpt': EnterpriseGPTClient,
    'new_system': NewIntegration,
}
```

### Step 4: Add Tests
```python
# tests/unit/integrations/test_new_integration.py
import pytest
from navo.integrations.new_system.client import NewIntegration

@pytest.fixture
def new_integration():
    config = {"api_url": "https://api.example.com", "api_key": "test"}
    return NewIntegration(config)

async def test_search(new_integration):
    results = await new_integration.search("test query")
    assert isinstance(results, list)
```

## Monitoring and Observability

### Metrics Collection
Each integration provides detailed metrics:

```python
# Integration metrics
integration_metrics = {
    'requests_total': 1250,
    'requests_successful': 1198,
    'requests_failed': 52,
    'average_response_time': 145,  # milliseconds
    'cache_hit_rate': 0.73,
    'error_rate': 0.042
}
```

### Health Checks
```python
async def health_check():
    """Check integration health"""
    try:
        response = await self.client.get('/health')
        return {
            'status': 'healthy',
            'response_time': response.elapsed.total_seconds(),
            'last_check': datetime.utcnow()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'last_check': datetime.utcnow()
        }
```

### Alerting
- **Response Time Alerts**: Alert when response times exceed thresholds
- **Error Rate Alerts**: Alert when error rates spike
- **Authentication Alerts**: Alert on authentication failures
- **Quota Alerts**: Alert when approaching API quotas

## Best Practices

### Security
- Store credentials securely using environment variables
- Implement proper authentication and authorization
- Use HTTPS for all API communications
- Regularly rotate API keys and tokens
- Audit all access and operations

### Performance
- Implement appropriate caching strategies
- Use connection pooling for HTTP clients
- Batch requests where possible
- Monitor and optimize API usage
- Implement circuit breakers for resilience

### Reliability
- Handle all error conditions gracefully
- Implement retry logic with exponential backoff
- Provide fallback mechanisms
- Monitor integration health continuously
- Log all operations for debugging

The integrations directory provides the foundation for NAVO's multi-source knowledge discovery capabilities, enabling seamless access to enterprise knowledge systems while maintaining security, performance, and reliability standards.

