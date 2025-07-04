#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Default environment
ENVIRONMENT="development"
SKIP_TESTS=false
BUILD_FRONTEND=true
BUILD_BACKEND=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --frontend-only)
            BUILD_BACKEND=false
            shift
            ;;
        --backend-only)
            BUILD_FRONTEND=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (development, staging, production)"
            echo "  --skip-tests            Skip running tests"
            echo "  --frontend-only         Only build frontend"
            echo "  --backend-only          Only build backend"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Starting build process for $ENVIRONMENT environment"

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please create one based on .env.example"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Frontend build
if [ "$BUILD_FRONTEND" = true ]; then
    print_status "Building frontend..."
    cd frontend
    
    # Install dependencies
    print_status "Installing frontend dependencies..."
    npm ci --legacy-peer-deps
    
    # Run tests
    if [ "$SKIP_TESTS" = false ]; then
        print_status "Running frontend tests..."
        npm run test || {
            print_error "Frontend tests failed"
            exit 1
        }
        
        print_status "Running frontend linting..."
        npm run lint || {
            print_error "Frontend linting failed"
            exit 1
        }
        
        print_status "Running frontend type checking..."
        npm run type-check || {
            print_error "Frontend type checking failed"
            exit 1
        }
    fi
    
    # Build based on environment
    case $ENVIRONMENT in
        production)
            print_status "Building frontend for production..."
            npm run build:prod
            ;;
        staging)
            print_status "Building frontend for staging..."
            npm run build:staging
            ;;
        *)
            print_status "Building frontend for development..."
            npm run build
            ;;
    esac
    
    print_status "Frontend build completed"
    cd ..
fi

# Backend build
if [ "$BUILD_BACKEND" = true ]; then
    print_status "Building backend..."
    cd backend
    
    # Install dependencies
    print_status "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Run tests
    if [ "$SKIP_TESTS" = false ]; then
        print_status "Running backend tests..."
        python manage.py test || {
            print_error "Backend tests failed"
            exit 1
        }
    fi
    
    # Collect static files
    print_status "Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Check for migrations
    print_status "Checking for pending migrations..."
    python manage.py makemigrations --check || {
        print_warning "There are pending migrations"
    }
    
    print_status "Backend build completed"
    cd ..
fi

# Docker build
if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "staging" ]; then
    print_status "Building Docker images..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.production.yml build
    else
        docker-compose -f docker-compose.yml build
    fi
    
    print_status "Docker build completed"
fi

print_status "Build process completed successfully!"

# Output summary
echo ""
echo "=== Build Summary ==="
echo "Environment: $ENVIRONMENT"
echo "Frontend built: $BUILD_FRONTEND"
echo "Backend built: $BUILD_BACKEND"
echo "Tests skipped: $SKIP_TESTS"
echo "===================="