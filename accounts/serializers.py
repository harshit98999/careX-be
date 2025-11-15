from rest_framework import serializers
# CORRECT: Import models from the .models file
from .models import User, ClientProfile, DoctorProfile, HospitalProfile
from .utils import generate_otp, send_otp_email
from django.utils import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes the JWT token claims to include user's email, first name, and role.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['role'] = user.role
        return token


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')
    role = serializers.ChoiceField(choices=User.Role.choices)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password2', 'role')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role']
        )
        user.set_password(validated_data['password'])
        
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        # The post_save signal handles profile creation.
        # We can pre-populate the hospital name from the first_name field if desired.
        if user.role == User.Role.HOSPITAL:
            # Check if the profile was created by the signal
            if hasattr(user, 'hospitalprofile'):
                user.hospitalprofile.hospital_name = validated_data.get('first_name', '')
                user.hospitalprofile.save()

        send_otp_email(user.email, otp, purpose="account verification")
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ClientProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Client profile.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = ClientProfile
        fields = (
            'email', 
            'first_name', 
            'last_name', 
            'role',
            'bio', 
            'date_of_birth', 
            'phone_number', 
            'profile_picture'
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()

        return super().update(instance, validated_data)


class DoctorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Doctor profile.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = (
            'email', 
            'first_name', 
            'last_name', 
            'role',
            'specialization', 
            'license_number', 
            'years_of_experience',
            'phone_number', 
            'profile_picture'
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()

        return super().update(instance, validated_data)


class HospitalProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Hospital profile.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    contact_person_first_name = serializers.CharField(source='user.first_name')
    contact_person_last_name = serializers.CharField(source='user.last_name')
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = HospitalProfile
        fields = (
            'email', 
            'contact_person_first_name',
            'contact_person_last_name',
            'role',
            'hospital_name', 
            'address', 
            'phone_number',
            'profile_picture'
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Update the contact person's name on the User model
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()
        
        # Update HospitalProfile fields using super() for simplicity
        return super().update(instance, validated_data)