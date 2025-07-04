import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if superuser already exists
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@pasargadprints.com',
        password='Admin123!',
        first_name='Admin',
        last_name='User'
    )
    print("✅ Superuser created successfully!")
    print("Username: admin")
    print("Password: Admin123!")
else:
    print("ℹ️ Superuser 'admin' already exists")
    
# Create a staff user as well
if not User.objects.filter(username='staff').exists():
    staff_user = User.objects.create_user(
        username='staff',
        email='staff@pasargadprints.com',
        password='Staff123!',
        first_name='Staff',
        last_name='Member'
    )
    staff_user.is_staff = True
    staff_user.save()
    print("\n✅ Staff user created successfully!")
    print("Username: staff")
    print("Password: Staff123!")
else:
    print("\nℹ️ Staff user 'staff' already exists")

print("\n📝 Access the admin panel at:")
print("https://0709-24-17-91-122.ngrok-free.app/admin/")
print("\nFeatures available in admin:")
print("• View and edit all products")
print("• Update stock quantities directly from the list view")
print("• Activate/deactivate products")
print("• Add product images (via URL or upload)")
print("• Manage categories and reviews")