#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

# Default values
ENVIRONMENT="development"
PULL_IMAGES=false
REBUILD=false
MIGRATE=true
COLLECTSTATIC=true
SKIP_TESTS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --pull)
            PULL_IMAGES=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --no-migrate)
            MIGRATE=false
            shift
            ;;
        --no-collectstatic)
            COLLECTSTATIC=false
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (development, staging, production)"
            echo "  --pull                   Pull latest images before deployment"
            echo "  --rebuild                Rebuild images before deployment"
            echo "  --no-migrate             Skip database migrations"
            echo "  --no-collectstatic       Skip static file collection"
            echo "  --skip-tests             Skip running tests"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_header "Starting deployment for $ENVIRONMENT environment"

# Validate environment
case $ENVIRONMENT in
    development)
        COMPOSE_FILE="docker-compose.yml"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    production)
        COMPOSE_FILE="docker-compose.production.yml"
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        print_error "Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please create one based on .env.example"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

print_status "Using compose file: $COMPOSE_FILE"

# Run tests if not skipped
if [ "$SKIP_TESTS" = false ] && [ "$ENVIRONMENT" != "development" ]; then
    print_status "Running tests..."
    
    # Backend tests
    print_status "Running backend tests..."
    cd backend
    python -m pytest || {
        print_error "Backend tests failed"
        exit 1
    }
    cd ..
    
    # Frontend tests
    print_status "Running frontend tests..."
    cd frontend
    npm run test:ci || {
        print_error "Frontend tests failed"
        exit 1
    }
    cd ..
    
    print_status "All tests passed!"
fi

# Pull images if requested
if [ "$PULL_IMAGES" = true ]; then
    print_status "Pulling latest images..."
    docker-compose -f $COMPOSE_FILE pull
fi

# Rebuild images if requested
if [ "$REBUILD" = true ]; then
    print_status "Rebuilding images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start services
print_status "Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Run migrations if enabled
if [ "$MIGRATE" = true ]; then
    print_status "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec -T backend python manage.py migrate
fi

# Collect static files if enabled and not development
if [ "$COLLECTSTATIC" = true ] && [ "$ENVIRONMENT" != "development" ]; then
    print_status "Collecting static files..."
    docker-compose -f $COMPOSE_FILE exec -T backend python manage.py collectstatic --noinput
fi

# Create superuser in development
if [ "$ENVIRONMENT" = "development" ]; then
    print_status "Creating superuser for development..."
    docker-compose -f $COMPOSE_FILE exec -T backend python manage.py createsuperuser --noinput --username admin --email admin@example.com || echo "Superuser already exists"
fi

# Show service status
print_status "Checking service status..."
docker-compose -f $COMPOSE_FILE ps

# Display access URLs
print_header "Deployment complete!"
echo ""
echo "=== Service URLs ==="
case $ENVIRONMENT in
    development)
        echo "Frontend: http://localhost:3000"
        echo "Backend: http://localhost:8000"
        echo "Backend Admin: http://localhost:8000/admin"
        ;;
    staging)
        echo "Frontend: http://localhost:3000"
        echo "Backend: http://localhost:8000"
        echo "Nginx: http://localhost:80"
        ;;
    production)
        echo "Frontend: http://localhost:3000"
        echo "Backend: http://localhost:8000"
        echo "Nginx: http://localhost:80"
        echo "Nginx HTTPS: https://localhost:443"
        ;;
esac
echo "===================="

print_status "Deployment completed successfully!"