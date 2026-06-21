#!/bin/bash
# Start FastAPI server in the background
uvicorn main:app --host 0.0.0.0 --port $PORT &

# Start the LiveKit agent worker in the foreground
python agent.py start   