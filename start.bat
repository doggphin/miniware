@echo off
start cmd /k "cd api && call venv\Scripts\activate.bat && python manage.py runserver"
start cmd /k "cd frontend && npm run dev"

:: Wait for a few seconds to ensure the servers start
timeout /t 10 /nobreak

:: Open the browser at the specified URL
start http://localhost:5173/corr