#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists (for local development)
if [ -d "venv/Scripts" ]; then
    source venv/Scripts/activate
elif [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

echo "Starting Dummy Web Server to satisfy Render..."
# Trick Render into staying alive by binding to the expected port
PORT=${PORT:-10000}
python -m http.server $PORT &

echo "Starting LiveKit Agent Worker..."
# Use "start" instead of "dev" for production deployment on Render!
python agent.py dev
