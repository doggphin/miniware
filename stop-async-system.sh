#!/bin/bash

# Stop the async processing system

# Stop the Django API server
echo "Stopping Django API server..."
pkill -f "python manage.py runserver"

# Stop Docker Compose services
echo "Stopping Docker Compose services..."
docker-compose down

echo "System stopped successfully!"
