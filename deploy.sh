#!/bin/bash

# NAVO One-Click Deployment Script
# This script sets up NAVO with all dependencies and configurations

set -e

echo "🚀 Starting NAVO Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3.11+ is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
        print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3.11"
fi

print_success "Python version check passed"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    print_success "Docker installed successfully"
else
    print_success "Docker found"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose found"
fi

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

print_success "Python dependencies installed"

# Setup environment configuration
print_status "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warning "Environment file created from template. Please configure your API keys in .env"
else
    print_success "Environment file already exists"
fi

# Setup Redis
print_status "Setting up Redis..."
if ! command -v redis-server &> /dev/null; then
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install redis
        else
            print_error "Homebrew not found. Please install Redis manually"
            exit 1
        fi
    else
        print_error "Unsupported operating system for automatic Redis installation"
        exit 1
    fi
    print_success "Redis installed successfully"
else
    print_success "Redis already installed"
fi

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    print_status "Starting Redis server..."
    redis-server --daemonize yes
    print_success "Redis server started"
else
    print_success "Redis server already running"
fi

# Setup database
print_status "Setting up database..."
$PYTHON_CMD -c "
from src.navo.core.memory_layer import NAVOMemoryLayer
memory = NAVOMemoryLayer()
memory.initialize_database()
print('Database initialized successfully')
"
print_success "Database setup completed"

# Run tests
print_status "Running test suite..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short
    if [ $? -eq 0 ]; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed. Check output above."
    fi
else
    print_warning "pytest not found. Skipping tests."
fi

# Build Docker images
print_status "Building Docker images..."
docker build -t navo:latest .
print_success "Docker image built successfully"

# Setup Docker Compose
print_status "Setting up Docker Compose services..."
docker-compose up -d postgres redis
print_success "Docker services started"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Health check
print_status "Performing health check..."
$PYTHON_CMD -c "
import requests
import time
import sys

# Start NAVO in background for health check
import subprocess
import os

# Set environment variables
os.environ['NAVO_PHASE'] = '2'

# Import and start NAVO
from src.navo.api.app import app
import uvicorn
import threading

def start_server():
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='error')

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Wait for server to start
time.sleep(5)

try:
    response = requests.get('http://localhost:8000/health', timeout=10)
    if response.status_code == 200:
        print('✅ Health check passed')
        sys.exit(0)
    else:
        print(f'❌ Health check failed: {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Health check passed"
else
    print_error "Health check failed"
fi

# Create startup script
print_status "Creating startup script..."
cat > start_navo.sh << 'EOF'
#!/bin/bash

# NAVO Startup Script

set -e

echo "🚀 Starting NAVO..."

# Activate virtual environment
source venv/bin/activate

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
fi

# Check if Docker services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "Starting Docker services..."
    docker-compose up -d
fi

# Set environment variables
export NAVO_PHASE=2

# Start NAVO
echo "Starting NAVO API server..."
python main.py

EOF

chmod +x start_navo.sh
print_success "Startup script created"

# Create health check script
print_status "Creating health check script..."
cat > health_check.sh << 'EOF'
#!/bin/bash

# NAVO Health Check Script

echo "🔍 NAVO Health Check"

# Check if NAVO is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ NAVO API: Running"
else
    echo "❌ NAVO API: Not responding"
fi

# Check Redis
if pgrep -x "redis-server" > /dev/null; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Not running"
fi

# Check Docker services
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker Services: Running"
else
    echo "❌ Docker Services: Not running"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
echo "📊 Memory Usage: ${MEMORY_USAGE}%"

# Check disk usage
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}')
echo "💾 Disk Usage: ${DISK_USAGE}"

EOF

chmod +x health_check.sh
print_success "Health check script created"

# Create demo scenarios script
print_status "Creating demo scenarios script..."
cat > demo_scenarios.py << 'EOF'
#!/usr/bin/env python3

"""
NAVO Demo Scenarios
Demonstrates key NAVO capabilities with realistic examples
"""

import asyncio
import json
import time
from src.navo.core.navo_engine import NAVOEngine
from src.navo.core.memory_layer import NAVOMemoryLayer
from src.navo.core.reasoning_engine import NAVOReasoningEngine

