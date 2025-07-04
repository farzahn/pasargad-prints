FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Copy .env file from root directory for environment variables
COPY ../.env .env

# Expose port
EXPOSE 3000

# Start development server with host binding for external access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]