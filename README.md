# Pasargad Prints E-commerce Platform

A modern, full-stack e-commerce platform for unique 3D-printed products built with Django REST Framework and React.

## 🚀 Features

### Frontend
- **Modern UI/UX**: Clean, responsive design with Tailwind CSS
- **Product Catalog**: Browse products with filtering, search, and sorting
- **Shopping Cart**: Persistent cart for both guests and authenticated users
- **User Authentication**: JWT-based auth with "remember me" functionality
- **Product Reviews**: Rating system and customer reviews
- **Secure Checkout**: Stripe integration for payment processing

### Backend
- **RESTful API**: Django REST Framework with comprehensive endpoints
- **PostgreSQL Database**: Robust data management
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Shopping Cart Persistence**: Session-based for guests, user-based for members
- **Order Management**: Complete order lifecycle tracking
- **Email Integration**: Gmail SMTP for notifications
- **Image Management**: Automatic image resizing and optimization

### Security Features
- Environment variable configuration
- XSS and CSRF protection
- Rate limiting ready
- Secure password hashing
- CORS configuration
- Session timeout (10 minutes)

## 🛠️ Tech Stack

### Backend
- Django 4.2.7
- Django REST Framework
- PostgreSQL
- JWT Authentication
- Stripe API
- Pillow (image processing)

### Frontend
- React 19 with TypeScript
- Vite (build tool)
- Redux Toolkit (state management)
- React Router v7
- Tailwind CSS
- Axios
- React Hook Form

### DevOps
- Docker & Docker Compose
- Environment-based configuration

## 📦 Project Structure

```
pasargad-prints/
├── backend/
│   ├── pasargad_prints/     # Main Django project
│   ├── apps/
│   │   ├── users/           # User management
│   │   ├── products/        # Product catalog
│   │   ├── cart/            # Shopping cart
│   │   ├── orders/          # Order management
│   │   └── payments/        # Payment processing
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Route pages
│   │   ├── store/          # Redux store and slices
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd pasargad-prints
```

2. Create environment file for backend:
```bash
cp backend/.env.example backend/.env
```

3. Update the environment variables in `docker-compose.yml`:
- `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY`
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
- `SECRET_KEY` (generate a new one for production)

4. Build and run with Docker Compose:
```bash
docker-compose up --build
```

5. Run database migrations:
```bash
docker-compose exec backend python manage.py migrate
```

6. Create a superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

7. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin

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

### Backend
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `DATABASE_URL` - PostgreSQL connection string
- `STRIPE_PUBLISHABLE_KEY` - Stripe public key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `EMAIL_HOST_USER` - Gmail address for SMTP
- `EMAIL_HOST_PASSWORD` - Gmail app password

### Frontend
- `VITE_API_URL` - Backend API URL
- `VITE_STRIPE_PUBLISHABLE_KEY` - Stripe public key

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

## 🚢 Deployment

### Production Checklist
1. Set `DEBUG=False` in production
2. Generate new `SECRET_KEY`
3. Configure production database
4. Set up SSL certificates
5. Configure production email settings
6. Set up monitoring and logging
7. Configure backup strategy

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💬 Support

For support, email support@pasargadprints.com or create an issue in the repository.