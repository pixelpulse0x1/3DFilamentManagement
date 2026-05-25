#!/bin/sh
set -e

mkdir -p /data/database

exec python -c "from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=3155, debug=False)"
