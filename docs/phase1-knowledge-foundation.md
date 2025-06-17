# NAVO Phase 1: Knowledge Discovery Foundation

## Overview

Phase 1 establishes the foundational capabilities for enterprise knowledge discovery, providing multi-source search, natural language processing, and source attribution. This phase focuses on delivering immediate value through improved documentation accessibility while establishing the technical foundation for subsequent phases.

## Implementation Timeline

**Duration**: 2 weeks  
**Team Size**: 2-3 engineers  
**Prerequisites**: Enterprise GPT access, Confluence/SharePoint API credentials

## Core Components

### Search Engine Architecture

The search engine provides the core capability for multi-source document retrieval and ranking. Built on Elasticsearch with semantic search capabilities, it supports both keyword and vector-based search methodologies.

**Key Features**:
- Multi-source document indexing
- Hybrid search combining keyword and semantic matching
- Real-time index updates
- Configurable ranking algorithms
- Performance optimization through caching

**Implementation**:
```python
class NAVOSearchEngine:
    def __init__(self, config: SearchConfig):
        self.elasticsearch = Elasticsearch(
            hosts=config.elasticsearch_hosts,
            http_auth=(config.username, config.password),
            use_ssl=True,
            verify_certs=True
        )
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache = Redis(host=config.redis_host, port=config.redis_port)
    
    async def search(self, query: str, sources: List[str] = None) -> SearchResults:
        # Check cache first
        cache_key = self._generate_cache_key(query, sources)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return SearchResults.from_json(cached_result)
        
        # Perform hybrid search
        keyword_results = await self._keyword_search(query, sources)
        semantic_results = await self._semantic_search(query, sources)
        
        # Merge and rank results
        merged_results = self._merge_and_rank(keyword_results, semantic_results)
        
        # Cache results
        await self.cache.setex(cache_key, 3600, merged_results.to_json())
        
        return merged_results
```

### Natural Language Processing Pipeline

The NLP pipeline processes user queries to extract intent, entities, and context, enabling more accurate document retrieval and response generation.

**Processing Steps**:
1. **Query Normalization**: Text cleaning and standardization
2. **Entity Extraction**: Identification of technical terms, project names, and concepts
3. **Intent Classification**: Categorization of query types (how-to, what-is, where-is)
4. **Context Enhancement**: Addition of user and organizational context

**Implementation**:
```python
class QueryProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
    
    async def process_query(self, query: str, user_context: dict) -> ProcessedQuery:
        # Normalize query text
        normalized_query = self._normalize_text(query)
        
        # Extract entities
        entities = await self.entity_extractor.extract(normalized_query)
        
        # Classify intent
        intent = await self.intent_classifier.classify(normalized_query)
        
        # Enhance with context
        enhanced_query = self._enhance_with_context(
            normalized_query, entities, intent, user_context
        )
        
        return ProcessedQuery(
            original=query,
            normalized=normalized_query,
            entities=entities,
            intent=intent,
            enhanced=enhanced_query
        )
```

### Source Attribution System

Every response includes comprehensive source attribution to ensure transparency and enable users to access original documents.

**Attribution Components**:
- Document source and URL
- Last modified timestamp
- Author information (when available)
- Confidence score
- Relevance ranking

### Integration Layer

Phase 1 includes integration with primary knowledge sources through standardized API interfaces.

**Confluence Integration**:
```python
class ConfluenceIntegration:
    def __init__(self, base_url: str, username: str, api_token: str):
        self.client = Confluence(
            url=base_url,
            username=username,
            password=api_token
        )
    
    async def search_content(self, query: str, space_keys: List[str] = None) -> List[Document]:
        cql_query = f'text ~ "{query}"'
        if space_keys:
            cql_query += f' and space in ({",".join(space_keys)})'
        
        results = self.client.cql(cql=cql_query, limit=50)
        return [self._convert_to_document(result) for result in results['results']]
    
    def _convert_to_document(self, confluence_result: dict) -> Document:
        return Document(
            id=confluence_result['content']['id'],
            title=confluence_result['content']['title'],
            url=confluence_result['content']['_links']['webui'],
            content=confluence_result['excerpt'],
            source='confluence',
            last_modified=confluence_result['lastModified'],
            space=confluence_result['content']['space']['name']
        )
```

