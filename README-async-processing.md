# Asynchronous Task Processing System

This document explains how the asynchronous task processing system works using RabbitMQ and Celery.

## System Architecture

```
+-------------+         +-------------+         +-------------+         +-------------+
|             |         |             |         |             |         |             |
|  Frontend   |-------->|  Django API |-------->|  RabbitMQ   |-------->|  Celery    |
|  (Svelte)   |<--------|  (Controller)|<--------|  (Queue)    |<--------|  Worker    |
|             |         |             |         |             |         |             |
+-------------+         +-------------+         +-------------+         +-------------+
                              ^                                               |
                              |                                               |
                              |                                               |
                              v                                               v
                        +-------------+                                 +-------------+
                        |             |                                 |             |
                        |   Redis     |<--------------------------------|  File       |
                        |  (Results)  |                                 |  System     |
                        |             |                                 |             |
                        +-------------+                                 +-------------+
```

## Component Roles

### 1. Frontend (Svelte)
- Provides the user interface for submitting correction requests
- Sends API requests to the Django backend
- Polls for task status updates and displays progress to the user
- Updates the UI when tasks are completed or failed

### 2. Django API (Controller)
- Receives correction requests from the frontend
- Creates task records in the database
- Enqueues tasks in RabbitMQ
- Provides endpoints for checking task status
- Returns task results when complete

### 3. RabbitMQ (Message Queue)
- Stores tasks in queues until they are processed
- Ensures tasks are not lost if workers are down
- Distributes tasks to available workers
- Provides reliability and scalability for task processing

### 4. Redis (Result Backend)
- Stores task results and status information
- Provides fast access to task status for polling
- Acts as a cache for completed task results

### 5. Celery Worker
- Consumes tasks from RabbitMQ
- Processes media correction tasks
- Updates task status in the Django API
- Handles errors and retries

### 6. File System
- Shared storage accessible by both the Django API and Celery workers
- Stores input files and correction results

## Task Flow

1. **Task Submission**:
   - User submits a correction request through the frontend
   - Frontend sends a POST request to the appropriate API endpoint
   - Django API creates a task record and returns a task ID
   - API enqueues the task in RabbitMQ

2. **Task Processing**:
   - Celery worker picks up the task from RabbitMQ
   - Worker updates task status to "PROCESSING"
   - Worker performs the correction using the appropriate function
   - Worker updates task status to "COMPLETED" or "FAILED"

3. **Result Retrieval**:
   - Frontend polls the API for task status
   - When task is complete, API returns the result
   - Frontend updates the UI to show completion

## Kubernetes Deployment

The system is deployed using Kubernetes with the following components:

1. **RabbitMQ Deployment**:
   - Runs the RabbitMQ message broker
   - Persists queue data using a PersistentVolumeClaim
   - Exposes AMQP port (5672) and management UI port (15672)

2. **Redis Deployment**:
   - Runs the Redis result backend
   - Persists result data using a PersistentVolumeClaim
   - Exposes Redis port (6379)

3. **Celery Worker Deployment**:
   - Runs multiple Celery worker instances
   - Connects to RabbitMQ and Redis
   - Mounts shared storage for file access
   - Scales horizontally for increased processing capacity

## Docker Compose (Development)

For local development, a Docker Compose configuration is provided that sets up:
- RabbitMQ container
- Redis container
- Celery worker container

## Benefits of This Architecture

1. **Scalability**: Workers can be scaled independently based on processing needs
2. **Resilience**: Tasks persist in the queue if workers are down
3. **Resource Efficiency**: Heavy processing is offloaded from the API server
4. **User Experience**: Frontend can show progress and handle long-running tasks gracefully
5. **Fault Tolerance**: Failed tasks can be retried without losing progress
