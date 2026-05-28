import os
import sys

# Add backend directory to path so Django modules can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from esg_backend.wsgi import application

# Vercel requires a variable named "app" to serve the WSGI application
app = application
