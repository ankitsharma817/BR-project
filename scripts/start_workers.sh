#!/usr/bin/env bash
# Start all Celery workers
set -e
export PYTHONPATH="$(pwd)"

echo "Starting matching worker..."
celery -A api.tasks.celery_app worker \
  --queues=matching \
  --concurrency=2 \
  --loglevel=info \
  --hostname=matching@%h &

echo "Starting embedding worker..."
celery -A api.tasks.celery_app worker \
  --queues=embedding \
  --concurrency=1 \
  --loglevel=info \
  --hostname=embedding@%h &

echo "Starting email + webhook worker..."
celery -A api.tasks.celery_app worker \
  --queues=email,webhooks \
  --concurrency=4 \
  --loglevel=info \
  --hostname=misc@%h &

echo "Starting Flower monitoring on port 5555..."
celery -A api.tasks.celery_app flower --port=5555 &

echo "All workers started."
wait
