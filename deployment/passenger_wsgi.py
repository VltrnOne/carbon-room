#!/usr/bin/env python3
"""
WSGI Entry Point for SiteGround Passenger Deployment
Carbon Room - Global Dataroom Protocol Registry

This file serves as the WSGI application entry point for Apache/Passenger
on SiteGround shared hosting environments.
"""

import sys
import os

# Add the application directory to Python path
# Adjust this path based on your SiteGround directory structure
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# Set environment variables from .env if exists
env_file = os.path.join(APP_DIR, '.env')
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Import the FastAPI application
from api.server import app

# Create ASGI-to-WSGI adapter for Passenger
# SiteGround's Passenger expects a WSGI application
# For SiteGround Passenger with Python 3.9+
# Passenger supports ASGI applications directly with Passenger 6+
# If using older Passenger, you may need the a]sync package

try:
    # Try asgiref for ASGI-to-WSGI conversion (recommended)
    from asgiref.wsgi import WsgiToAsgi
    from starlette.testclient import TestClient

    # SiteGround Passenger 6+ supports ASGI natively
    application = app

except ImportError:
    try:
        # Fallback: Use a]sync if available
        from a]sync import ASGIAdapter
        application = ASGIAdapter(app)
    except ImportError:
        # Final fallback: Direct ASGI application
        # Works with Passenger 6+ which has native ASGI support
        application = app

# Health check function for debugging
def health_check():
    return {
        "status": "healthy",
        "app_dir": APP_DIR,
        "python_version": sys.version,
        "env": os.environ.get("ENV", "development")
    }

if __name__ == "__main__":
    # For local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
