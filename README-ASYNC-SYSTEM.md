# Miniware Asynchronous Task Processing System

This README provides comprehensive instructions for running, configuring, and debugging the asynchronous task processing system for media corrections.

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Running the System](#running-the-system)
5. [Configuration](#configuration)
6. [Debugging](#debugging)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Common Issues and Solutions](#common-issues-and-solutions)
9. [Architecture Details](#architecture-details)

## System Overview

The asynchronous task processing system uses RabbitMQ and Celery to handle media correction tasks. Instead of processing corrections synchronously, the system:

1. Receives correction requests from the frontend
2. Creates task records in the database
3. Enqueues tasks in RabbitMQ
4. Processes tasks asynchronously using Celery workers
5. Updates task status and returns results when complete

This approach provides better scalability, resilience, and user experience for processing media files.

## Prerequisites

- **Docker and Docker Compose**: Required for running RabbitMQ and Redis containers
- **Python 3.9+**: Required for the Django API and Celery worker
- **Node.js 16+**: Required for the frontend (if running separately)
- **Kubernetes and kubectl** (optional): Required for Kubernetes deployment

## Installation

### Windows

1. Clone the repository:
   ```
   git clone https://github.com/your-org/miniware.git
   cd miniware
   ```

2. Install Python dependencies:
   ```
   cd api
   pip install -r requirements.txt
   cd ..
   ```

3. Build the worker image:
   ```
   docker build -t miniware-celery-worker:latest .\worker
   ```

### Linux/macOS

1. Clone the repository:
   ```
   git clone https://github.com/your-org/miniware.git
   cd miniware
   ```

2. Install Python dependencies:
   ```
   cd api
   pip install -r requirements.txt
   cd ..
   ```

3. Build the worker image:
   ```
   docker build -t miniware-celery-worker:latest ./worker
   ```

4. Make scripts executable:
   ```
   chmod +x start-async-system.sh stop-async-system.sh
   ```

## Running the System

### Using Provided Scripts

#### Windows

1. Start the system:
   ```
   start-async-system.bat
   ```

2. Stop the system:
   ```
   stop-async-system.bat
   ```

#### Linux/macOS

1. Start the system:
   ```
   ./start-async-system.sh
   ```

2. Stop the system:
   ```
   ./stop-async-system.sh
   ```

### Manual Startup

If you prefer to start components individually:

1. Start RabbitMQ and Redis:
   ```
   docker-compose up -d rabbitmq redis
   ```

2. Apply Django migrations:
   ```
   cd api
   python manage.py makemigrations corr
   python manage.py migrate
   ```

3. Start the Django API:
   ```
   cd api
   python manage.py runserver 0.0.0.0:8000
   ```

4. Start the Celery worker:
   ```
   cd worker
   celery -A worker worker --loglevel=info
   ```

5. Start the frontend (if running separately):
   ```
   cd frontend
   npm install
   npm run dev
   ```

## Configuration

### RabbitMQ Configuration

RabbitMQ configuration is defined in `docker-compose.yml`. You can modify:

- **Username/Password**: Change `RABBITMQ_DEFAULT_USER` and `RABBITMQ_DEFAULT_PASS`
- **Port Mapping**: Change the port mapping (default: 5672 for AMQP, 15672 for Management UI)

If you change these settings, also update them in:
- `api/mwlocal/settings.py` (CELERY_BROKER_URL)
- `worker/worker.py` (broker_url)

### Redis Configuration

Redis configuration is also in `docker-compose.yml`. You can modify:

- **Port Mapping**: Change the port mapping (default: 6379)

If you change these settings, also update them in:
- `api/mwlocal/settings.py` (CELERY_RESULT_BACKEND)
- `worker/worker.py` (result_backend)

### Celery Worker Configuration

Celery worker settings are in `worker/worker.py`. You can modify:

- **Concurrency**: Change the number of worker processes
- **Task Time Limit**: Change the maximum time a task can run
- **Logging Level**: Change the logging verbosity

Example:
```python
app.conf.worker_concurrency = 4  # Number of worker processes
app.conf.task_time_limit = 60 * 60  # 1 hour
```

### Django API Configuration

Django API settings are in `api/mwlocal/settings.py`. You can modify:

- **Celery Settings**: Change broker URL, result backend, etc.
- **Database Settings**: Change database configuration
- **Allowed Hosts**: Add hosts that can access the API

## Debugging

### Checking Task Status

1. **Via API**:
   ```
   GET /corr/tasks/<task_id>/
   ```

2. **Via RabbitMQ Management UI**:
   - Open http://localhost:15672
   - Login with username `miniware` and password `miniware_password`
   - Go to "Queues" to see pending tasks
   - Go to "Exchanges" to see message routing

3. **Via Django Admin**:
   - Open http://localhost:8000/admin
   - Login with your admin credentials
   - Go to "Corr" > "Correction tasks"

### Viewing Logs

#### Django API Logs

Django API logs are output to the console where you started the server.

#### Celery Worker Logs

Celery worker logs are output to the console where you started the worker, or to the Docker logs if running in a container:

```
docker logs -f miniware_celery-worker_1
```

#### RabbitMQ Logs

```
docker logs -f miniware_rabbitmq_1
```

#### Redis Logs

```
docker logs -f miniware_redis_1
```

### Common Debugging Techniques

1. **Check Task Status**:
   ```python
   from corr.models import CorrectionTask
   task = CorrectionTask.objects.get(task_id='your-task-id')
   print(f"Status: {task.status}")
   print(f"Result: {task.result}")
   print(f"Error: {task.error_message}")
   ```

2. **Inspect RabbitMQ Queues**:
   - Check queue lengths in the RabbitMQ Management UI
   - Look for messages stuck in queues

3. **Run Celery Worker in Debug Mode**:
   ```
   celery -A worker worker --loglevel=debug
   ```

4. **Test Task Processing Manually**:
   ```python
   from worker.worker import process_correction
   result = process_correction.delay('task-id', 'audio', '/path/to/file.mp3', '/output/folder', {})
   print(result.get())  # This will block until the task completes
   ```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured to access your cluster
- Docker registry for storing images

### Deployment Steps

#### Windows

```
k8s\deploy.bat
```

#### Linux/macOS

```
./k8s/deploy.sh
```

### Manual Deployment

1. Apply persistent volume claims:
   ```
   kubectl apply -f k8s/rabbitmq-deployment.yaml
   kubectl apply -f k8s/redis-deployment.yaml
   ```

2. Wait for RabbitMQ and Redis to be ready:
   ```
   kubectl wait --for=condition=available --timeout=300s deployment/rabbitmq
   kubectl wait --for=condition=available --timeout=300s deployment/redis
   ```

3. Deploy API and run migrations:
   ```
   kubectl apply -f k8s/api-deployment.yaml
   kubectl apply -f k8s/run-migrations.yaml
   ```

4. Deploy Celery workers:
   ```
   kubectl apply -f k8s/celery-worker-deployment.yaml
   ```

### Accessing Services

1. API:
   ```
   kubectl port-forward svc/api-service 8000:8000
   ```

2. RabbitMQ Management UI:
   ```
   kubectl port-forward svc/rabbitmq 15672:15672
   ```

## Common Issues and Solutions

### RabbitMQ Connection Issues

**Symptom**: Celery worker can't connect to RabbitMQ

**Solutions**:
- Check if RabbitMQ container is running: `docker ps | grep rabbitmq`
- Verify RabbitMQ credentials in settings
- Check network connectivity between services
- Restart RabbitMQ: `docker-compose restart rabbitmq`

### Task Stuck in Pending State

**Symptom**: Task status remains "PENDING" for a long time

**Solutions**:
- Check if Celery worker is running: `docker ps | grep celery-worker`
- Check Celery worker logs for errors
- Verify task is in the RabbitMQ queue
- Restart Celery worker: `docker-compose restart celery-worker`

### Database Migration Issues

**Symptom**: Django migrations fail

**Solutions**:
- Check Django migration logs
- Run migrations manually: `python manage.py migrate --traceback`
- Reset migrations if necessary (development only): 
  ```
  python manage.py migrate corr zero
  python manage.py makemigrations corr
  python manage.py migrate corr
  ```

### File Access Issues

**Symptom**: Worker can't access files

**Solutions**:
- Check file paths and permissions
- Ensure shared volumes are properly mounted
- Verify file exists at the specified path
- Check if paths use correct slashes for the operating system (/ for Linux, \ for Windows)

## Architecture Details

### Components

1. **Frontend (Svelte)**:
   - Provides user interface
   - Sends API requests
   - Polls for task status

2. **Django API**:
   - Receives correction requests
   - Creates task records
   - Enqueues tasks in RabbitMQ
   - Provides task status endpoints

3. **RabbitMQ**:
   - Message broker for task queue
   - Ensures tasks are not lost
   - Distributes tasks to workers

4. **Redis**:
   - Result backend for Celery
   - Stores task results and status

5. **Celery Worker**:
   - Consumes tasks from RabbitMQ
   - Processes media corrections
   - Updates task status

### Data Flow

1. User submits correction request via frontend
2. Frontend sends request to Django API
3. API creates task record and returns task ID
4. API enqueues task in RabbitMQ
5. Celery worker picks up task from RabbitMQ
6. Worker processes task and updates status
7. Frontend polls API for task status
8. When task completes, frontend displays result

### File Structure

```
miniware/
├── api/                  # Django API
│   ├── corr/             # Correction app
│   │   ├── models.py     # Task model
│   │   ├── tasks.py      # Task creation
│   │   ├── views.py      # API endpoints
│   │   └── urls.py       # URL routing
│   └── mwlocal/          # Django project
│       ├── celery.py     # Celery config
│       └── settings.py   # Django settings
├── worker/               # Celery worker
│   ├── worker.py         # Worker application
│   ├── Dockerfile        # Worker container
│   └── requirements.txt  # Worker dependencies
├── docker-compose.yml    # Local development
├── k8s/                  # Kubernetes configs
├── start-async-system.bat/sh  # Start scripts
└── stop-async-system.bat/sh   # Stop scripts
```
