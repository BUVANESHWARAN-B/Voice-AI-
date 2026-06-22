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
# Trick Render into staying alive by explicitly binding to 0.0.0.0
PORT=${PORT:-10000}
python3 -c "import http.server, socketserver; Handler = http.server.SimpleHTTPRequestHandler; httpd = socketserver.TCPServer(('0.0.0.0', $PORT), Handler); print('Serving at port', $PORT); httpd.serve_forever()" &

echo "Starting LiveKit Agent Worker..."
# Use "start" instead of "dev" for production deployment on Render!
exec python agent.py start
