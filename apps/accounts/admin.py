from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Profile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display   = ['email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter    = ['role', 'is_active']
    search_fields  = ['email', 'first_name', 'last_name']
    ordering       = ['-date_joined']
    fieldsets      = UserAdmin.fieldsets + (
        ('Aavarana', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets  = UserAdmin.add_fieldsets + (
        ('Aavarana', {'fields': ('email', 'role', 'phone_number')}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'created_at']
    raw_id_fields = ['user']
