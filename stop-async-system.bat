@echo off
REM Stop the async processing system

REM Stop the Django API server
echo Stopping Django API server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *runserver*" >nul 2>&1

REM Stop Docker Compose services
echo Stopping Docker Compose services...
docker-compose down

echo System stopped successfully!
