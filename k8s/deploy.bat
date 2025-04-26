@echo off
REM Deploy the async processing system to Kubernetes

REM Check if kubectl is installed
where kubectl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo kubectl is not installed. Please install kubectl first.
    exit /b 1
)

REM Check if Kubernetes cluster is accessible
kubectl cluster-info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Cannot connect to Kubernetes cluster. Please check your kubeconfig.
    exit /b 1
)

REM Build and push Docker images
echo Building and pushing Docker images...
docker build -t miniware-celery-worker:latest .\worker
docker build -t miniware-api:latest .\api

REM Apply Kubernetes configurations
echo Applying Kubernetes configurations...

REM Create persistent volume claims
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

REM Wait for RabbitMQ and Redis to be ready
echo Waiting for RabbitMQ and Redis to be ready...
kubectl wait --for=condition=available --timeout=300s deployment/rabbitmq
kubectl wait --for=condition=available --timeout=300s deployment/redis

REM Deploy API and run migrations
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/run-migrations.yaml

REM Wait for migrations to complete
echo Waiting for migrations to complete...
kubectl wait --for=condition=complete --timeout=300s job/django-migrations

REM Deploy Celery workers
kubectl apply -f k8s/celery-worker-deployment.yaml

echo Deployment completed successfully!
echo To access the API, run: kubectl port-forward svc/api-service 8000:8000
echo To access RabbitMQ Management UI, run: kubectl port-forward svc/rabbitmq 15672:15672