**SharePoint Integration**:
```python
class SharePointIntegration:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.graph_client = GraphServiceClient(
            credentials=ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        )
    
    async def search_content(self, query: str, site_ids: List[str] = None) -> List[Document]:
        search_request = SearchRequest(
            requests=[
                SearchRequestObject(
                    entity_types=['driveItem'],
                    query=SearchQuery(query_string=query),
                    from_=0,
                    size=50
                )
            ]
        )
        
        results = await self.graph_client.search.query.post(search_request)
        return [self._convert_to_document(hit) for hit in results.value[0].hits_containers[0].hits]
```

## Configuration

### Environment Setup

Phase 1 requires configuration of multiple external services and dependencies.

**Required Environment Variables**:
```bash
# Elasticsearch Configuration
ELASTICSEARCH_HOSTS=https://elasticsearch.company.com:9200
ELASTICSEARCH_USERNAME=navo_user
ELASTICSEARCH_PASSWORD=secure_password

# Redis Configuration
REDIS_HOST=redis.company.com
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Confluence Configuration
CONFLUENCE_BASE_URL=https://company.atlassian.net
CONFLUENCE_USERNAME=navo@company.com
CONFLUENCE_API_TOKEN=confluence_api_token

# SharePoint Configuration
AZURE_TENANT_ID=tenant-id-here
AZURE_CLIENT_ID=client-id-here
AZURE_CLIENT_SECRET=client-secret-here

# Enterprise GPT Configuration
OPENAI_API_KEY=enterprise-gpt-api-key
OPENAI_ORGANIZATION=org-id-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

**Configuration File Structure**:
```yaml
# config/phase1.yaml
search_engine:
  elasticsearch:
    hosts:
      - "https://elasticsearch.company.com:9200"
    auth:
      username: "${ELASTICSEARCH_USERNAME}"
      password: "${ELASTICSEARCH_PASSWORD}"
    ssl:
      verify_certs: true
      ca_certs: "/path/to/ca.pem"
  
  semantic_search:
    model: "all-MiniLM-L6-v2"
    similarity_threshold: 0.7
    max_results: 50
  
  caching:
    redis:
      host: "${REDIS_HOST}"
      port: 6379
      password: "${REDIS_PASSWORD}"
    ttl: 3600  # 1 hour

integrations:
  confluence:
    base_url: "${CONFLUENCE_BASE_URL}"
    username: "${CONFLUENCE_USERNAME}"
    api_token: "${CONFLUENCE_API_TOKEN}"
    spaces:
      - "ENG"  # Engineering space
      - "DOC"  # Documentation space
      - "OPS"  # Operations space
  
  sharepoint:
    tenant_id: "${AZURE_TENANT_ID}"
    client_id: "${AZURE_CLIENT_ID}"
    client_secret: "${AZURE_CLIENT_SECRET}"
    sites:
      - "engineering"
      - "documentation"
      - "operations"

nlp:
  spacy_model: "en_core_web_sm"
  entity_types:
    - "PERSON"
    - "ORG"
    - "PRODUCT"
    - "TECHNOLOGY"
  
performance:
  max_concurrent_requests: 100
  request_timeout: 30
  cache_size: 1000
```

## Deployment Guide

### Local Development Setup

**Prerequisites**:
- Python 3.11+
- Docker and Docker Compose
- Access to enterprise systems (Confluence, SharePoint)

**Setup Steps**:
```bash
# Clone repository
git clone https://github.com/company/navo.git
cd navo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start infrastructure services
docker-compose up -d elasticsearch redis

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database and indices
python scripts/init_phase1.py

# Start development server
uvicorn src.navo.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

