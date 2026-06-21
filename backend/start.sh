#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists (for local development)
# Render does not need this as it installs dependencies globally
if [ -d "venv/Scripts" ]; then
    source venv/Scripts/activate
elif [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

# Use the PORT environment variable provided by Render, or default to 8000 locally
PORT=${PORT:-8000}

# Bind to 0.0.0.0 so Render can detect the open port!
echo "Starting Backend API (FastAPI) on 0.0.0.0:$PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT