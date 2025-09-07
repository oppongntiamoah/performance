from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, Department, Staff, Role


class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ("email", "is_active", "is_staff", "is_admin")
    list_filter = ("is_active", "is_staff", "is_admin")
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_admin", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "staff_id",
        "department",
        "is_hod",
        "is_pc",
        "is_vp",
        "is_active",
    )
    list_filter = ("department", "is_hod", "is_pc", "is_vp", "is_active")
    search_fields = ("fname", "lname", "staff_id", "user__email")
    ordering = ("fname", "lname")
    autocomplete_fields = ("user", "department")


# Register CustomUser separately
admin.site.register(CustomUser, CustomUserAdmin)
