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

echo "Starting LiveKit Agent Worker..."
# Use "start" instead of "dev" for production deployment on Render!
python agent.py start
