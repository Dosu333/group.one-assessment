#!/bin/bash

# Wait for database to be ready
echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

exec "$@"