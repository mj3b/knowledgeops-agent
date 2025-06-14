# KnowledgeOps Agent - Configuration Guide

**Version:** 1.0.0  
**Date:** June 14, 2025  
**Author:** Manus AI  

## Table of Contents

1. [Introduction](#introduction)
2. [Environment Variables](#environment-variables)
3. [Configuration File (`config.yaml`)](#configuration-file-configyaml)
4. [Core System Configuration](#core-system-configuration)
5. [Integration Configuration](#integration-configuration)
6. [AI and Machine Learning Configuration](#ai-and-machine-learning-configuration)
7. [Security Configuration](#security-configuration)
8. [Performance and Scalability Configuration](#performance-and-scalability-configuration)
9. [Logging and Monitoring Configuration](#logging-and-monitoring-configuration)
10. [Notification Configuration](#notification-configuration)
11. [Multi-Tenant Configuration](#multi-tenant-configuration)
12. [Advanced Configuration](#advanced-configuration)
13. [Configuration Best Practices](#configuration-best-practices)

## Introduction

The KnowledgeOps Agent offers a flexible and comprehensive configuration system that allows administrators to tailor the platform to specific organizational needs, security policies, and integration requirements. Configuration can be managed through environment variables for deployment-specific settings and a central `config.yaml` file for more detailed and structured configurations. This guide provides a comprehensive overview of all available configuration options, best practices for managing configurations, and examples for common use cases.

Understanding the configuration options is crucial for optimizing performance, ensuring security, and integrating the KnowledgeOps Agent seamlessly into your existing enterprise ecosystem. This guide is intended for system administrators, DevOps engineers, and anyone responsible for deploying and maintaining the KnowledgeOps Agent.

### Configuration Hierarchy

The KnowledgeOps Agent uses a layered configuration approach:

1.  **Default Values:** Built-in defaults for all settings.
2.  **`config.yaml` File:** Overrides default values. This is the primary method for detailed configuration.
3.  **Environment Variables:** Override values from `config.yaml` and defaults. Ideal for deployment-specific settings and secrets.

This hierarchy allows for a base configuration to be defined in `config.yaml` and then customized for different environments (development, staging, production) using environment variables without modifying the core configuration file.

## Environment Variables

Environment variables are primarily used for settings that vary between deployment environments or for sensitive information like API keys and database credentials. They take precedence over settings in `config.yaml`.

### Core Environment Variables

-   `KNOWLEDGEOPS_ENV`: (String) Specifies the deployment environment (e.g., `development`, `staging`, `production`). Default: `production`.
-   `KNOWLEDGEOPS_CONFIG_PATH`: (String) Path to the `config.yaml` file. Default: `./config.yaml`.
-   `KNOWLEDGEOPS_LOG_LEVEL`: (String) Logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`). Default: `INFO`.
-   `KNOWLEDGEOPS_PORT`: (Integer) Port number for the main application. Default: `5000`.
-   `KNOWLEDGEOPS_SECRET_KEY`: (String) Secret key for session management and cryptographic signing. **Required for production.**

### Database Connection

-   `DATABASE_URL`: (String) Full database connection string (e.g., `postgresql://user:password@host:port/database`).
-   `DATABASE_TYPE`: (String) Type of database (e.g., `postgresql`, `mysql`). Default: `postgresql`.
-   `DATABASE_HOST`: (String) Database server hostname.
-   `DATABASE_PORT`: (Integer) Database server port.
-   `DATABASE_NAME`: (String) Database name.
-   `DATABASE_USER`: (String) Database username.
-   `DATABASE_PASSWORD`: (String) Database password.

### Cache (Redis)

-   `REDIS_URL`: (String) Full Redis connection string (e.g., `redis://:password@host:port/0`).
-   `REDIS_HOST`: (String) Redis server hostname. Default: `localhost`.
-   `REDIS_PORT`: (Integer) Redis server port. Default: `6379`.
-   `REDIS_PASSWORD`: (String) Redis password (if any).
-   `REDIS_DB`: (Integer) Redis database number. Default: `0`.

### Message Queue (e.g., RabbitMQ, Kafka)

-   `MESSAGE_QUEUE_URL`: (String) Connection string for the message queue.
-   `MESSAGE_QUEUE_TYPE`: (String) Type of message queue (e.g., `rabbitmq`, `kafka`).

### External API Keys

-   `OPENAI_API_KEY`: (String) API key for OpenAI services.
-   `AZURE_OPENAI_API_KEY`: (String) API key for Azure OpenAI services.
-   `AZURE_OPENAI_ENDPOINT`: (String) Endpoint for Azure OpenAI services.
-   `CONFLUENCE_API_TOKEN_PRIMARY`: (String) API token for the primary Confluence instance.
-   `SHAREPOINT_CLIENT_ID_PRIMARY`: (String) Client ID for the primary SharePoint integration.
-   `SHAREPOINT_CLIENT_SECRET_PRIMARY`: (String) Client secret for the primary SharePoint integration.

### Example `.env` file

```env
KNOWLEDGEOPS_ENV=production
KNOWLEDGEOPS_LOG_LEVEL=INFO
KNOWLEDGEOPS_PORT=8080
KNOWLEDGEOPS_SECRET_KEY=

# PostgreSQL Database
DATABASE_URL=postgresql://knowledgeops_user:securepassword123@db.example.com:5432/knowledgeops_prod

# Redis Cache
REDIS_URL=redis://:anothersecurepassword@cache.example.com:6379/0

# OpenAI API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Confluence API Token
CONFLUENCE_API_TOKEN_PRIMARY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# SharePoint Credentials
SHAREPOINT_CLIENT_ID_PRIMARY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SHAREPOINT_CLIENT_SECRET_PRIMARY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Configuration File (`config.yaml`)

The `config.yaml` file is the central place for detailed configuration of the KnowledgeOps Agent. It uses YAML format for readability and structure. The application loads this file at startup. If `KNOWLEDGEOPS_CONFIG_PATH` environment variable is set, it will load from that path; otherwise, it defaults to `./config.yaml` in the application root.

### Basic Structure

```yaml
system:
  version: "1.0.0"
  environment: "production" # Can be overridden by KNOWLEDGEOPS_ENV
  maintenance_mode: false

logging:
  level: "INFO" # Can be overridden by KNOWLEDGEOPS_LOG_LEVEL
  format: "json"
  file_path: "/var/log/knowledgeops/app.log"

server:
  port: 5000 # Can be overridden by KNOWLEDGEOPS_PORT
  host: "0.0.0.0"
  workers: 4

# ... other sections like database, cache, integrations, ai, security, etc.
```

## Core System Configuration

This section in `config.yaml` defines fundamental system-wide settings.

```yaml
system:
  # Application version (primarily for informational purposes)
  version: "1.0.0"

  # Deployment environment (development, staging, production)
  # Overridden by KNOWLEDGEOPS_ENV environment variable if set.
  environment: "production"

  # Enable maintenance mode. If true, API returns 503 Service Unavailable.
  maintenance_mode: false
  maintenance_message: "The KnowledgeOps Agent is currently undergoing scheduled maintenance. Please try again later."

  # Base URL for the application, used for generating absolute URLs in responses and notifications.
  base_app_url: "https://knowledge.example.com"

  # Feature flags to enable/disable specific functionalities.
  # Allows for gradual rollout or disabling features without code changes.
  feature_flags:
    semantic_search: true
    real_time_sync: true
    advanced_analytics: true
    multi_language_support: false
    user_feedback_collection: true
    adaptive_card_responses: true

  # Default language and timezone for the application.
  # Can be overridden by user preferences.
  default_language: "en-US"
  default_timezone: "UTC"

  # Temporary file storage configuration
  temp_file_storage:
    path: "/tmp/knowledgeops"
    max_size_gb: 10
    cleanup_interval_hours: 24
```

**Details:**

-   `maintenance_mode`: When `true`, the API will return HTTP 503 for most requests, allowing for system updates.
-   `base_app_url`: Essential for ensuring links in emails, notifications, and API responses are correct.
-   `feature_flags`: Boolean values to toggle major features. This is useful for A/B testing or phased rollouts.
-   `default_language` / `default_timezone`: System-wide defaults if user-specific settings are not available.
-   `temp_file_storage`: Configuration for temporary storage used during document processing or uploads.

## Integration Configuration

This section defines how the KnowledgeOps Agent connects to and interacts with external knowledge sources like Confluence and SharePoint, as well as other third-party services.

```yaml
integrations:
  # Global settings for all integrations
  global_sync_enabled: true
  default_sync_interval_minutes: 60 # Default interval if not specified per integration
  max_concurrent_sync_jobs: 5

  # Configuration for Confluence integrations
  # Multiple Confluence instances can be configured
  confluence:
    - id: "confluence_primary" # Unique identifier for this integration instance
      name: "Primary Corporate Confluence"
      enabled: true
      type: "cloud" # or "server", "datacenter"
      base_url: "https://yourcompany.atlassian.net/wiki"
      authentication:
        # Authentication method: "api_token", "oauth2", "basic"
        method: "api_token"
        # For api_token: provide username (email) and token (from env var)
        username: "service.account@example.com"
        api_token_env_var: "CONFLUENCE_API_TOKEN_PRIMARY" # Name of the env var holding the token
        # For oauth2: provide client_id, client_secret_env_var, redirect_uri, scopes
        # client_id: "xxxxxxxxxxxx"
        # client_secret_env_var: "CONFLUENCE_OAUTH_SECRET_PRIMARY"
        # redirect_uri: "https://knowledge.example.com/auth/confluence/callback"
        # scopes: ["read:confluence-content.all", "read:confluence-space.summary"]
      sync_settings:
        # Spaces to include in synchronization. Use `*` for all accessible spaces.
        spaces_to_sync: ["ENG", "PRODUCT", "SUPPORT"]
        # Spaces to explicitly exclude.
        spaces_to_exclude: ["SANDBOX", "ARCHIVE"]
        # Content types to include (e.g., page, blogpost, comment, attachment)
        content_types_to_sync: ["page", "blogpost", "attachment"]
        # Sync interval in minutes for this specific instance.
        sync_interval_minutes: 30
        # Enable incremental sync (only fetch changes since last sync).
        incremental_sync: true
        # Maximum number of pages to fetch per API call during sync.
        page_limit_per_request: 100
        # Whether to sync attachments and their content.
        sync_attachments: true
        max_attachment_size_mb: 50
        # File types for attachments to sync (e.g., ["pdf", "docx", "txt"])
        attachment_file_types: ["*"] # Sync all attachment types
        # Respect Confluence permissions during sync and search.
        respect_permissions: true
      processing_options:
        # Extract custom fields/metadata from Confluence pages.
        extract_custom_fields: true
        # Enable Optical Character Recognition (OCR) for images in attachments.
        enable_ocr_for_attachments: false
        # Maximum depth for traversing page hierarchies.
        max_page_depth: 10

  # Configuration for SharePoint integrations
  sharepoint:
    - id: "sharepoint_engineering"
      name: "Engineering SharePoint Site"
      enabled: true
      type: "online" # or "on_premise"
      # For online: provide tenant_id and site_url
      tenant_id: "yourtenant.onmicrosoft.com"
      site_url: "https://yourtenant.sharepoint.com/sites/Engineering"
      # For on_premise: provide site_url and authentication details
      authentication:
        # Authentication method: "oauth2_client_credentials", "user_credentials"
        method: "oauth2_client_credentials"
        client_id_env_var: "SHAREPOINT_CLIENT_ID_ENGINEERING"
        client_secret_env_var: "SHAREPOINT_CLIENT_SECRET_ENGINEERING"
        # For user_credentials (less secure, for on-premise testing mainly):
        # username_env_var: "SHAREPOINT_USER_ENGINEERING"
        # password_env_var: "SHAREPOINT_PASSWORD_ENGINEERING"
      sync_settings:
        # Document libraries to sync. Use `*` for all accessible libraries.
        document_libraries_to_sync: ["Documents", "Technical Specifications", "Project Plans"]
        # Folders to exclude within synced libraries (paths relative to library root).
        folders_to_exclude: ["Archive", "Old Versions"]
        # File types to include (e.g., ["docx", "pdf", "xlsx", "pptx"])
        file_types_to_sync: ["docx", "pdf", "md"]
        # Sync interval in minutes for this specific instance.
        sync_interval_minutes: 45
        incremental_sync: true
        # Respect SharePoint permissions.
        respect_permissions: true
        # Sync list items as documents.
        sync_list_items: false
        # Lists to sync if sync_list_items is true.
        lists_to_sync: ["Issue Tracker", "Project Tasks"]
      processing_options:
        # Extract SharePoint metadata columns.
        extract_metadata_columns: true
        # Enable OCR for images within documents.
        enable_ocr_for_documents: true
        # Version history handling: "latest" or "all"
        version_history: "latest"

  # Example for a generic webhook integration (e.g., for receiving external events)
  webhooks:
    - id: "external_system_feed"
      name: "External System Content Feed"
      enabled: true
      url_env_var: "EXTERNAL_WEBHOOK_URL"
      secret_env_var: "EXTERNAL_WEBHOOK_SECRET"
      events_to_subscribe: ["content.created", "content.updated"]
```

**Details:**

-   Each integration type (Confluence, SharePoint) is a list, allowing multiple instances (e.g., different Confluence servers or SharePoint sites).
-   `id` and `name` help identify the integration instance in logs and UI.
-   `enabled`: Toggles the entire integration instance.
-   Authentication details often refer to environment variables (e.g., `api_token_env_var`) for security.
-   `sync_settings`: Controls what content is fetched (spaces, libraries, content types, file types) and how often.
-   `respect_permissions`: Critical for ensuring users only see content they are authorized to access in the source system.
-   `processing_options`: Defines how content is handled after fetching (e.g., OCR, metadata extraction).

## AI and Machine Learning Configuration

This section configures the AI models and services used for natural language processing, semantic search, and other intelligent features.

```yaml
ai_ml:
  # Primary Large Language Model (LLM) provider configuration
  llm_provider:
    # Provider name: "openai", "azure_openai", "huggingface_hub", "local_ollama"
    name: "openai"
    # API key environment variable name
    api_key_env_var: "OPENAI_API_KEY"
    # For Azure OpenAI:
    # endpoint_env_var: "AZURE_OPENAI_ENDPOINT"
    # deployment_name: "gpt-35-turbo"
    # api_version: "2023-07-01-preview"
    # For HuggingFace Hub:
    # repo_id: "google/flan-t5-large"
    # For local Ollama:
    # base_url: "http://localhost:11434"
    # model_name: "llama2"

  # Default models for different tasks
  models:
    query_understanding: "gpt-3.5-turbo" # Model for parsing and understanding user queries
    response_generation: "gpt-3.5-turbo" # Model for generating natural language responses
    summarization: "text-davinci-003" # Or a model specialized for summarization
    embedding_generation: "text-embedding-ada-002" # Model for creating vector embeddings

  # Semantic search configuration
  semantic_search:
    enabled: true
    # Vector database provider: "pinecone", "weaviate", "chroma", "elasticsearch_vector", "pgvector"
    vector_db_provider: "pgvector"
    # For Pinecone:
    # api_key_env_var: "PINECONE_API_KEY"
    # environment: "us-west1-gcp"
    # index_name: "knowledgeops-embeddings"
    # For Elasticsearch Vector Search:
    # elasticsearch_url_env_var: "ELASTICSEARCH_URL"
    # index_name: "knowledgeops_vector_index"
    # For pgvector (assumes PostgreSQL is already configured):
    # (No specific config needed here if using the main DB with pgvector extension)

    embedding_dimension: 1536 # Dimension of the embeddings (e.g., 1536 for text-embedding-ada-002)
    similarity_metric: "cosine" # "cosine", "euclidean", "dot_product"
    top_k_results: 5 # Number of semantically similar documents to retrieve

  # Natural Language Processing (NLP) settings
  nlp:
    # Enable/disable specific NLP features
    enable_intent_recognition: true
    enable_entity_extraction: true
    enable_sentiment_analysis: false # For user feedback, etc.

    # Language for NLP processing (if different from system default)
    processing_language: "en"

    # Custom entity definitions for Named Entity Recognition (NER)
    custom_ner_entities:
      - label: "PROJECT_CODE"
        patterns: ["PROJ-\\d{4}", "Project\\s\\w+"]
      - label: "ENVIRONMENT_TAG"
        patterns: ["QLAB\\d{2}", "PROD", "DEV", "STG"]

  # RAG (Retrieval Augmented Generation) specific settings
  rag:
    # Number of document chunks to retrieve for context
    context_chunk_size: 3
    # Overlap between chunks
    chunk_overlap_tokens: 50
    # Maximum tokens for the generated response
    max_response_tokens: 500
```

**Details:**

-   `llm_provider`: Specifies which LLM service to use (OpenAI, Azure, HuggingFace, local). API keys are sourced from environment variables.
-   `models`: Defines which specific LLM models are used for tasks like query understanding, response generation, summarization, and creating embeddings.
-   `semantic_search`: Configures the vector database used for semantic similarity searches. Options include cloud services like Pinecone or self-hosted solutions like Chroma or Elasticsearch with vector capabilities, or pgvector extension for PostgreSQL.
-   `nlp`: Settings for NLP features like intent recognition, entity extraction, and custom entity definitions for NER to recognize organization-specific terms.
-   `rag`: Parameters for the Retrieval Augmented Generation process, controlling how context is retrieved and used for generating answers.

## Security Configuration

This section details security-related settings, including authentication, authorization, API security, and data protection.

```yaml
security:
  # Authentication settings
  authentication:
    # Default authentication method for the API: "oauth2", "api_key", "jwt"
    default_api_auth_method: "oauth2"
    # Session timeout in minutes for web UI
    session_timeout_minutes: 480 # 8 hours
    # JWT settings (if jwt auth_method is used)
    jwt:
      secret_key_env_var: "KNOWLEDGEOPS_JWT_SECRET_KEY" # Env var for JWT signing secret
      algorithm: "HS256"
      access_token_expire_minutes: 30
      refresh_token_expire_days: 7
    # OAuth 2.0 provider settings (if KnowledgeOps acts as an OAuth provider)
    oauth2_provider:
      enabled: false # Set to true if this instance should act as an OAuth2 provider
      # ... (full OAuth2 provider config: clients, scopes, token settings)
    # SSO Integration (e.g., SAML, OpenID Connect with external IdP)
    sso:
      enabled: true
      provider: "saml" # "saml", "oidc"
      saml:
        idp_entity_id_env_var: "SAML_IDP_ENTITY_ID"
        idp_sso_url_env_var: "SAML_IDP_SSO_URL"
        idp_x509_cert_env_var: "SAML_IDP_X509_CERT"
        sp_entity_id: "https://knowledge.example.com/saml/metadata"
        sp_acs_url: "https://knowledge.example.com/saml/acs"
        attribute_mapping:
          email: "urn:oid:0.9.2342.19200300.100.1.3"
          first_name: "urn:oid:2.5.4.42"
          last_name: "urn:oid:2.5.4.4"
          groups: "urn:oid:1.3.6.1.4.1.5923.1.5.1.1"
      oidc:
        # ... (OIDC client settings for integrating with an external IdP)

  # Authorization settings
  authorization:
    # Default role for new users
    default_user_role: "viewer"
    # Role definitions and permissions
    roles:
      viewer:
        permissions: ["documents:read", "query:submit"]
      editor:
        permissions: ["documents:read", "documents:write", "query:submit", "feedback:submit"]
      admin:
        permissions: ["*"] # Wildcard for all permissions
    # Enable/disable fine-grained access control based on document source permissions
    enforce_source_permissions: true

  # API Security settings
  api_security:
    # Enable Cross-Origin Resource Sharing (CORS)
    cors_enabled: true
    cors_allowed_origins: ["https://*.example.com", "http://localhost:3000"]
    cors_allowed_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allowed_headers: ["Authorization", "Content-Type", "X-Request-ID"]
    cors_max_age_seconds: 3600
    # Content Security Policy (CSP) header for web UI
    content_security_policy: "default-src \'self\'; img-src *; script-src \'self\' cdn.example.com; style-src \'self\' \'unsafe-inline\'"
    # HTTP Strict Transport Security (HSTS) settings
    hsts_enabled: true
    hsts_max_age_seconds: 31536000 # 1 year
    hsts_include_subdomains: true
    hsts_preload: false

  # Data protection settings
  data_protection:
    # Enable encryption for sensitive data at rest (e.g., API keys in DB)
    encryption_at_rest_enabled: true
    encryption_key_env_var: "KNOWLEDGEOPS_DATA_ENCRYPTION_KEY" # Env var for data encryption key
    # PII (Personally Identifiable Information) handling
    pii_detection_enabled: true
    pii_redaction_enabled: false # If true, automatically redact PII in logs/responses
    pii_fields_to_scan: ["query_text", "document_content", "user_profile.email"]

  # Audit logging configuration
  audit_logging:
    enabled: true
    # Events to log: "all", "security", "admin_actions", "data_access"
    log_level: "security"
    # Retention period in days for audit logs
    retention_days: 180
    # Output for audit logs: "file", "database", "syslog"
    output_target: "file"
    file_path: "/var/log/knowledgeops/audit.log"
```

**Details:**

-   `authentication`: Configures how users and API clients authenticate. Supports JWT, OAuth2 (as a provider), and SSO (SAML/OIDC integration with external Identity Providers).
-   `authorization`: Defines roles and their associated permissions. `enforce_source_permissions` is key for respecting Confluence/SharePoint access rights.
-   `api_security`: CORS, CSP, HSTS settings to secure web interactions.
-   `data_protection`: Settings for encrypting sensitive data at rest and handling PII.
-   `audit_logging`: Configures what events are audited and where logs are stored.

## Performance and Scalability Configuration

This section allows tuning of parameters related to system performance, caching, and resource utilization.

```yaml
performance:
  # Web server and application worker configuration
  server_workers:
    # Number of Gunicorn/Uvicorn worker processes. Set to 0 for auto (based on CPU cores).
    count: 0
    # Type of worker (e.g., "sync", "gthread" for Gunicorn; "uvicorn.workers.UvicornWorker" for Uvicorn)
    type: "uvicorn.workers.UvicornWorker"
    threads_per_worker: 4 # For gthread workers
    timeout_seconds: 120 # Worker timeout

  # Caching configuration (general application cache, not Redis specific)
  caching:
    # Default cache TTL (Time To Live) in seconds for various items
    default_ttl_seconds: 3600 # 1 hour
    query_results_ttl_seconds: 600 # 10 minutes
    user_profile_ttl_seconds: 1800 # 30 minutes
    # Maximum size for in-memory caches (e.g., LRU cache for frequently accessed items)
    in_memory_cache_max_size_mb: 256

  # Database connection pooling
  database_connection_pool:
    min_size: 5
    max_size: 50
    timeout_seconds: 30 # Connection acquisition timeout
    max_overflow: 10 # How many connections can be temporarily created over max_size

  # Asynchronous task processing (e.g., using Celery with RabbitMQ/Redis as broker)
  async_tasks:
    enabled: true
    broker_url_env_var: "CELERY_BROKER_URL" # e.g., amqp://guest:guest@localhost:5672// or redis://localhost:6379/1
    result_backend_env_var: "CELERY_RESULT_BACKEND_URL" # e.g., redis://localhost:6379/2
    concurrency: 8 # Number of concurrent Celery workers
    default_queue: "knowledgeops_tasks"
    task_time_limit_seconds: 1800 # 30 minutes for long tasks like document indexing

  # Rate limiting configuration (global defaults, can be overridden per user/API key)
  rate_limiting:
    enabled: true
    default_strategy: "fixed_window" # "fixed_window", "sliding_window", "token_bucket"
    # Default limits for unauthenticated users or general API access
    default_limit_per_minute: 100
    default_burst_limit: 200 # For token bucket or similar strategies
```

**Details:**

-   `server_workers`: Configuration for the HTTP server (e.g., Gunicorn, Uvicorn) workers.
-   `caching`: TTLs for various types of cached data.
-   `database_connection_pool`: Parameters for optimizing database connections.
-   `async_tasks`: Configuration for background task processing, often using Celery. Broker and backend URLs are typically set via environment variables.
-   `rate_limiting`: Default API rate limiting policies.

## Logging and Monitoring Configuration

This section configures how application logs, metrics, and monitoring data are generated and exported.

```yaml
logging:
  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  # Overridden by KNOWLEDGEOPS_LOG_LEVEL environment variable if set.
  level: "INFO"

  # Log format: "text", "json"
  # JSON format is recommended for production for easier parsing by log management systems.
  format: "json"

  # Log output target: "console", "file", "syslog"
  output_target: "console"

  # File logging settings (if output_target is "file")
  file:
    path: "/var/log/knowledgeops/app.log"
    max_size_mb: 100
    backup_count: 10 # Number of rotated log files to keep
    compress_rotated_logs: true

  # Syslog settings (if output_target is "syslog")
  syslog:
    address: "/dev/log" # Or "host:port" for remote syslog
    facility: "local0"

  # Enable/disable logging for specific modules or components
  module_log_levels:
    sqlalchemy.engine: "WARNING"
    werkzeug: "INFO"
    httpx: "INFO"

monitoring:
  # Enable Prometheus metrics endpoint (e.g., /metrics)
  prometheus_enabled: true
  prometheus_port: 9091 # Port for Prometheus metrics server, if separate

  # Distributed tracing configuration (e.g., OpenTelemetry with Jaeger/Zipkin)
  tracing:
    enabled: false
    provider: "opentelemetry" # "opentelemetry", "jaeger", "zipkin"
    # OpenTelemetry specific settings
    opentelemetry:
      service_name: "knowledgeops-agent"
      exporter_type: "otlp_http" # "otlp_http", "otlp_grpc", "jaeger_thrift_http"
      endpoint_env_var: "OTEL_EXPORTER_OTLP_ENDPOINT" # e.g., http://localhost:4318
      # Sampling rate (0.0 to 1.0)
      sample_rate: 0.1
```

**Details:**

-   `logging`: Controls log level, format (text/JSON), and output (console, file, syslog). Module-specific log levels can be set to reduce noise from verbose libraries.
-   `monitoring`: Enables Prometheus metrics endpoint for scraping by a Prometheus server. Configures distributed tracing.

## Notification Configuration

This section defines how users and administrators are notified of system events, alerts, and content updates.

```yaml
notifications:
  # Global notification settings
  enabled: true
  default_channels: ["email", "in_app"] # Default channels if user hasn't specified

  # Email notification settings
  email:
    enabled: true
    smtp_server_env_var: "SMTP_HOST"
    smtp_port: 587 # Or 465 for SSL, 25 for unencrypted (not recommended)
    smtp_use_tls: true
    smtp_username_env_var: "SMTP_USERNAME"
    smtp_password_env_var: "SMTP_PASSWORD"
    from_address: "noreply@knowledge.example.com"
    from_name: "KnowledgeOps Agent"
    # HTML email templates directory
    template_dir: "./templates/emails"

  # In-app notification settings (if a web UI component is part of the system)
  in_app:
    enabled: true
    # How long in-app notifications are stored/displayed
    retention_days: 30

  # Microsoft Teams integration for notifications
  msteams:
    enabled: false
    # Default webhook URL for Teams channel (can be overridden per notification type)
    default_webhook_url_env_var: "MSTEAMS_WEBHOOK_URL_GENERAL"

  # Slack integration for notifications
  slack:
    enabled: false
    # Default webhook URL for Slack channel
    default_webhook_url_env_var: "SLACK_WEBHOOK_URL_GENERAL"

  # Specific notification event configurations
  event_notifications:
    # Notification for new document matching user interests
    new_relevant_document:
      enabled: true
      channels: ["email", "in_app"]
      # User can override these settings in their profile
      user_configurable: true
      default_frequency: "daily_digest" # "immediate", "daily_digest", "weekly_digest"

    # Notification for system maintenance
    system_maintenance_scheduled:
      enabled: true
      channels: ["email", "msteams"]
      # Target specific admin roles or groups
      target_roles: ["admin"]

    # Alert for critical system errors
    critical_system_error:
      enabled: true
      channels: ["email", "msteams", "pagerduty"]
      target_roles: ["admin", "devops"]
      # PagerDuty specific integration (if used)
      pagerduty_integration_key_env_var: "PAGERDUTY_INTEGRATION_KEY"
```

**Details:**

-   Configures various notification channels (email, in-app, MS Teams, Slack). Sensitive details like SMTP passwords or webhook URLs are set via environment variables.
-   `event_notifications`: Allows fine-grained control over which events trigger notifications, to whom, through which channels, and how frequently.

## Multi-Tenant Configuration

If the KnowledgeOps Agent is designed to support multiple tenants (e.g., different departments or client organizations using a shared instance), this section defines tenant-specific settings.

```yaml
multi_tenancy:
  enabled: false # Set to true to enable multi-tenant mode

  # Strategy for isolating tenant data: "shared_database_discriminator_column",
  # "separate_schemas", "separate_databases"
  isolation_strategy: "shared_database_discriminator_column"

  # Default resource quotas for new tenants (can be overridden per tenant)
  default_tenant_quotas:
    max_users: 100
    max_documents_indexed: 100000
    max_api_calls_per_month: 1000000
    max_custom_integrations: 2

  # Tenant identification strategy: "subdomain", "path_prefix", "custom_header"
  tenant_identification_strategy: "subdomain" # e.g., tenant1.knowledge.example.com
  # If path_prefix: e.g., knowledge.example.com/tenant1/
  # If custom_header: e.g., X-Tenant-ID: tenant1

  # Configuration for specific tenants (if not managed dynamically via an admin API)
  # This section might be minimal if tenants are provisioned via API/UI
  tenants:
    - id: "tenant_alpha"
      name: "Alpha Corporation"
      subdomain: "alpha" # Used if tenant_identification_strategy is "subdomain"
      # Tenant-specific overrides for integrations, AI models, security, etc.
      config_overrides:
        integrations:
          confluence:
            - id: "alpha_confluence"
              base_url: "https://alpha.atlassian.net/wiki"
              # ... other specific settings for Alpha Corp Confluence
        ai_ml:
          models:
            query_understanding: "gpt-4"
      quotas:
        max_users: 200
```

**Details:**

-   `enabled`: Master switch for multi-tenancy.
-   `isolation_strategy`: Critical architectural choice for how tenant data is separated.
-   `default_tenant_quotas`: Default limits applied to new tenants.
-   `tenant_identification_strategy`: How the system identifies which tenant a request belongs to.
-   `tenants`: Static configuration for tenants. In many real-world scenarios, tenant provisioning and configuration would be managed via an administrative API or UI rather than a static config file.

## Advanced Configuration

This section is for highly specific or experimental configurations, often related to deep system internals or third-party library tuning.

```yaml
advanced:
  # Tuning for underlying libraries (e.g., SQLAlchemy, httpx)
  library_tuning:
    sqlalchemy:
      # Enable/disable specific SQLAlchemy features or set engine options
      echo_pool: false # Log connection pool activity
      pool_recycle_seconds: 3600 # How often connections are recycled
    httpx:
      # Default timeout for HTTP requests made by the application to external services
      default_timeout_seconds: 30
      # HTTP/2 support for outgoing requests
      http2_enabled: true
      # Connection limits for the HTTP client pool
      connection_limits:
        max_connections: 100
        max_keepalive_connections: 20

  # Experimental features (use with caution)
  experimental_features:
    # Example: Enable a new, untested query algorithm
    new_query_algorithm_enabled: false
    new_query_algorithm_params:
      param_x: 1.23

  # Custom request/response header manipulation
  header_manipulation:
    add_response_headers:
      X-KnowledgeOps-Version: "${system.version}" # Reference other config values
      X-Powered-By: "KnowledgeOps Agent"
    # Remove specific request headers before processing
    remove_request_headers: ["X-Forwarded-Proto"]

  # Debugging specific components
  component_debugging:
    query_parser_debug_mode: false
    sync_job_verbose_logging: false
```

**Details:**

-   `library_tuning`: Allows fine-tuning parameters for libraries like SQLAlchemy (database) or httpx (HTTP client).
-   `experimental_features`: For enabling features that are not yet stable or fully tested.
-   `header_manipulation`: For adding custom HTTP headers to responses or modifying request headers.

## Configuration Best Practices

1.  **Use Environment Variables for Secrets:** Never hardcode API keys, passwords, or other sensitive information in `config.yaml`. Always use environment variables (e.g., `*_ENV_VAR` references in the config) or a dedicated secrets management system.
2.  **Version Control `config.yaml` (without secrets):** The `config.yaml` file (template version without actual secret values) should be version controlled with your application code. Environment-specific `.env` files should NOT be version controlled.
3.  **Environment-Specific Configurations:** Use environment variables to override settings for different environments (dev, staging, prod). For example, `KNOWLEDGEOPS_ENV=development` can trigger different logging levels or disable certain integrations.
4.  **Validate Configuration at Startup:** The application should validate the loaded configuration at startup and fail fast if critical settings are missing or invalid.
5.  **Modular Configuration:** Keep the `config.yaml` well-organized with clear sections. For very large configurations, consider if your framework supports including sub-configuration files.
6.  **Documentation:** Clearly document all configuration options, their purpose, possible values, and defaults (as done in this guide).
7.  **Regular Review:** Periodically review configuration settings, especially security-related ones, to ensure they are still appropriate and align with best practices.
8.  **Atomic Changes:** When making configuration changes, especially in production, aim for small, atomic changes that can be easily rolled back if issues arise.
9.  **Reloadable Configuration (Advanced):** For some settings, consider implementing mechanisms to reload configuration without restarting the application, but be cautious about the complexity and potential side effects.

---

*This Configuration Guide provides a comprehensive overview of settings available in the KnowledgeOps Agent. Always refer to the latest version of this document and any release notes for changes or additions to configuration options.*