async def demo_basic_query():
    """Demo basic knowledge discovery"""
    print("🔍 Demo 1: Basic Knowledge Discovery")
    
    engine = NAVOEngine()
    
    query = "What's the API versioning standard?"
    context = {"user_id": "demo_user", "team": "engineering"}
    
    print(f"Query: {query}")
    
    start_time = time.time()
    result = await engine.process_query(query, context)
    end_time = time.time()
    
    print(f"Response Time: {(end_time - start_time) * 1000:.0f}ms")
    print(f"Results Found: {len(result.results)}")
    print(f"Confidence: {result.reasoning.confidence:.2f}")
    print("✅ Demo 1 Complete\n")

async def demo_memory_learning():
    """Demo memory and learning capabilities"""
    print("🧠 Demo 2: Memory and Learning")
    
    memory = NAVOMemoryLayer()
    
    # Simulate user feedback
    await memory.store_feedback(
        query_id="demo-query-1",
        result_id="demo-result-1",
        feedback="helpful",
        rating=5
    )
    
    # Retrieve learned patterns
    patterns = await memory.get_query_patterns("API")
    print(f"Learned Patterns: {len(patterns)}")
    
    print("✅ Demo 2 Complete\n")

async def demo_reasoning_transparency():
    """Demo transparent reasoning"""
    print("🤔 Demo 3: Transparent Reasoning")
    
    reasoning = NAVOReasoningEngine()
    
    query = "How do I configure retry logic for synthetic scripts?"
    context = {"intent": "procedural", "domain": "testing"}
    
    result = await reasoning.analyze_query(query, context)
    
    print(f"Query: {query}")
    print(f"Reasoning Steps: {len(result.steps)}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Execution Time: {result.execution_time_ms}ms")
    
    for i, step in enumerate(result.steps, 1):
        print(f"  Step {i}: {step.type} - {step.summary}")
    
    print("✅ Demo 3 Complete\n")

async def demo_performance_metrics():
    """Demo performance monitoring"""
    print("📊 Demo 4: Performance Metrics")
    
    # Simulate multiple queries for metrics
    engine = NAVOEngine()
    
    queries = [
        "Where's the retry logic documentation?",
        "What's the onboarding process?",
        "How do I configure VuGen scripts?",
        "What are the API rate limits?",
        "Where's the troubleshooting guide?"
    ]
    
    total_time = 0
    successful_queries = 0
    
    for query in queries:
        try:
            start_time = time.time()
            result = await engine.process_query(query, {"user_id": "demo_user"})
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            total_time += query_time
            successful_queries += 1
            
            print(f"Query: '{query[:30]}...' - {query_time:.0f}ms")
        except Exception as e:
            print(f"Query failed: {e}")
    
    if successful_queries > 0:
        avg_time = total_time / successful_queries
        print(f"\nAverage Response Time: {avg_time:.0f}ms")
        print(f"Success Rate: {successful_queries}/{len(queries)} ({successful_queries/len(queries)*100:.1f}%)")
    
    print("✅ Demo 4 Complete\n")

async def main():
    """Run all demo scenarios"""
    print("🎭 NAVO Demo Scenarios")
    print("=" * 50)
    
    try:
        await demo_basic_query()
        await demo_memory_learning()
        await demo_reasoning_transparency()
        await demo_performance_metrics()
        
        print("🎉 All demos completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

EOF

chmod +x demo_scenarios.py
print_success "Demo scenarios script created"

# Final setup summary
print_status "Deployment Summary"
echo "===================="
print_success "✅ NAVO deployed successfully!"
echo ""
echo "📁 Files created:"
echo "  - start_navo.sh (startup script)"
echo "  - health_check.sh (health monitoring)"
echo "  - demo_scenarios.py (demo scenarios)"
echo ""
echo "🚀 To start NAVO:"
echo "  ./start_navo.sh"
echo ""
echo "🔍 To check health:"
echo "  ./health_check.sh"
echo ""
echo "🎭 To run demos:"
echo "  python demo_scenarios.py"
echo ""
echo "🌐 Access points:"
echo "  - Web Interface: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
print_warning "⚠️  Don't forget to configure your API keys in .env file!"
echo ""
print_success "🎉 NAVO is ready to bring knowledge to where work happens!"

