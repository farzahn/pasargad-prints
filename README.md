# Pasargad Prints E-commerce Platform

A modern, full-stack e-commerce platform for unique 3D-printed products built with Django REST Framework and React with TypeScript.

## ⚠️ Important: Environment Setup

The application uses a consolidated `.env` file for all configuration. The project includes a comprehensive environment configuration that supports development, staging, and production environments.

### Environment Variables

The main `.env` file contains all necessary configuration for both backend and frontend services:

```bash
# Core Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
NODE_ENV=development

# Database Configuration
DB_NAME=pasargad_prints
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Stripe Payment Settings
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pasargadprints.com

# Goshippo Shipping Configuration
GOSHIPPO_API_KEY=shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15
GOSHIPPO_TEST_MODE=True
BUSINESS_NAME=Pasargad Prints
BUSINESS_ADDRESS=123 Main Street
BUSINESS_CITY=New York
BUSINESS_STATE=NY
BUSINESS_ZIP=10001
BUSINESS_COUNTRY=US
BUSINESS_PHONE=+1-555-123-4567
BUSINESS_EMAIL=shipping@pasargadprints.com

# Redis and Cache (Optional)
USE_REDIS_CACHE=False
REDIS_URL=redis://127.0.0.1:6379/1

# CDN and Storage (Optional)
USE_CDN=False
USE_S3=False

# Feature Flags
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_WISHLIST=true
VITE_ENABLE_PRODUCT_COMPARISON=true
```

**Required Configuration:**
- Get Stripe test keys from https://stripe.com/docs/keys
- Get Goshippo API key from https://apps.goshippo.com/settings/api or use test key provided
- Use Gmail App Password for email (not your regular password)
- Generate a secure SECRET_KEY for production
- The `.env` file is the main configuration file and should NOT be ignored in git (it contains development defaults)

## 🚀 Features

### Frontend (React + TypeScript)
- **Modern UI/UX**: Clean, responsive design with Tailwind CSS
- **Product Catalog**: Browse products with advanced filtering, search, and sorting
- **Shopping Cart**: Persistent cart for both guests and authenticated users
- **User Authentication**: JWT-based auth with "remember me" functionality
- **Product Reviews**: Rating system and customer reviews
- **Secure Checkout**: Stripe integration for payment processing
- **Wishlist**: Save products for later purchase
- **Product Comparison**: Compare multiple products side-by-side
- **Dark Mode**: Toggle between light and dark themes
- **Admin Dashboard**: Complete admin interface for managing products, orders, and users
- **Analytics**: Real-time statistics and performance monitoring
- **PWA Support**: Progressive Web App capabilities
- **SEO Optimized**: Structured data and meta tags

### Backend (Django + PostgreSQL)
- **RESTful API**: Django REST Framework with comprehensive endpoints
- **PostgreSQL Database**: Robust data management with advanced queries
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Shopping Cart Persistence**: Session-based for guests, user-based for members
- **Order Management**: Complete order lifecycle tracking with email notifications
- **Shipping Integration**: Goshippo API for shipping rates, labels, and tracking
- **Email Integration**: Gmail SMTP for notifications with HTML templates
- **Image Management**: Automatic image resizing and optimization
- **Promotions System**: Discount codes and promotional campaigns
- **Analytics Tracking**: User behavior and purchase analytics
- **Recommendations**: Product recommendation engine
- **Low Stock Alerts**: Automated inventory management
- **Celery Integration**: Asynchronous task processing
- **Redis Caching**: Optional caching for improved performance

### Security Features
- Environment variable configuration
- XSS and CSRF protection
- Rate limiting middleware
- Secure password hashing
- CORS configuration
- Session timeout management
- Security headers middleware
- Input validation and sanitization

## 🛠️ Tech Stack

### Backend
- **Django 4.2.7** - Python web framework
- **Django REST Framework 3.14.0** - API framework
- **PostgreSQL 15** - Primary database
- **Redis 5.0.1** - Caching and session storage
- **Celery 5.3.4** - Asynchronous task queue
- **Stripe API 9.12.0** - Payment processing
- **Goshippo 4.9.0** - Shipping API integration
- **Pillow 10.1.0** - Image processing
- **psycopg2-binary 2.9.9** - PostgreSQL adapter
- **Gunicorn 21.2.0** - WSGI server

