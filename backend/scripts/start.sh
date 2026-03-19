#!/bin/sh

# Exit on error and undefined variables
set -o errexit
set -o nounset

# The docker-compose.yml uses `depends_on` with `service_healthy` for postgres,
# which is generally sufficient to ensure the database is ready when the backend starts.
# For more complex scenarios, a dedicated wait script could be added here.

echo "Starting Uvicorn server in development mode with auto-reload..."

# The 'exec' command replaces the shell process with the uvicorn process,
# which is a good practice for running services in containers.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload