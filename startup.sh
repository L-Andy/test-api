#!/bin/bash
set -e

echo "Starting Wellness Connect API..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-6000} --workers 1
