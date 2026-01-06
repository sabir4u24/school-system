import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.contrib.auth.models import User

def check_user(username):
    pass

if __name__ == '__main__':
    print("Listing all users:")
    for u in User.objects.all():
        print(f"- {u.username} (Superuser: {u.is_superuser})")
        print(f"  Groups: {[g.name for g in u.groups.all()]}")
