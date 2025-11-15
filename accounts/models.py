from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with role-based distinction (Client, Doctor, or Hospital).
    """
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        DOCTOR = "DOCTOR", "Doctor"
        HOSPITAL = "HOSPITAL", "Hospital" # <-- NEW ROLE ADDED

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True) # For Hospital, this can be the contact person's name
    last_name = models.CharField(max_length=150, blank=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Role of the user
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.CLIENT)

    # Fields for OTP
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clientprofile')
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/clients/', blank=True, null=True)
    
    def __str__(self):
        return f'{self.user.email} - Client Profile'


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctorprofile')
    specialization = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/doctors/', blank=True, null=True)

    def __str__(self):
        return f'Dr. {self.user.first_name} {self.user.last_name} - Doctor Profile'


# --- NEW MODEL FOR HOSPITAL PROFILE ---
class HospitalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospitalprofile')
    hospital_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/hospitals/', blank=True, null=True)
    
    def __str__(self):
        return f'{self.hospital_name or self.user.email} - Hospital Profile'


# --- Signals to create a Profile automatically when a User is created ---

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.Role.CLIENT:
            ClientProfile.objects.create(user=instance)
        elif instance.role == User.Role.DOCTOR:
            DoctorProfile.objects.create(user=instance)
        elif instance.role == User.Role.HOSPITAL: # <-- HANDLE HOSPITAL ROLE
            HospitalProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # This signal now needs to handle the possibility that a profile might not exist yet
    # especially during the initial creation. Using hasattr checks for safety.
    if instance.role == User.Role.CLIENT:
        if hasattr(instance, 'clientprofile'):
            instance.clientprofile.save()
    elif instance.role == User.Role.DOCTOR:
        if hasattr(instance, 'doctorprofile'):
            instance.doctorprofile.save()
    elif instance.role == User.Role.HOSPITAL: # <-- HANDLE HOSPITAL ROLE
        if hasattr(instance, 'hospitalprofile'):
            instance.hospitalprofile.save()