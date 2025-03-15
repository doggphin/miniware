#!/bin/bash

# Start the API server in the background
gnome-terminal -- bash -c "cd api && python manage.py runserver; exec bash"

# Start the frontend server in the background
gnome-terminal -- bash -c "cd frontend && npm run dev; exec bash"

# Wait for a few seconds to ensure the servers start
sleep 10

# Open the browser at the specified URL
xdg-open http://localhost:5173/correct
