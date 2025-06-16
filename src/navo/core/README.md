# NAVO Core Components

This directory contains the core NAVO components that implement the intelligent knowledge discovery and reasoning capabilities.

## Directory Structure

```
core/
├── __init__.py                 # Package initialization
├── navo_engine.py             # Central orchestrator
├── memory_layer.py            # Persistent memory system
├── reasoning_engine.py        # Transparent reasoning
├── query_processor.py         # Query understanding
├── response_generator.py      # Response generation
├── cache_manager.py           # Multi-level caching
└── permission_manager.py      # Access control
```

## Core Components Overview

### NAVO Engine (`navo_engine.py`)
The central orchestrator that coordinates all NAVO components and manages the complete query processing workflow.

**Key Responsibilities:**
- Query routing and processing coordination
- Memory and reasoning integration
- Response generation and caching
- Performance monitoring and analytics
- Error handling and fallback mechanisms

**Key Methods:**
- `process_query()` - Main query processing entry point
- `get_analytics()` - Performance and usage analytics
- `health_check()` - System health monitoring

### Memory Layer (`memory_layer.py`)
Persistent memory system inspired by cognitive architectures that enables NAVO to learn and improve over time.

**Memory Types:**
- **Episodic Memory**: Specific query-document interactions
- **Semantic Memory**: Knowledge about document relationships
- **Procedural Memory**: Successful search patterns
- **Working Memory**: Current context and session state

**Key Methods:**
- `store_interaction()` - Store query-result interactions
- `get_similar_queries()` - Find similar past queries
- `store_feedback()` - Learn from user feedback
- `cleanup_old_memories()` - Memory maintenance

### Reasoning Engine (`reasoning_engine.py`)
Transparent decision-making system that provides explainable AI with multi-step analysis and confidence scoring.

**Reasoning Steps:**
1. **Analytical** - Parse and understand query intent
2. **Predictive** - Predict document relevance scores
3. **Diagnostic** - Identify knowledge gaps and issues
4. **Prescriptive** - Generate specific recommendations
5. **Comparative** - Rank and compare options

**Key Methods:**
- `analyze_query()` - Multi-step query analysis
- `generate_recommendations()` - Create ranked recommendations
- `calculate_confidence()` - Confidence scoring
- `get_reasoning_trace()` - Audit trail generation

### Query Processor (`query_processor.py`)
Natural language understanding and intent classification system that interprets user queries and extracts relevant context.

**Capabilities:**
- Intent classification (procedural, factual, troubleshooting, discovery)
- Entity extraction (project codes, systems, protocols)
- Context enrichment (team, project, domain)
- Query normalization and expansion

**Key Methods:**
- `process_query()` - Main query processing
- `classify_intent()` - Intent classification
- `extract_entities()` - Entity recognition
- `enrich_context()` - Context enhancement

### Response Generator (`response_generator.py`)
Context-aware response generation system that creates intelligent, helpful responses with proper source attribution.

**Features:**
- Source attribution and confidence scoring
- Content summarization and highlighting
- Freshness tracking and outdated content flagging
- Follow-up question suggestions
- Adaptive response formatting

**Key Methods:**
- `generate_response()` - Main response generation
- `summarize_content()` - Content summarization
- `attribute_sources()` - Source attribution
- `suggest_followups()` - Follow-up suggestions

### Cache Manager (`cache_manager.py`)
Multi-level caching system that optimizes performance through intelligent caching strategies.

**Cache Levels:**
- **L1 Cache**: In-memory query results (Redis)
- **L2 Cache**: Processed document content (Redis)
- **L3 Cache**: Raw API responses (Redis)
- **Persistent Cache**: Long-term storage (SQLite/PostgreSQL)

**Key Methods:**
- `get_cached_result()` - Retrieve cached results
- `cache_result()` - Store results in cache
- `invalidate_cache()` - Cache invalidation
- `get_cache_stats()` - Cache performance metrics

### Permission Manager (`permission_manager.py`)
Fine-grained access control system that respects source system permissions and implements enterprise security policies.

**Security Features:**
- Permission inheritance from source systems
- Role-based access control (RBAC)
- Attribute-based access control (ABAC)
- Audit logging and compliance tracking

**Key Methods:**
- `check_permissions()` - Permission validation
- `inherit_permissions()` - Source permission inheritance
- `log_access()` - Audit trail logging
- `get_user_permissions()` - User permission retrieval

## Integration Patterns

### Component Communication
All core components communicate through well-defined interfaces and use dependency injection for loose coupling:

```python
from navo.core.navo_engine import NAVOEngine
from navo.core.memory_layer import NAVOMemoryLayer
from navo.core.reasoning_engine import NAVOReasoningEngine

# Initialize components
memory = NAVOMemoryLayer()
reasoning = NAVOReasoningEngine()
engine = NAVOEngine(memory=memory, reasoning=reasoning)

# Process query with full pipeline
result = await engine.process_query(query, context)
```

### Error Handling
All components implement comprehensive error handling with graceful degradation:

- **Memory failures**: Fall back to stateless operation
- **Reasoning failures**: Use simplified heuristics
- **Cache failures**: Direct source queries
- **Permission failures**: Secure denial with audit logging

### Performance Monitoring
Each component provides detailed performance metrics:

- **Execution time tracking**: Per-component timing
- **Resource usage monitoring**: Memory and CPU utilization
- **Success/failure rates**: Component reliability metrics
- **Cache performance**: Hit rates and efficiency

## Configuration

Core components are configured through the main configuration system:

```yaml
# config/config.yaml
core:
  memory:
    database_url: "sqlite:///navo_memory.db"
    cleanup_interval: 3600  # 1 hour
    max_memory_age: 2592000  # 30 days
  
  reasoning:
    confidence_threshold: 0.7
    max_reasoning_steps: 5
    enable_audit_trail: true
  
  cache:
    redis_url: "redis://localhost:6379"
    default_ttl: 3600  # 1 hour
    max_cache_size: "1GB"
  
  permissions:
    enable_rbac: true
    enable_abac: true
    audit_all_access: true
```

## Testing

Each core component has comprehensive test coverage:

```bash
# Run core component tests
pytest tests/unit/core/ -v

# Run specific component tests
pytest tests/unit/core/test_memory_layer.py -v
pytest tests/unit/core/test_reasoning_engine.py -v
pytest tests/unit/core/test_navo_engine.py -v

# Run integration tests
pytest tests/integration/core/ -v
```

## Development Guidelines

### Adding New Components
1. Follow the established interface patterns
2. Implement comprehensive error handling
3. Add performance monitoring
4. Include thorough test coverage
5. Update this documentation

### Modifying Existing Components
1. Maintain backward compatibility
2. Update tests for new functionality
3. Consider performance implications
4. Update configuration if needed
5. Document breaking changes

### Performance Considerations
- Use async/await for I/O operations
- Implement proper caching strategies
- Monitor memory usage and cleanup
- Profile performance-critical paths
- Consider horizontal scaling needs

The core components form the foundation of NAVO's intelligent knowledge discovery capabilities, providing the memory, reasoning, and processing power needed to transform documentation discovery from reactive searching to proactive knowledge delivery.

