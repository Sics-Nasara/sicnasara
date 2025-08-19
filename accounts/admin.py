# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from scuelo.admin import sics_site  # import the custom admin site
# Unregister first so we can re-register with Jazzmin customization (optional)
admin.site.unregister(User )
admin.site.unregister(Group )

# Register again with default Django UserAdmin & GroupAdmin
@admin.register(User , site=sics_site)
class CustomUserAdmin(UserAdmin):
    """Admin panel for Django's built-in User model."""
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_superuser", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)


@admin.register(Group , site=sics_site) 
class CustomGroupAdmin(GroupAdmin):
    """Admin panel for Django's built-in Group model."""
    search_fields = ("name",)
    ordering = ("name",)
