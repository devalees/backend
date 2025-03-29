from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .serializers import UserSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
import pyotp
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all().order_by('id')  # Add default ordering
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        logger.info(f"User requesting: {self.request.user}")
        logger.info(f"Is authenticated: {self.request.user.is_authenticated}")
        logger.info(f"Is superuser: {self.request.user.is_superuser}")
        
        if self.request.user.is_superuser:
            queryset = User.objects.all().order_by('id')  # Add ordering
            logger.info(f"Superuser access - returning all users. Count: {queryset.count()}")
            return queryset
        
        logger.info(f"Regular user access - returning only user's own record")
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        """Override list method to add debug info"""
        logger.info("List method called")
        logger.info(f"Request headers: {request.headers}")
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ['create', 'login', 'refresh_token', 'register', 'verify_2fa', 'password_reset', 'password_reset_confirm']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        """Soft delete the user"""
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Login user and return tokens"""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(email=email, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if 2FA is enabled
        if user.two_factor_enabled:
            return Response({
                'requires_2fa': True,
                'user_id': user.id,
                'message': '2FA verification required'
            }, status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def verify_2fa(self, request):
        """Verify 2FA code and return tokens"""
        user_id = request.data.get('user_id')
        code = request.data.get('code')

        if not user_id or not code:
            return Response(
                {'error': 'Please provide both user_id and 2FA code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not user.two_factor_enabled:
            return Response(
                {'error': '2FA is not enabled for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if user.verify_2fa_code(code):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            else:
                return Response(
                    {'error': 'Invalid 2FA code'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """Enable 2FA for the current user"""
        user = request.user
        
        try:
            # Generate new 2FA secret
            secret = user.generate_2fa_secret()
            
            # Generate QR code
            qr_code = user.generate_2fa_qr_code()
            
            # Create TOTP URI for manual entry
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                user.username,
                issuer_name=settings.TWO_FACTOR['ISSUER_NAME']
            )
            
            return Response({
                'secret': secret,
                'qr_code': qr_code,
                'totp_uri': totp_uri,
                'manual_entry_code': secret,  # For manual entry in authenticator app
                'message': 'Please either scan the QR code or manually enter the code in your authenticator app',
                'instructions': [
                    '1. Open your authenticator app (Google Authenticator, Authy, etc.)',
                    '2. Choose to add a new account',
                    '3. Either scan the QR code OR',
                    '4. Manually enter the following code: ' + secret,
                    '5. Once added, enter the 6-digit code shown in your app to confirm setup'
                ]
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def confirm_2fa(self, request):
        """Confirm and enable 2FA after verifying the code"""
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response(
                {'error': 'Please provide the 2FA code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if user.verify_2fa_code(code):
                user.enable_2fa()
                # Generate backup codes after enabling 2FA
                backup_codes = user.generate_backup_codes()
                return Response({
                    'message': '2FA has been enabled successfully',
                    'backup_codes': backup_codes
                })
            else:
                return Response(
                    {'error': 'Invalid 2FA code'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """Disable 2FA for the current user"""
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response(
                {'error': 'Please provide the 2FA code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if user.verify_2fa_code(code):
                user.disable_2fa()
                return Response({
                    'message': '2FA has been disabled successfully'
                })
            else:
                return Response(
                    {'error': 'Invalid 2FA code'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def generate_backup_codes(self, request):
        """Generate new backup codes for 2FA"""
        user = request.user
        
        try:
            backup_codes = user.generate_backup_codes()
            return Response({
                'backup_codes': backup_codes,
                'message': 'New backup codes have been generated. Please store them securely.'
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def verify_backup_code(self, request):
        """Verify a backup code"""
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response(
                {'error': 'Please provide the backup code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.verify_backup_code(code):
            return Response({
                'message': 'Backup code verified successfully'
            })
        else:
            return Response(
                {'error': 'Invalid backup code'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def refresh_token(self, request):
        """Refresh access token"""
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token)
            })
        except Exception as e:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout user and blacklist refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def password_reset(self, request):
        """Request password reset"""
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Send password reset email
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
        email_body = f"Please click the following link to reset your password: {reset_url}"
        
        send_mail(
            'Password Reset Requested',
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset email has been sent'})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def password_reset_confirm(self, request):
        """Confirm password reset"""
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response(
                {'error': 'Please provide uid, token and new password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password has been reset successfully'})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
