#!/bin/bash

# Change directory to 'api'
cd api

# Create a virtual environment if it doesn't exist yet
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Change directory to 'frontend'
cd ../frontend

# Install npm dependencies
npm install