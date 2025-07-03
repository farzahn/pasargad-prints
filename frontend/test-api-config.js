#!/usr/bin/env node

// Test script to verify API configuration
// Run with: node test-api-config.js

const axios = require('axios');

// Read environment variables
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

console.log('Testing API Configuration...');
console.log('=========================');
console.log(`VITE_API_URL: ${API_URL}`);
console.log('');

// Test endpoints
const endpoints = [
  '/api/users/auth/login/',
  '/api/products/',
  '/api/cart/',
];

async function testEndpoint(endpoint) {
  const fullUrl = `${API_URL}${endpoint}`;
  console.log(`Testing: ${fullUrl}`);
  
  try {
    const response = await axios.get(fullUrl, {
      validateStatus: () => true // Accept any status code
    });
    
    if (response.status === 404 && response.config.url.includes('/api/api/')) {
      console.log(`❌ DOUBLE /api DETECTED! Check your VITE_API_URL configuration.`);
    } else if (response.status === 401 || response.status === 403) {
      console.log(`✅ Endpoint reachable (auth required)`);
    } else if (response.status === 405) {
      console.log(`✅ Endpoint reachable (method not allowed for GET)`);
    } else if (response.status >= 200 && response.status < 300) {
      console.log(`✅ Endpoint reachable and accessible`);
    } else {
      console.log(`⚠️  Status: ${response.status}`);
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
  console.log('');
}

async function runTests() {
  for (const endpoint of endpoints) {
    await testEndpoint(endpoint);
  }
  
  console.log('Configuration Recommendations:');
  console.log('============================');
  console.log('✅ VITE_API_URL should be the base backend URL without /api');
  console.log('✅ Example: http://localhost:8000');
  console.log('❌ NOT: http://localhost:8000/api or /api');
}

runTests();