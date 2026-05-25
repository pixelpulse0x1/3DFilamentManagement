#!/bin/sh
set -e

# Ensure data directories exist at runtime (after volume mount)
mkdir -p /data/database

# Start the application
exec python -c "from app import init_db; init_db(); from app import app; app.run(host='0.0.0.0', port=3155, debug=False)"
