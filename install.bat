@echo off
cd api

:: Create a virtual environment if it doesn't exist yet
if not exist venv (
	python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Install dependencies from requirements.txt
pip install -r requirements.txt

cd ..\frontend

npm install