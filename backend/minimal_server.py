#!/usr/bin/env python3
"""
Minimal Django server for testing API functionality
"""
import os
import sys
from django.core.wsgi import get_wsgi_application
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')

class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """Multi-threaded WSGI server"""
    pass

def run_server():
    """Run the Django application"""
    print("🚀 Starting Minimal Django Server")
    print("=" * 50)
    
    try:
        # Get Django WSGI application
        application = get_wsgi_application()
        print("✅ Django WSGI application loaded")
        
        # Create server
        server = make_server('127.0.0.1', 8000, application, ThreadedWSGIServer)
        print("✅ Server created on http://127.0.0.1:8000")
        
        print("\n📋 Available endpoints:")
        print("   • http://127.0.0.1:8000/api/")
        print("   • http://127.0.0.1:8000/api/users/auth/login/")
        print("   • http://127.0.0.1:8000/admin/")
        
        print(f"\n🎯 Ready to test frontend connection!")
        print("Press Ctrl+C to stop the server")
        
        # Start serving
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_server()