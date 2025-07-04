#!/bin/bash
set -e

echo "Starting deployment process..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput

# Create superuser if needed
echo "Creating superuser if needed..."
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser --noinput || echo "Superuser already exists"

# Check health
echo "Checking service health..."
docker-compose -f docker-compose.production.yml ps

echo "Deployment complete!"
echo "Frontend available at: http://localhost"
echo "Backend admin available at: http://localhost/admin"