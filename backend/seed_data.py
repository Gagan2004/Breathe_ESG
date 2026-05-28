import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from ingestion.models import Organization
from rest_framework.authtoken.models import Token

User = get_user_model()

def seed():
    print("Seeding database...")
    
    # 1. Create Organization
    org, created = Organization.objects.get_or_create(name="Acme Corporation")
    if created:
        print(f"Created organization: {org.name}")
    else:
        print(f"Organization already exists: {org.name}")
        
    # 2. Create Analyst User
    analyst, created = User.objects.get_or_create(
        username="analyst",
        email="analyst@acme.com",
        defaults={
            "organization": org,
            "is_staff": True,
            "is_superuser": False
        }
    )
    if created:
        analyst.set_password("analyst123")
        analyst.save()
        print(f"Created analyst user. Password: analyst123")
    else:
        print("Analyst user already exists.")
        
    token_analyst, _ = Token.objects.get_or_create(user=analyst)
    print(f"Analyst Token: {token_analyst.key}")

    # 3. Create Manager User
    manager, created = User.objects.get_or_create(
        username="manager",
        email="manager@acme.com",
        defaults={
            "organization": org,
            "is_staff": True,
            "is_superuser": False
        }
    )
    if created:
        manager.set_password("manager123")
        manager.save()
        print(f"Created manager user. Password: manager123")
    else:
        print("Manager user already exists.")
        
    token_manager, _ = Token.objects.get_or_create(user=manager)
    print(f"Manager Token: {token_manager.key}")

    # 4. Create Admin User
    admin, created = User.objects.get_or_create(
        username="admin",
        email="admin@acme.com",
        defaults={
            "organization": org,
            "is_staff": True,
            "is_superuser": True
        }
    )
    if created:
        admin.set_password("admin123")
        admin.save()
        print(f"Created admin user. Password: admin123")
    else:
        print("Admin user already exists.")
        
    token_admin, _ = Token.objects.get_or_create(user=admin)
    print(f"Admin Token: {token_admin.key}")

    print("Seeding completed successfully.")

if __name__ == "__main__":
    seed()
