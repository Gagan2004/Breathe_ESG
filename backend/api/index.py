import os
import sys

# Add the parent folder of 'api/' (which is 'backend/') to the python system path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esg_backend.wsgi import application

# Vercel serverless expects a handler named "app"
app = application
