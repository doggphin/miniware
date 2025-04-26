@echo off
REM Start the async processing system using Docker Compose

REM Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if Docker Compose is installed
where docker-compose >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Build the worker image
echo Building Celery worker image...
docker build -t miniware-celery-worker:latest .\worker

REM Start the services
echo Starting RabbitMQ, Redis, and Celery worker...
docker-compose up -d

REM Apply Django migrations
echo Applying Django migrations...
cd api
python manage.py makemigrations corr
python manage.py migrate
cd ..

REM Start the Django API server
echo Starting Django API server...
start /b cmd /c "cd api && python manage.py runserver 0.0.0.0:8000"

echo System is now running!
echo RabbitMQ Management UI: http://localhost:15672 (username: miniware, password: miniware_password)
echo Django API: http://localhost:8000
echo To stop the system, run: docker-compose down