### Frontend
- **React 19 with TypeScript** - UI framework
- **Vite 7.0.0** - Build tool and dev server
- **Redux Toolkit 2.8.2** - State management
- **React Router v7.6.3** - Client-side routing
- **Tailwind CSS 3.4.0** - Utility-first CSS framework
- **Axios 1.10.0** - HTTP client
- **React Hook Form 7.59.0** - Form management
- **React Helmet Async** - SEO and meta tags
- **Recharts 3.0.2** - Data visualization
- **React Toastify** - Notifications

### DevOps & Infrastructure
- **Docker & Docker Compose** - Containerization
- **PostgreSQL 15** - Database service
- **Nginx** - Reverse proxy and static file serving
- **Environment-based configuration** - Multi-environment support
- **Health checks** - Service monitoring

## 📦 Project Structure

```
pasargad-prints/
├── backend/
│   ├── pasargad_prints/     # Main Django project
│   │   ├── settings.py      # Django settings
│   │   ├── urls.py          # URL routing
│   │   └── wsgi.py          # WSGI configuration
│   ├── apps/
│   │   ├── users/           # User management & authentication
│   │   ├── products/        # Product catalog & search
│   │   ├── cart/            # Shopping cart functionality
│   │   ├── orders/          # Order management & tracking
│   │   ├── payments/        # Stripe payment processing
│   │   ├── promotions/      # Discount codes & campaigns
│   │   ├── recommendations/ # Product recommendations
│   │   ├── analytics/       # Usage analytics
│   │   ├── wishlist/        # User wishlist
│   │   └── utils/           # Shared utilities
│   ├── templates/           # Email templates
│   ├── media/              # User uploaded files
│   ├── static/             # Static files
│   ├── scripts/            # Management scripts
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   │   ├── admin/       # Admin-specific components
│   │   │   └── banners/     # Banner components
│   │   ├── pages/          # Route pages
│   │   │   └── admin/       # Admin dashboard pages
│   │   ├── store/          # Redux store and slices
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   └── types/          # TypeScript type definitions
│   ├── public/             # Static assets
│   ├── package.json
│   └── Dockerfile
├── monitoring/             # Monitoring configuration
├── nginx.conf             # Nginx configuration
├── docker-compose.yml     # Development environment
├── docker-compose.production.yml  # Production environment
├── .env                   # Environment variables (main config)
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 🚀 Quick Start with Docker (Recommended)

1. **Clone the repository:**
```bash
git clone <repository-url>
cd pasargad-prints
```

2. **Configure environment variables:**
   - The project includes a comprehensive `.env` file with development defaults
   - Update the `.env` file with your specific configuration:
     - Add your Stripe API keys
     - Configure your email settings
     - Set a secure SECRET_KEY for production

3. **Build and start all services:**
```bash
docker-compose up --build
```

4. **In a new terminal, run database migrations:**
```bash
docker-compose exec backend python manage.py migrate
```

5. **Create a superuser account:**
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. **Load sample data (optional):**
```bash
docker-compose exec backend python manage.py loaddata sample_data.json
```

7. **🎉 Access the application:**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **Django Admin**: http://localhost:8000/admin

### 🖥️ Application Ports

- **Frontend (React)**: Port 3000
- **Backend (Django)**: Port 8000
- **Database (PostgreSQL)**: Port 5432 (internal)
- **Redis (optional)**: Port 6379 (when enabled)

## 🔄 Managing the Application

### Starting the Platform
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Start with rebuild
docker-compose up --build
```

### Stopping the Platform
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

### Useful Commands
```bash
# View logs
docker-compose logs -f

# Execute commands in backend container
docker-compose exec backend python manage.py <command>

# Execute commands in frontend container
docker-compose exec frontend npm run <command>

# Access backend shell
docker-compose exec backend python manage.py shell

# Access database
docker-compose exec db psql -U postgres -d pasargad_prints
```

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📝 API Documentation

### Authentication Endpoints
- `POST /api/users/auth/login/` - User login
- `POST /api/users/auth/register/` - User registration
- `POST /api/users/auth/refresh/` - Refresh JWT token

### Product Endpoints
- `GET /api/products/` - List products (with filtering)
- `GET /api/products/<id>/` - Product details
- `GET /api/products/categories/` - List categories
- `GET /api/products/featured/` - Featured products

