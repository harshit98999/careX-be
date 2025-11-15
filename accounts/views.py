from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
# models import is not needed here if using get_user_model
from .serializers import (
    UserRegisterSerializer,
    MyTokenObtainPairSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginSerializer,
    ClientProfileSerializer,
    DoctorProfileSerializer,
    HospitalProfileSerializer, # <-- Import HospitalProfileSerializer
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .utils import generate_otp, send_otp_email

User = get_user_model()


# --- REGISTRATION FLOW VIEWS ---
# No changes needed for RegisterView, VerifyOTPView, or ResendOTPView.
# They are generic and work based on the User model.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "User registered successfully. Please check your email for an OTP to activate your account."},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class VerifyOTPView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_active:
            return Response({"message": "Account is already activated."}, status=status.HTTP_400_BAD_REQUEST)
        if user.otp != otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        otp_expiry_time = user.otp_created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        if timezone.now() > otp_expiry_time:
            return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.otp = None
        user.otp_created_at = None
        user.save()
        return Response({"message": "Account activated successfully. You can now log in."}, status=status.HTTP_200_OK)

class ResendOTPView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_active:
            return Response({"message": "Account is already activated."}, status=status.HTTP_400_BAD_REQUEST)
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        if send_otp_email(user.email, otp, purpose="account verification"):
            return Response({"message": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- LOGIN FLOW VIEWS ---
# No changes needed for LoginView, ResendLoginOTPView, or LoginVerifyOTPView.
# They are generic and work based on the User model.

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"error": "Account not activated. Please verify your email first."}, status=status.HTTP_403_FORBIDDEN)
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        send_otp_email(user.email, otp, purpose="login")
        return Response({"message": "OTP has been sent to your email for login verification."}, status=status.HTTP_200_OK)

class ResendLoginOTPView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user.is_active:
            return Response({"error": "Account not activated. Cannot log in."}, status=status.HTTP_403_FORBIDDEN)
        if not user.otp_created_at:
             return Response({"error": "No active login attempt found. Please initiate login first."}, status=status.HTTP_400_BAD_REQUEST)
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        if send_otp_email(user.email, otp, purpose="login"):
            return Response({"message": "A new login OTP has been sent to your email."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginVerifyOTPView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.otp != otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        otp_expiry_time = user.otp_created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        if timezone.now() > otp_expiry_time:
            return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.otp = None
        user.otp_created_at = None
        user.save()
        
        token = MyTokenObtainPairSerializer.get_token(user)
        
        return Response({
            'refresh': str(token),
            'access': str(token.access_token),
            'role': user.role,
        }, status=status.HTTP_200_OK)


# --- User Profile View (UPDATED) ---
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the profile of the currently authenticated user.
    Dynamically selects the serializer and queryset based on the user's role.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the user's role.
        """
        user_role = self.request.user.role
        if user_role == User.Role.DOCTOR:
            return DoctorProfileSerializer
        elif user_role == User.Role.HOSPITAL: # <-- HANDLE HOSPITAL ROLE
            return HospitalProfileSerializer
        # Default to Client
        return ClientProfileSerializer

    def get_object(self):
        """
        Return the profile object associated with the currently authenticated user.
        """
        user = self.request.user
        user_role = user.role
        
        if user_role == User.Role.DOCTOR:
            return user.doctorprofile
        elif user_role == User.Role.HOSPITAL: # <-- HANDLE HOSPITAL ROLE
            return user.hospitalprofile
        # Default to Client
        return user.clientprofile