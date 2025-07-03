import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("🔧 Fixing admin users for email-based authentication...\n")

# Delete existing users if they exist
for username in ['admin', 'staff']:
    try:
        user = User.objects.get(username=username)
        user.delete()
        print(f"Removed old user: {username}")
    except User.DoesNotExist:
        pass

# Create superuser with email
try:
    admin_user = User.objects.create_superuser(
        email='admin@pasargadprints.com',
        username='admin',  # Still needed as REQUIRED_FIELD
        password='Admin123!',
        first_name='Admin',
        last_name='User'
    )
    print("\n✅ Superuser created successfully!")
    print("Email: admin@pasargadprints.com")
    print("Password: Admin123!")
except Exception as e:
    print(f"Error creating superuser: {e}")
    # Try to get existing user
    try:
        admin_user = User.objects.get(email='admin@pasargadprints.com')
        admin_user.set_password('Admin123!')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        print("\n✅ Updated existing superuser password!")
        print("Email: admin@pasargadprints.com")
        print("Password: Admin123!")
    except:
        pass

# Create staff user with email
try:
    staff_user = User.objects.create_user(
        email='staff@pasargadprints.com',
        username='staff',  # Still needed as REQUIRED_FIELD
        password='Staff123!',
        first_name='Staff',
        last_name='Member'
    )
    staff_user.is_staff = True
    staff_user.save()
    print("\n✅ Staff user created successfully!")
    print("Email: staff@pasargadprints.com")
    print("Password: Staff123!")
except Exception as e:
    print(f"Error creating staff user: {e}")
    # Try to get existing user
    try:
        staff_user = User.objects.get(email='staff@pasargadprints.com')
        staff_user.set_password('Staff123!')
        staff_user.is_staff = True
        staff_user.save()
        print("\n✅ Updated existing staff user password!")
        print("Email: staff@pasargadprints.com")
        print("Password: Staff123!")
    except:
        pass

print("\n📝 Login to admin with EMAIL (not username):")
print("https://0709-24-17-91-122.ngrok-free.app/admin/")
print("\n⚠️ IMPORTANT: Use the email addresses above to login, NOT the usernames!")