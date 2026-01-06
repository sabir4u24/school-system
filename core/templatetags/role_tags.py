from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.filter
def is_teacher(user):
    return hasattr(user, 'teacher_profile') or user.groups.filter(name='Teachers').exists()

@register.filter
def is_staff(user):
    return hasattr(user, 'staff_profile') or user.groups.filter(name='Office Staff').exists()

@register.filter
def get_teacher_class(user):
    if hasattr(user, 'teacher_profile'):
        t = user.teacher_profile
        return f"{t.assigned_class}-{t.assigned_section}"
    return ""
