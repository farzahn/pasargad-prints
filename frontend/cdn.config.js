// CDN Configuration for different environments
export const cdnConfig = {
  production: {
    baseUrl: 'https://cdn.pasargadprints.com',
    staticUrl: 'https://static.pasargadprints.com',
    optimization: {
      enabled: true,
      formats: ['webp', 'avif', 'jpeg', 'png'],
      defaultFormat: 'webp',
      quality: 80,
      responsive: true,
      sizes: [320, 640, 768, 1024, 1280, 1536, 1920]
    },
    caching: {
      images: {
        maxAge: 31536000, // 1 year
        sMaxAge: 31536000,
        staleWhileRevalidate: 86400 // 1 day
      },
      fonts: {
        maxAge: 31536000, // 1 year
        sMaxAge: 31536000,
        immutable: true
      },
      css: {
        maxAge: 31536000, // 1 year
        sMaxAge: 31536000,
        immutable: true
      },
      js: {
        maxAge: 31536000, // 1 year
        sMaxAge: 31536000,
        immutable: true
      }
    }
  },
  staging: {
    baseUrl: 'https://staging-cdn.pasargadprints.com',
    staticUrl: 'https://staging-static.pasargadprints.com',
    optimization: {
      enabled: true,
      formats: ['webp', 'jpeg', 'png'],
      defaultFormat: 'webp',
      quality: 75,
      responsive: true,
      sizes: [320, 640, 768, 1024, 1280, 1536]
    },
    caching: {
      images: {
        maxAge: 86400, // 1 day
        sMaxAge: 86400,
        staleWhileRevalidate: 3600 // 1 hour
      },
      fonts: {
        maxAge: 86400, // 1 day
        sMaxAge: 86400,
        immutable: false
      },
      css: {
        maxAge: 86400, // 1 day
        sMaxAge: 86400,
        immutable: false
      },
      js: {
        maxAge: 86400, // 1 day
        sMaxAge: 86400,
        immutable: false
      }
    }
  },
  development: {
    baseUrl: 'http://localhost:8000',
    staticUrl: 'http://localhost:8000',
    optimization: {
      enabled: false,
      formats: ['jpeg', 'png'],
      defaultFormat: 'jpeg',
      quality: 90,
      responsive: false,
      sizes: [1024]
    },
    caching: {
      images: {
        maxAge: 0,
        sMaxAge: 0,
        staleWhileRevalidate: 0
      },
      fonts: {
        maxAge: 0,
        sMaxAge: 0,
        immutable: false
      },
      css: {
        maxAge: 0,
        sMaxAge: 0,
        immutable: false
      },
      js: {
        maxAge: 0,
        sMaxAge: 0,
        immutable: false
      }
    }
  }
};

// Nginx CDN Configuration Template
export const nginxConfig = `
# CDN Configuration for Pasargad Prints

# Image optimization and caching
location ~* \.(jpg|jpeg|png|gif|ico|svg|webp|avif)$ {
    expires 1y;
    add_header Cache-Control "public, immutable, stale-while-revalidate=86400";
    add_header Vary Accept;
    
    # WebP support
    location ~* \.(jpg|jpeg|png)$ {
        add_header Vary Accept;
        if ($http_accept ~* "webp") {
            rewrite ^(.*)$ $1.webp last;
        }
    }
    
    # AVIF support
    location ~* \.(jpg|jpeg|png)$ {
        add_header Vary Accept;
        if ($http_accept ~* "avif") {
            rewrite ^(.*)$ $1.avif last;
        }
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types image/svg+xml;
}

# Font caching
location ~* \.(woff|woff2|eot|ttf|otf)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Access-Control-Allow-Origin *;
    
    # Preload hints
    add_header Link "</fonts/$1>; rel=preload; as=font; type=font/$1; crossorigin=anonymous";
}

# CSS and JS caching
location ~* \.(css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/css application/javascript;
}

# HTML caching
location ~* \.html$ {
    expires 5m;
    add_header Cache-Control "public, must-revalidate";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/html;
}

# API responses - no caching
location /api/ {
    expires -1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
}

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.google-analytics.com https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; media-src 'self' https:; object-src 'none'; frame-ancestors 'self';" always;
`;

// CloudFront CDN Configuration
export const cloudFrontConfig = {
  origins: [
    {
      domainName: 'pasargadprints.com',
      originPath: '',
      customOriginConfig: {
        httpPort: 80,
        httpsPort: 443,
        originProtocolPolicy: 'https-only'
      }
    }
  ],
  defaultCacheBehavior: {
    targetOriginId: 'pasargadprints-origin',
    viewerProtocolPolicy: 'redirect-to-https',
    compress: true,
    cachePolicyId: 'managed-caching-optimized',
    originRequestPolicyId: 'managed-cors-s3-origin'
  },
  cacheBehaviors: [
    {
      pathPattern: '/api/*',
      targetOriginId: 'pasargadprints-origin',
      viewerProtocolPolicy: 'redirect-to-https',
      cachePolicyId: 'managed-caching-disabled',
      originRequestPolicyId: 'managed-cors-preflight'
    },
    {
      pathPattern: '*.jpg',
      targetOriginId: 'pasargadprints-origin',
      viewerProtocolPolicy: 'redirect-to-https',
      compress: true,
      cachePolicyId: 'managed-caching-optimized-for-uncompressed-objects'
    },
    {
      pathPattern: '*.png',
      targetOriginId: 'pasargadprints-origin',
      viewerProtocolPolicy: 'redirect-to-https',
      compress: true,
      cachePolicyId: 'managed-caching-optimized-for-uncompressed-objects'
    },
    {
      pathPattern: '*.css',
      targetOriginId: 'pasargadprints-origin',
      viewerProtocolPolicy: 'redirect-to-https',
      compress: true,
      cachePolicyId: 'managed-caching-optimized'
    },
    {
      pathPattern: '*.js',
      targetOriginId: 'pasargadprints-origin',
      viewerProtocolPolicy: 'redirect-to-https',
      compress: true,
      cachePolicyId: 'managed-caching-optimized'
    }
  ]
};