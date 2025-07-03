#!/bin/bash

echo "Starting Pasargad Prints with Ngrok..."

# Check if using nginx setup
if [ "$1" == "nginx" ]; then
    echo "Using nginx configuration..."
    docker compose -f docker-compose.ngrok.yml up -d
    echo "Waiting for services to start..."
    sleep 10
    echo "Starting ngrok on port 80..."
    ngrok http 80
else
    echo "Using direct port configuration..."
    docker compose up -d
    echo "Waiting for services to start..."
    sleep 10
    echo "Starting ngrok on port 3000..."
    ngrok http 3000
fi