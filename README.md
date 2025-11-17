# Task Queue Worker System

A distributed task queue system built with Python, Flask, Redis, Docker, and Kubernetes. This project demonstrates microservices architecture with automatic scaling, health monitoring, and resilient task processing.

## 🏗️ Architecture

The system consists of three main components:

- **API Service** (`src/taskqueueworker/api.py`): Flask REST API that receives task submissions and provides status tracking
- **Worker Service** (`src/taskqueueworker/worker.py`): Background workers that process tasks from the Redis queue
- **Redis**: Message broker and state storage for the queue and task metadata

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │────────▶│  API Service│────────▶│    Redis    │
│             │   HTTP  │  (Flask)    │         │   (Queue)   │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                        │
                                                        │ BLPOP
                                                        ▼
                                                 ┌─────────────┐
                                                 │   Workers   │
                                                 │ (Auto-scale)│
                                                 └─────────────┘
```

## ✨ Features

- **Horizontal Auto-Scaling**: Workers automatically scale from 2-10 replicas based on CPU usage
- **Task Type**: Built-in support for sending emails
- **Real-time Status Tracking**: Monitor task progress via REST API endpoints
- **Health Checks**: Kubernetes liveness and readiness probes for reliability
- **Resource Management**: Defined CPU and memory limits for optimal performance
- **Load Balancing**: Multiple API replicas with LoadBalancer service
- **Persistent Queue**: Redis-backed queue survives pod restarts

## 📋 Prerequisites

- **Docker** and **Docker Compose** (for local development)
- **Kubernetes cluster**: minikube, kind, Docker Desktop, or cloud provider
- **kubectl**: Configured to connect to your cluster
- **Python 3.11+**: For local development and testing

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Local Development)

1. **Clone the repository**:
```bash
git clone https://github.com/joshuaemerson/task-queue-worker.git
cd task-queue-worker
```

2. **Start all services**:
```bash
docker-compose up --build
```

3. **Access the API**:
```bash
# API will be available at http://localhost:5000
curl http://localhost:5000/health
```

### Option 2: Kubernetes Deployment (Production)

#### Step 1: Prepare Your Cluster

Choose your Kubernetes environment:

```bash
# Using Minikube (recommended for local testing)
minikube start
eval $(minikube docker-env)

# Using kind
kind create cluster --name task-queue

# Using Docker Desktop
# Enable Kubernetes in Docker Desktop settings
```

#### Step 2: Build Docker Images

```bash
# Build both images
docker build -f Dockerfile.api -t task-queue-api:latest .
docker build -f Dockerfile.worker -t task-queue-worker:latest .

# Verify images were created
docker images | grep task-queue
```

#### Step 3: Deploy to Kubernetes

```bash
# Deploy Redis (message broker)
kubectl apply -f k8s/redis-deployment.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis --timeout=60s

# Deploy API service
kubectl apply -f k8s/api-deployment.yaml

# Wait for API to be ready
kubectl wait --for=condition=ready pod -l app=task-api --timeout=120s

# Deploy Workers with auto-scaling
kubectl apply -f k8s/worker-deployment.yaml
```

#### Step 4: Verify Deployment

```bash
# Check all resources
kubectl get all

# Expected output:
# - 1 Redis pod (redis-xxx)
# - 3 API pods (task-api-xxx)
# - 2 Worker pods (task-worker-xxx) - will scale based on load
# - Services: redis-service, api-service
# - HPA: task-worker-hpa
```

#### Step 5: Access the API

```bash
# Option A: Port forwarding (easiest for local testing)
kubectl port-forward service/api-service 8080:80

# Option B: Minikube service (opens in browser)
minikube service api-service

# Option C: Get LoadBalancer IP (cloud providers only)
kubectl get service api-service -o wide
```

## 📚 API Reference

### Base URL
- Local Docker Compose: `http://localhost:5000`
- Kubernetes Port Forward: `http://localhost:8080`
- Minikube: Run `minikube service api-service --url`

### Endpoints

#### Health Check
```bash
GET /health

# Response:
{
  "status": "healthy",
  "redis": "connected"
}

# Example:
curl http://localhost:8080/health
```

#### Create Task
```bash
POST /tasks
Content-Type: application/json

{
    "type": "email",
    "data": {
        "subject": "Test Email",
        "recipient": "penguinmanrrr@gmail.com",
        "content": "This is the contents for the test email"
    }
}

# Response:
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "message": "Task created successfully"
}
```

#### Get Task Status
```bash
GET /tasks/{task_id}

# Response:
{
  "created_at": "2025-11-14T15:37:57.169221",
  "data": {
      "content": "This is the contents for the test email",
      "recipient": "penguinmanrrr@gmail.com",
      "subject": "Test Email"
  },
  "id": "bd420f6f-bbaf-44d2-b4e5-748349a50811",
  "status": "queued",
  "type": "email"
}

# Example:
curl http://localhost:8080/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### List All Tasks
```bash
GET /tasks

# Response:
{
  "tasks": [
    {
      "id": "...",
      "type": "email",
      "status": "completed",
      ...
    }
  ],
  "count": 42
}

# Example:
curl http://localhost:8080/tasks
```

#### Queue Statistics
```bash
GET /queue/stats

# Response:
{
  "queue_length": 15,
  "total_tasks": 100
}

# Example:
curl http://localhost:8080/queue/stats
```


## 🔧 Supported Task Types

The worker supports these built-in task types (defined in `src/taskqueueworker/worker.py`):

| Task Type | Description | Example Use Case | Processing Time |
|-----------|-------------|------------------|-----------------|
| `email` | Simulates sending emails | User notifications | 1-3 seconds |


### Adding New Task Types

Edit `src/taskqueueworker/worker.py` and add to the `process_task()` function:

```python
def process_task(task):
    task_type = task.get('type')
    task_data = task.get('data', {})
    
    if task_type == 'video_transcode':
        # Your custom logic here
        time.sleep(random.uniform(10, 20))
        result = f"Video transcoded to {task_data.get('format', 'mp4')}"
    
    # ... existing task types ...
    
    return result
```

## 📊 Monitoring and Debugging

### View Logs

```bash
# API service logs
kubectl logs -l app=task-api --tail=50 -f

# Worker logs (all workers)
kubectl logs -l app=task-worker --tail=50 -f

# Specific worker pod
kubectl logs task-worker-78d7477dc8-aaaa -f

# Redis logs
kubectl logs -l app=redis --tail=50
```

### Check Resource Usage

```bash
# Pod CPU and memory usage
kubectl top pods

# Output:
# NAME                          CPU(cores)   MEMORY(bytes)
# redis-7bf784d547-2lfht        5m           18Mi
# task-api-xxx                  12m          48Mi
# task-worker-78d7477dc8-aaaa   88m          54Mi
# task-worker-78d7477dc8-bbbb   85m          52Mi

# Node resource usage
kubectl top nodes

# HPA status and scaling metrics
kubectl describe hpa task-worker-hpa
```

