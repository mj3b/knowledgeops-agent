# KnowledgeOps Agent - Enterprise Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_enterprise.txt .
RUN pip install --no-cache-dir -r requirements_enterprise.txt

# Copy application code
COPY confluence_integration.py .
COPY sharepoint_integration.py .
COPY unified_knowledge_manager.py .
COPY knowledgeops_app.py .

# Create cache directory
RUN mkdir -p /app/knowledge_cache

# Create non-root user
RUN useradd --create-home --shell /bin/bash knowledgeops
RUN chown -R knowledgeops:knowledgeops /app
USER knowledgeops

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--max-requests", "1000", "knowledgeops_app:app"]

