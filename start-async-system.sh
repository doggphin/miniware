#!/bin/bash

# Start the async processing system using Docker Compose

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build the worker image
echo "Building Celery worker image..."
docker build -t miniware-celery-worker:latest ./worker

# Start the services
echo "Starting RabbitMQ, Redis, and Celery worker..."
docker-compose up -d

# Apply Django migrations
echo "Applying Django migrations..."
cd api
python manage.py makemigrations corr
python manage.py migrate
cd ..

# Start the Django API server
echo "Starting Django API server..."
cd api
python manage.py runserver 0.0.0.0:8000 &
cd ..

echo "System is now running!"
echo "RabbitMQ Management UI: http://localhost:15672 (username: miniware, password: miniware_password)"
echo "Django API: http://localhost:8000"
echo "To stop the system, run: docker-compose down"