**Docker Deployment**:
```dockerfile
# Dockerfile.phase1
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash navo
USER navo

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "src.navo.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Kubernetes Deployment**:
```yaml
# k8s/phase1-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: navo-phase1
  labels:
    app: navo
    phase: "1"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: navo
      phase: "1"
  template:
    metadata:
      labels:
        app: navo
        phase: "1"
    spec:
      containers:
      - name: navo-phase1
        image: company/navo:phase1-latest
        ports:
        - containerPort: 8000
        env:
        - name: ELASTICSEARCH_HOSTS
          valueFrom:
            secretKeyRef:
              name: navo-secrets
              key: elasticsearch-hosts
        - name: ELASTICSEARCH_USERNAME
          valueFrom:
            secretKeyRef:
              name: navo-secrets
              key: elasticsearch-username
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## API Reference

### Search Endpoint

**POST /api/v1/search**

Search across configured knowledge sources using natural language queries.

**Request**:
```json
{
  "query": "What is the retry logic for project automation?",
  "sources": ["confluence", "sharepoint"],
  "max_results": 10,
  "include_content": true
}
```

**Response**:
```json
{
  "query_id": "uuid-here",
  "query": "What is the retry logic for project automation?",
  "results": [
    {
      "id": "doc-123",
      "title": "Project Automation Guide",
      "url": "https://confluence.company.com/pages/123",
      "source": "confluence",
      "confidence": 0.94,
      "relevance_score": 0.89,
      "last_modified": "2024-03-15T10:30:00Z",
      "excerpt": "The retry logic for project automation is based on exponential backoff...",
      "metadata": {
        "space": "Engineering",
        "author": "john.doe@company.com",
        "page_type": "documentation"
      }
    }
  ],
  "total_results": 15,
  "search_time_ms": 127,
  "sources_searched": ["confluence", "sharepoint"]
}
```

### Health Check Endpoints

**GET /health**
Returns overall system health status.

**GET /ready**
Returns readiness status for load balancer health checks.

**GET /metrics**
Prometheus metrics endpoint for monitoring.

## Testing Strategy

### Unit Tests

Comprehensive unit tests for all core components with >90% code coverage.

```python
# tests/test_search_engine.py
import pytest
from src.navo.core.search_engine import NAVOSearchEngine

class TestSearchEngine:
    @pytest.fixture
    def search_engine(self):
        config = SearchConfig(
            elasticsearch_hosts=["http://localhost:9200"],
            redis_host="localhost"
        )
        return NAVOSearchEngine(config)
    
    @pytest.mark.asyncio
    async def test_search_returns_results(self, search_engine):
        query = "test query"
        results = await search_engine.search(query)
        
        assert isinstance(results, SearchResults)
        assert len(results.documents) > 0
        assert all(doc.confidence > 0 for doc in results.documents)
    
    @pytest.mark.asyncio
    async def test_search_caching(self, search_engine):
        query = "cached query"
        
        # First search
        results1 = await search_engine.search(query)
        
        # Second search should use cache
        results2 = await search_engine.search(query)
        
        assert results1.query_id == results2.query_id
        assert results2.from_cache is True
```

### Integration Tests

End-to-end tests validating integration with external services.

```python
# tests/integration/test_confluence_integration.py
import pytest
from src.navo.integrations.confluence import ConfluenceIntegration

class TestConfluenceIntegration:
    @pytest.fixture
    def confluence_client(self):
        return ConfluenceIntegration(
            base_url=os.getenv("TEST_CONFLUENCE_URL"),
            username=os.getenv("TEST_CONFLUENCE_USERNAME"),
            api_token=os.getenv("TEST_CONFLUENCE_TOKEN")
        )
    
    @pytest.mark.asyncio
    async def test_search_returns_documents(self, confluence_client):
        results = await confluence_client.search_content("test documentation")
        
        assert len(results) > 0
        assert all(isinstance(doc, Document) for doc in results)
        assert all(doc.source == "confluence" for doc in results)
```

