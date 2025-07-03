#!/usr/bin/env node

// Simple test to verify the login endpoint is reachable through ngrok
// This tests both direct backend access and frontend proxy

const http = require('http');
const https = require('https');

// Test configuration
const tests = [
  {
    name: 'Direct Backend API (localhost:8000)',
    url: 'http://localhost:8000/api/auth/login/',
    method: 'OPTIONS' // Test CORS preflight
  },
  {
    name: 'Frontend Proxy (localhost:3000)',
    url: 'http://localhost:3000/api/auth/login/',
    method: 'OPTIONS' // Test CORS preflight
  }
];

// Function to make HTTP request
function testEndpoint(test) {
  return new Promise((resolve, reject) => {
    const url = new URL(test.url);
    const protocol = url.protocol === 'https:' ? https : http;
    
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: test.method,
      headers: {
        'Origin': 'https://example.ngrok.io', // Simulate ngrok origin
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'
      }
    };

    console.log(`\nTesting: ${test.name}`);
    console.log(`URL: ${test.url}`);
    console.log(`Method: ${test.method}`);

    const req = protocol.request(options, (res) => {
      console.log(`Status: ${res.statusCode}`);
      console.log('Headers:', JSON.stringify(res.headers, null, 2));
      
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200 || res.statusCode === 204) {
          console.log('✓ Endpoint is reachable');
          console.log('CORS Headers:');
          console.log(`  Access-Control-Allow-Origin: ${res.headers['access-control-allow-origin'] || 'Not set'}`);
          console.log(`  Access-Control-Allow-Credentials: ${res.headers['access-control-allow-credentials'] || 'Not set'}`);
          console.log(`  Access-Control-Allow-Methods: ${res.headers['access-control-allow-methods'] || 'Not set'}`);
          resolve(true);
        } else {
          console.log('✗ Unexpected status code');
          if (data) console.log('Response:', data);
          resolve(false);
        }
      });
    });

    req.on('error', (err) => {
      console.log('✗ Connection error:', err.message);
      resolve(false);
    });

    req.end();
  });
}

// Run all tests
async function runTests() {
  console.log('Login Endpoint Connectivity Test');
  console.log('================================');
  
  let allPassed = true;
  
  for (const test of tests) {
    const passed = await testEndpoint(test);
    if (!passed) allPassed = false;
  }
  
  console.log('\n================================');
  console.log(allPassed ? '✓ All tests passed!' : '✗ Some tests failed');
  
  // Test actual login request (optional)
  console.log('\n\nTesting actual login request...');
  const loginTest = {
    name: 'Login POST Request',
    url: 'http://localhost:3000/api/auth/login/',
    method: 'POST',
    body: JSON.stringify({
      username: 'testuser',
      password: 'testpass'
    })
  };
  
  const loginReq = http.request({
    hostname: 'localhost',
    port: 3000,
    path: '/api/auth/login/',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': loginTest.body.length
    }
  }, (res) => {
    console.log(`Login test status: ${res.statusCode}`);
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      if (res.statusCode === 400 || res.statusCode === 401) {
        console.log('✓ Login endpoint is responding (authentication failed as expected)');
      } else if (res.statusCode === 200) {
        console.log('✓ Login endpoint is working!');
      } else {
        console.log('Response:', data);
      }
    });
  });
  
  loginReq.on('error', (err) => {
    console.log('✗ Login request error:', err.message);
  });
  
  loginReq.write(loginTest.body);
  loginReq.end();
}

// Run the tests
runTests();