### Cart Endpoints
- `GET /api/cart/` - Get cart
- `POST /api/cart/add/` - Add to cart
- `PUT /api/cart/items/<id>/` - Update cart item
- `DELETE /api/cart/items/<id>/remove/` - Remove from cart

### User Endpoints
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update profile
- `POST /api/users/password/change/` - Change password

## 🔐 Environment Variables

The application uses a comprehensive `.env` file that serves both backend and frontend. Key variables include:

### Core Application
- `SECRET_KEY` - Django secret key (required)
- `DEBUG` - Debug mode (True/False)
- `NODE_ENV` - Environment (development/staging/production)

### Database Configuration
- `DB_NAME` - PostgreSQL database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)

### API Configuration
- `VITE_API_URL` - Backend API URL for frontend
- `VITE_API_BASE_URL` - Base API URL
- `FRONTEND_URL` - Frontend URL for CORS

### Payment Processing
- `STRIPE_PUBLISHABLE_KEY` - Stripe public key
- `STRIPE_SECRET_KEY` - Stripe secret key (required)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `VITE_STRIPE_PUBLISHABLE_KEY` - Stripe public key for frontend

### Email Configuration
- `EMAIL_HOST_USER` - SMTP email address
- `EMAIL_HOST_PASSWORD` - SMTP password or app password
- `DEFAULT_FROM_EMAIL` - Default sender email

### Shipping Configuration (Goshippo)
- `GOSHIPPO_API_KEY` - Goshippo API key (test: shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15)
- `GOSHIPPO_TEST_MODE` - Enable test mode (True/False)
- `BUSINESS_NAME` - Your business name for shipping labels
- `BUSINESS_ADDRESS` - Your business address
- `BUSINESS_CITY` - Your business city
- `BUSINESS_STATE` - Your business state
- `BUSINESS_ZIP` - Your business ZIP code
- `BUSINESS_COUNTRY` - Your business country (default: US)
- `BUSINESS_PHONE` - Your business phone
- `BUSINESS_EMAIL` - Your business email

### Optional Services
- `USE_REDIS_CACHE` - Enable Redis caching (True/False)
- `REDIS_URL` - Redis connection URL
- `USE_CDN` - Enable CDN for static files (True/False)
- `USE_S3` - Enable AWS S3 for file storage (True/False)

### Feature Flags
- `VITE_ENABLE_DARK_MODE` - Enable dark mode toggle
- `VITE_ENABLE_WISHLIST` - Enable wishlist feature
- `VITE_ENABLE_PRODUCT_COMPARISON` - Enable product comparison
- `VITE_ENABLE_ANALYTICS` - Enable analytics tracking
- `VITE_ENABLE_PWA` - Enable PWA features

### Analytics & Monitoring
- `VITE_GOOGLE_ANALYTICS_ID` - Google Analytics ID
- `VITE_SENTRY_DSN` - Sentry error tracking DSN
- `VITE_ENABLE_PERFORMANCE_MONITORING` - Enable performance monitoring

## 🧪 Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📈 Performance Optimizations

- Image optimization with automatic resizing
- Pagination for product listings
- Efficient database queries with select_related/prefetch_related
- Frontend code splitting with React lazy loading
- Redis caching (ready to implement)

## 🔒 Security Best Practices

- All sensitive data in environment variables
- JWT tokens with refresh mechanism
- HTTPS enforcement in production
- Input validation and sanitization
- SQL injection protection with Django ORM
- XSS protection with React's built-in escaping

## 🐳 Docker Setup

### Development Environment
```bash
# Start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Production Environment
```bash
# Use production docker-compose file
docker-compose -f docker-compose.production.yml up --build -d

# Run migrations in production
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### Staging Environment
```bash
# Use staging docker-compose file
docker-compose -f docker-compose.staging.yml up --build -d
```

### Docker Services
- **backend**: Django application (port 8000)
- **frontend**: React application (port 3000)
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis cache (optional, port 6379)

## 🚢 Deployment

### Production Checklist
1. Set `DEBUG=False` in production
2. Generate new `SECRET_KEY`
3. Configure production database
4. Set up SSL certificates
5. Configure production email settings
6. Set up monitoring and logging
7. Configure backup strategy
8. Update environment variables for production
9. Set up proper CORS origins
10. Configure static file serving

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💬 Support

For support, email support@pasargadprints.com or create an issue in the repository.# CI/CD Test - Fourth Iteration
# Fifth Iteration Test
