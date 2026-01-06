import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from core.models import TeacherProfile, StaffProfile

def create_users():
    # 0. Create Groups
    teacher_group, _ = Group.objects.get_or_create(name='Teachers')
    staff_group, _ = Group.objects.get_or_create(name='Office Staff')
    print("Groups checked/created.")

    # 1. Create Teacher
    if not User.objects.filter(username='teacher').exists():
        u = User.objects.create_user('teacher', 'teacher@example.com', 'teacher@123')
        TeacherProfile.objects.create(
            user=u,
            assigned_class='9', # Assign Class 9
            assigned_section='A',
            qualification='M.Sc. Physics',
            designation='Senior Teacher'
        )
        u.groups.add(teacher_group)
        print("Created User: teacher / teacher@123 (Class 9-A) & Group Assigned")
    else:
        u = User.objects.get(username='teacher')
        if not hasattr(u, 'teacher_profile'):
             TeacherProfile.objects.create(user=u, assigned_class='9', assigned_section='A')
        u.groups.add(teacher_group)
        print("User 'teacher' updated with group/profile.")

    # 2. Create Staff
    if not User.objects.filter(username='staff').exists():
        u = User.objects.create_user('staff', 'staff@example.com', 'staff@123')
        StaffProfile.objects.create(
            user=u,
            qualification='B.Com',
            designation='Clerk'
        )
        u.groups.add(staff_group)
        print("Created User: staff / staff@123 & Group Assigned")
    else:
        u = User.objects.get(username='staff')
        if not hasattr(u, 'staff_profile'):
             StaffProfile.objects.create(user=u, qualification='B.Com', designation='Clerk')
        u.groups.add(staff_group)
        print("User 'staff' updated with group/profile.")

if __name__ == '__main__':
    create_users()
