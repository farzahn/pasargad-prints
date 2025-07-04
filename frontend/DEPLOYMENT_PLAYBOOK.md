# Production Deployment Playbook
## Pasargad Prints E-commerce Platform - Frontend

**Version:** 1.0.0  
**Last Updated:** 2025-07-04  
**Environment:** Production  

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Build Process](#build-process)
4. [Deployment Steps](#deployment-steps)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Code Quality & Testing
- [ ] All unit tests passing (`npm run test`)
- [ ] Integration tests completed
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Performance benchmarks met
- [ ] Security scan completed
- [ ] Code review approved
- [ ] Branch merged to `main`

### ✅ Environment Configuration
- [ ] Production environment variables configured
- [ ] SSL certificates valid and renewed
- [ ] CDN configuration verified
- [ ] DNS records updated
- [ ] Analytics tracking configured
- [ ] Error monitoring setup

### ✅ Dependencies & Assets
- [ ] All dependencies updated to stable versions
- [ ] Image assets optimized
- [ ] Fonts preloaded
- [ ] Third-party services verified
- [ ] API endpoints accessible

---

## Environment Setup

### Required Environment Variables

```bash
# Production Environment Variables (.env.production)
VITE_APP_TITLE=Pasargad Prints
VITE_APP_VERSION=1.0.0
VITE_NODE_ENV=production

# API Configuration
VITE_API_BASE_URL=https://api.pasargadprints.com
VITE_API_TIMEOUT=30000

# CDN Configuration
VITE_CDN_URL=https://cdn.pasargadprints.com
VITE_STATIC_URL=https://static.pasargadprints.com

# Analytics & Tracking
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
VITE_GOOGLE_TAG_MANAGER_ID=GTM-XXXXXXX
VITE_ENABLE_ANALYTICS=true

# Security & Performance
VITE_ENABLE_CSP=true
VITE_ENABLE_SECURITY_HEADERS=true
VITE_ENABLE_COMPRESSION=true

# SEO Configuration
VITE_SITE_URL=https://pasargadprints.com
VITE_ENABLE_SITEMAP=true
VITE_ENABLE_ROBOTS_TXT=true
```

### Infrastructure Requirements

```yaml
# Server Specifications
CPU: 2+ cores
RAM: 4GB minimum, 8GB recommended
Storage: 20GB SSD minimum
Network: 1Gbps connection

# CDN Requirements
- Global edge locations
- Image optimization support
- Gzip/Brotli compression
- SSL/TLS encryption
```

---

## Build Process

### 1. Install Dependencies

```bash
# Install production dependencies
npm ci --production

# Verify dependencies
npm audit --audit-level high
```

### 2. Production Build

```bash
# Build for production
npm run build:prod

# Verify build
npm run preview
```

### 3. Build Optimization

```bash
# Analyze bundle size
npm run analyze

# Check performance
npm run test:performance

# Validate accessibility
npm run test:accessibility
```

### Build Output Structure

```
dist/
├── index.html                 # Main HTML file
├── assets/
│   ├── css/
│   │   └── main-[hash].css   # Minified CSS
│   ├── js/
│   │   ├── main-[hash].js    # Main application bundle
│   │   ├── vendor-[hash].js  # Third-party libraries
│   │   └── worker-[hash].js  # Service worker
│   ├── images/
│   │   └── [optimized-images] # Compressed images
│   └── fonts/
│       └── [font-files]      # Web fonts
├── sitemap.xml               # SEO sitemap
├── robots.txt               # Robot instructions
├── manifest.json            # PWA manifest
└── sw.js                   # Service worker
```

---

## Deployment Steps

### Method 1: Static Hosting (Recommended)

#### Using Nginx

1. **Upload Build Files**
```bash
# Copy build files to server
scp -r dist/* user@server:/var/www/pasargadprints/
```

2. **Nginx Configuration**
```nginx
# /etc/nginx/sites-available/pasargadprints.com
server {
    listen 443 ssl http2;
    server_name pasargadprints.com www.pasargadprints.com;
    
    root /var/www/pasargadprints;
    index index.html;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Cache Headers
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # HTML files
    location ~* \.html$ {
        expires 5m;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass https://api.pasargadprints.com/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name pasargadprints.com www.pasargadprints.com;
    return 301 https://$server_name$request_uri;
}
```

3. **Enable Configuration**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/pasargadprints.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### Using CDN (CloudFront)

1. **Upload to S3**
```bash
# Sync build files to S3
aws s3 sync dist/ s3://pasargadprints-frontend/ --delete

# Set cache headers
aws s3 cp s3://pasargadprints-frontend/ s3://pasargadprints-frontend/ \
  --recursive --metadata-directive REPLACE \
  --cache-control "max-age=31536000" \
  --exclude "*.html"

aws s3 cp s3://pasargadprints-frontend/ s3://pasargadprints-frontend/ \
  --recursive --metadata-directive REPLACE \
  --cache-control "max-age=300" \
  --include "*.html"
```

2. **CloudFront Configuration**
```json
{
  "origins": [
    {
      "domainName": "pasargadprints-frontend.s3.amazonaws.com",
      "id": "S3-pasargadprints-frontend",
      "s3OriginConfig": {
        "originAccessIdentity": "origin-access-identity/cloudfront/XXXXX"
      }
    }
  ],
  "defaultCacheBehavior": {
    "targetOriginId": "S3-pasargadprints-frontend",
    "viewerProtocolPolicy": "redirect-to-https",
    "compress": true,
    "cachePolicyId": "managed-caching-optimized"
  },
  "cacheBehaviors": [
    {
      "pathPattern": "*.html",
      "cachePolicyId": "managed-caching-disabled"
    },
    {
      "pathPattern": "/api/*",
      "cachePolicyId": "managed-caching-disabled"
    }
  ]
}
```

### Method 2: Docker Deployment

```dockerfile
# Production Dockerfile
FROM nginx:alpine

# Copy build files
COPY dist/ /usr/share/nginx/html/

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

```bash
# Build and deploy
docker build -t pasargadprints-frontend .
docker run -d -p 80:80 --name pasargadprints-frontend pasargadprints-frontend
```

---

## Post-Deployment Verification

### 1. Functional Testing

```bash
# Health check
curl -I https://pasargadprints.com
# Expected: 200 OK

# Main pages accessibility
curl -f https://pasargadprints.com/
curl -f https://pasargadprints.com/products
curl -f https://pasargadprints.com/cart
```

### 2. Performance Testing

```bash
# Lighthouse audit
npx lighthouse https://pasargadprints.com --chrome-flags="--headless"

# Expected scores:
# Performance: >90
# Accessibility: 100
# Best Practices: >90
# SEO: >90
```

### 3. Security Verification

```bash
# SSL test
openssl s_client -connect pasargadprints.com:443 -servername pasargadprints.com

# Security headers check
curl -I https://pasargadprints.com | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)"
```

### 4. SEO Verification

```bash
# Sitemap accessibility
curl -f https://pasargadprints.com/sitemap.xml

# Robots.txt
curl -f https://pasargadprints.com/robots.txt

# Meta tags verification
curl -s https://pasargadprints.com | grep -E "(title|meta.*description|meta.*keywords)"
```

### 5. Analytics Verification

- [ ] Google Analytics tracking active
- [ ] Google Tag Manager firing
- [ ] Error tracking functional
- [ ] Performance monitoring active

---

## Rollback Procedures

### Quick Rollback (Nginx)

```bash
# Backup current deployment
cp -r /var/www/pasargadprints /var/www/pasargadprints.backup.$(date +%Y%m%d_%H%M%S)

# Restore previous version
cp -r /var/www/pasargadprints.previous/* /var/www/pasargadprints/

# Reload Nginx
sudo systemctl reload nginx
```

### CloudFront Rollback

```bash
# Restore previous S3 version
aws s3 sync s3://pasargadprints-frontend-backup/ s3://pasargadprints-frontend/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id XXXXX --paths "/*"
```

### Docker Rollback

```bash
# Stop current container
docker stop pasargadprints-frontend

# Start previous version
docker run -d -p 80:80 --name pasargadprints-frontend pasargadprints-frontend:previous
```

---

## Monitoring & Maintenance

### Performance Monitoring

```bash
# Weekly performance checks
npm run test:performance

# Monitor Core Web Vitals
# - Largest Contentful Paint (LCP): <2.5s
# - First Input Delay (FID): <100ms
# - Cumulative Layout Shift (CLS): <0.1
```

### Security Monitoring

```bash
# Monthly security audits
npm audit
nmap -sS -O pasargadprints.com

# SSL certificate monitoring
openssl x509 -in /path/to/cert.pem -noout -dates
```

### Content Updates

```bash
# Update sitemap (monthly)
node scripts/generate-sitemap.js

# Update dependencies (quarterly)
npm update
npm audit fix
```

### Backup Procedures

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "/backups/pasargadprints-frontend-$DATE.tar.gz" /var/www/pasargadprints/
aws s3 cp "/backups/pasargadprints-frontend-$DATE.tar.gz" s3://pasargadprints-backups/
```

---

## Troubleshooting

### Common Issues

#### 1. Build Failures

**Problem:** Build process fails  
**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### 2. 404 Errors for Routes

**Problem:** SPA routes return 404  
**Solution:** Ensure nginx configuration includes:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

#### 3. Asset Loading Issues

**Problem:** CSS/JS files not loading  
**Solution:** Check file paths and cache headers
```bash
# Verify asset paths
ls -la /var/www/pasargadprints/assets/

# Clear browser cache
curl -H "Cache-Control: no-cache" https://pasargadprints.com
```

#### 4. Performance Issues

**Problem:** Slow page load times  
**Solution:**
```bash
# Check bundle sizes
npm run analyze

# Optimize images
npm run optimize:images

# Enable compression
# Verify gzip is enabled in nginx.conf
```

#### 5. Analytics Not Working

**Problem:** Analytics data not appearing  
**Solution:**
```javascript
// Check environment variables
console.log('GA ID:', import.meta.env.VITE_GOOGLE_ANALYTICS_ID);

// Verify initialization
if (typeof gtag !== 'undefined') {
  console.log('Analytics loaded successfully');
}
```

### Emergency Contacts

- **DevOps Team:** devops@pasargadprints.com
- **Security Team:** security@pasargadprints.com
- **On-call Engineer:** +1-xxx-xxx-xxxx

### Log Locations

```bash
# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Application logs
tail -f /var/log/pasargadprints/app.log

# System logs
journalctl -u nginx -f
```

---

## Deployment Automation

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: |
          npm run test
          npm run test:accessibility
      
      - name: Build for production
        run: npm run build:prod
        env:
          VITE_NODE_ENV: production
      
      - name: Deploy to S3
        run: aws s3 sync dist/ s3://pasargadprints-frontend/ --delete
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Invalidate CloudFront
        run: aws cloudfront create-invalidation --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} --paths "/*"
```

---

## Success Criteria

✅ **Deployment is considered successful when:**

1. All health checks pass
2. Performance scores meet targets (>90)
3. Accessibility audit passes (100/100)
4. Security headers present
5. Analytics tracking functional
6. Error rates <0.1%
7. Page load times <3 seconds
8. Core Web Vitals in green

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-07-04 | Initial production deployment |

---

**Next Review Date:** 2025-08-04  
**Document Owner:** Frontend Engineering Team