### Performance Tests

Load testing to validate performance requirements.

```python
# tests/performance/test_search_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def test_concurrent_search_performance():
    search_engine = NAVOSearchEngine(config)
    
    async def single_search():
        start_time = time.time()
        await search_engine.search("performance test query")
        return time.time() - start_time
    
    # Test 100 concurrent searches
    tasks = [single_search() for _ in range(100)]
    response_times = await asyncio.gather(*tasks)
    
    avg_response_time = sum(response_times) / len(response_times)
    p95_response_time = sorted(response_times)[94]  # 95th percentile
    
    assert avg_response_time < 0.2  # 200ms average
    assert p95_response_time < 0.5  # 500ms 95th percentile
```

## Monitoring and Observability

### Metrics Collection

Key performance indicators tracked through Prometheus metrics:

- **Search latency**: Response time distribution
- **Search accuracy**: Relevance scores and user feedback
- **Cache hit rate**: Percentage of requests served from cache
- **Error rate**: Failed requests per minute
- **Throughput**: Requests per second

### Logging

Structured logging with correlation IDs for request tracing:

```python
import structlog

logger = structlog.get_logger()

async def search_handler(request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    logger.info(
        "search_request_received",
        correlation_id=correlation_id,
        query=request.query,
        user_id=request.user_id
    )
    
    try:
        results = await search_engine.search(request.query)
        
        logger.info(
            "search_request_completed",
            correlation_id=correlation_id,
            results_count=len(results.documents),
            search_time_ms=results.search_time_ms
        )
        
        return results
    except Exception as e:
        logger.error(
            "search_request_failed",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### Alerting

Automated alerts for critical issues:

- Search latency exceeding 500ms for 5 minutes
- Error rate exceeding 5% for 2 minutes
- Cache hit rate below 70% for 10 minutes
- External service connectivity issues

## Security Considerations

### Authentication

Phase 1 supports multiple authentication methods:

- **API Key Authentication**: For service-to-service communication
- **OAuth 2.0**: For user authentication
- **Azure AD Integration**: For enterprise SSO

### Authorization

Role-based access control ensures users only access authorized content:

```python
class AuthorizationMiddleware:
    async def __call__(self, request, call_next):
        user = await self.authenticate_user(request)
        
        # Add user context to request
        request.state.user = user
        request.state.permissions = await self.get_user_permissions(user)
        
        response = await call_next(request)
        return response
    
    async def filter_results_by_permissions(self, results: SearchResults, user: User) -> SearchResults:
        filtered_documents = []
        
        for doc in results.documents:
            if await self.user_can_access_document(user, doc):
                filtered_documents.append(doc)
        
        return SearchResults(
            documents=filtered_documents,
            total_results=len(filtered_documents),
            query_id=results.query_id
        )
```

### Data Protection

- **Encryption in Transit**: TLS 1.3 for all API communications
- **Encryption at Rest**: AES-256 for cached data and logs
- **Data Masking**: Automatic PII detection and redaction in logs

## Success Metrics

### Technical Metrics

- **Response Time**: <127ms average, <500ms 95th percentile
- **Availability**: >99.5% uptime
- **Accuracy**: >85% relevance score
- **Cache Hit Rate**: >70%

### Business Metrics

- **User Adoption**: >80% of engineering team using NAVO weekly
- **Query Volume**: >1000 queries per week
- **User Satisfaction**: >4.0/5.0 average rating
- **Time Savings**: 30% reduction in documentation search time

### Quality Metrics

- **Code Coverage**: >90% for all components
- **Security Scan**: Zero critical vulnerabilities
- **Performance Tests**: All tests passing
- **Documentation**: 100% API coverage

## Conclusion

Phase 1 establishes a solid foundation for enterprise knowledge discovery with immediate value delivery. The architecture supports future phases while providing production-ready capabilities for multi-source search and natural language processing. Success in Phase 1 enables progression to more advanced capabilities in subsequent phases.

