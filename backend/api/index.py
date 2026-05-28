import os
import sys

# Add the parent folder of 'api/' (which is 'backend/') to the python system path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_backend.settings')
django.setup()

# Auto-run database migrations and seeding on serverless startup
from django.core.management import call_command
try:
    print("Vercel Startup: Auto-running database migrations...")
    call_command('migrate', noinput=True)
    
    print("Vercel Startup: Auto-running database seeding...")
    from seed_data import seed
    seed()
    print("Vercel Startup: Database setup complete.")
except Exception as e:
    print("Vercel Startup: Database setup skipped or failed (likely already initialized):", e)

from esg_backend.wsgi import application
app = application
