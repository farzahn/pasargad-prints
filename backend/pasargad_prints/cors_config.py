"""
CORS configuration for dynamic environments like ngrok
"""
from corsheaders.defaults import default_headers

# Allow ngrok headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'ngrok-skip-browser-warning',
]

# Function to check if origin should be allowed
def cors_allowed_origin_checker(origin, request):
    # Allow all ngrok domains
    if origin and ('.ngrok-free.app' in origin or '.ngrok.io' in origin):
        return True
    
    # Allow localhost for development
    if origin and ('localhost' in origin or '127.0.0.1' in origin):
        return True
    
    return False