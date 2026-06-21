#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/Scripts/activate

# Start the LiveKit Agent worker
echo "Starting LiveKit Agent Worker..."
python agent.py dev
