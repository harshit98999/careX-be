from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClientProfile, DoctorProfile

# Define an inline admin descriptor for ClientProfile
class ClientProfileInline(admin.StackedInline):
    """
    Allows editing of the ClientProfile directly within the User admin page.
    """
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Client Profile'
    fk_name = 'user'

# Define an inline admin descriptor for DoctorProfile
class DoctorProfileInline(admin.StackedInline):
    """
    Allows editing of the DoctorProfile directly within the User admin page.
    """
    model = DoctorProfile
    can_delete = False
    verbose_name_plural = 'Doctor Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    """
    Custom Admin configuration for the User model, now including role-based logic.
    """
    # Add 'role' to the list display to easily see user types
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    # Add 'role' to the filters
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        # Add 'role' to the personal info section
        ('Personal info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('OTP Info', {'fields': ('otp', 'otp_created_at')}),
    )

    # Fields for creating a new user (add_fieldsets is for the creation form)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # Add 'role' to the user creation form
            'fields': ('email', 'first_name', 'last_name', 'role', 'password', 'password2'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    # The inlines list is empty by default
    inlines = []

    def get_inlines(self, request, obj=None):
        """
        Dynamically displays the correct profile inline (Client or Doctor)
        based on the user's role. The inline will only appear after the user
        has been created and their role is set.
        """
        if obj: # If the user object exists
            if obj.role == User.Role.CLIENT:
                return [ClientProfileInline]
            elif obj.role == User.Role.DOCTOR:
                return [DoctorProfileInline]
        return super().get_inlines(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Ensures the related profile is saved when the user is saved.
        """
        super().save_model(request, obj, form, change)
        # The post_save signal handles profile creation/saving,
        # so manual intervention is not strictly needed here,
        # but it's good practice for clarity.
        if hasattr(obj, 'clientprofile'):
            obj.clientprofile.save()
        if hasattr(obj, 'doctorprofile'):
            obj.doctorprofile.save()

# Register your User model with your custom admin class
admin.site.register(User, CustomUserAdmin)

# We don't need to register the Profile models separately
# because they are now handled as inlines within the CustomUserAdmin.
# admin.site.register(ClientProfile)
# admin.site.register(DoctorProfile)