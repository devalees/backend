from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .serializers import UserSerializer, ChangePasswordSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
from django.db.models import Q
import pyotp
import logging

# Import filtering utilities
from Apps.filtering.filters import apply_filters, get_available_filters
from Apps.filtering.aggregations import apply_aggregations, get_available_aggregations

logger = logging.getLogger(__name__)

User = get_user_model()

# Custom permission class for RBAC-like functionality
class UserPermission(permissions.BasePermission):
    """
    Custom permission class that implements RBAC-like functionality
    without using direct RBAC inheritance
    """
    def has_permission(self, request, view):
        """
        Global permission check
        """
        # Allow authentication endpoints
        if view.action in ['login', 'refresh_token', 'password_reset', 'password_reset_confirm', 'register', 'verify_2fa']:
            return True
        
        # Authenticated users can access basic functionality
        if not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
            
        # List view should show only authorized users 
        if view.action == 'list':
            return True
        
        # For retrieve, update, destroy - check in has_object_permission
        if view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return True
            
        # For custom actions
        if view.action in ['available_filters', 'available_aggregations', 'enable_2fa', 
                          'confirm_2fa', 'disable_2fa', 'generate_backup_codes', 'verify_backup_code']:
            return request.user.is_authenticated
            
        # Default deny
        return False
        
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check
        """
        # Superusers always have access
        if request.user.is_superuser:
            return True
            
        # Users can always access their own record
        if obj.id == request.user.id:
            return True
            
        # Check if users are in the same organization
        try:
            user_org = request.user.organization
            obj_org = obj.organization
            
            if not user_org or not obj_org or user_org.id != obj_org.id:
                return False
                
            # Check for admin permissions within the organization
            try:
                if hasattr(request.user, 'has_role'):
                    has_admin = request.user.has_role('admin', user_org)
                    if has_admin:
                        return True
            except Exception as e:
                logger.error(f"Error checking role: {str(e)}")
                pass
        except Exception as e:
            logger.error(f"Organization check error: {str(e)}")
            return False
            
        return False

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model with filtering capabilities"""
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Get permissions based on action"""
        if self.action in ['login', 'refresh_token', 'password_reset', 'password_reset_confirm', 'register', 'verify_2fa']:
            return [AllowAny()]
            
        if self.action in ['available_filters', 'available_aggregations', 'change_password']:
            return [permissions.IsAuthenticated()]
            
        # For all other actions, use the custom permission class
        return [UserPermission()]

    def get_queryset(self):
        """
        Filter queryset based on user permissions and apply filter capabilities
        """
        logger.info(f"User requesting: {self.request.user}")
        logger.info(f"Is authenticated: {self.request.user.is_authenticated}")
        logger.info(f"Is superuser: {self.request.user.is_superuser}")
        
        if self.request.user.is_superuser:
            queryset = User.objects.all().order_by('id')
        else:
            # Get user's organization
            try:
                user_org = self.request.user.organization
                
                if user_org:
                    # Get all users in the same organization
                    queryset = User.objects.filter(
                        Q(organization=user_org) | 
                        Q(team_memberships__team__department__organization=user_org,
                          team_memberships__is_active=True)
                    ).distinct().order_by('id')
                else:
                    # If user doesn't have an organization, show only their own record
                    queryset = User.objects.filter(id=self.request.user.id)
            except Exception as e:
                logger.error(f"Error getting user organization: {str(e)}")
                queryset = User.objects.filter(id=self.request.user.id)
            
        # Apply filters from request
        if 'filters' in self.request.query_params:
            try:
                queryset = apply_filters(queryset, self.request.query_params.get('filters'))
            except Exception as e:
                logger.error(f"Error applying filters: {str(e)}")
            
        return queryset

    def list(self, request, *args, **kwargs):
        """
        List users with support for aggregations
        """
        logger.info("List method called")
        logger.info(f"Request headers: {request.headers}")
        
        # Check if we're doing aggregation
        if 'aggregate' in request.query_params:
            try:
                queryset = self.get_queryset()
                aggregation_results = apply_aggregations(queryset, request.query_params.get('aggregate'))
                return Response(aggregation_results)
            except Exception as e:
                logger.error(f"Error applying aggregations: {str(e)}")
        
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def available_filters(self, request):
        """Return the available filters for User model"""
        try:
            filters = get_available_filters(User)
            return Response(filters)
        except Exception as e:
            logger.error(f"Error getting available filters: {str(e)}")
            return Response({"error": "Error retrieving filters"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def available_aggregations(self, request):
        """Return the available aggregations for User model"""
        try:
            aggregations = get_available_aggregations(User)
            return Response(aggregations)
        except Exception as e:
            logger.error(f"Error getting available aggregations: {str(e)}")
            return Response({"error": "Error retrieving aggregations"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        """Soft delete the user"""
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Login user and return tokens"""
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not password:
            return Response(
                {'error': 'Please provide a password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not username and not email:
            return Response(
                {'error': 'Please provide either username or email'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try to authenticate with username or email
        if username:
            user = authenticate(username=username, password=password)
        else:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

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
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValidationError as e:
            if 'Too many verification attempts' in str(e):
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
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
        new_password2 = request.data.get('new_password2')

        print(f"Debug: uid={uid}, token={token}, new_password={new_password}, new_password2={new_password2}")

        if not uid or not token or not new_password or not new_password2:
            print("Debug: Missing required fields")
            return Response(
                {'error': 'Please provide uid, token, new password and password confirmation'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if new_password != new_password2:
            print("Debug: Passwords do not match")
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Decode the base64 UID
            decoded_uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=decoded_uid)
            print(f"Debug: Found user with id={decoded_uid}")
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, UnicodeDecodeError):
            print("Debug: Invalid uid or user not found")
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            print("Debug: Token validation failed")
            return Response(
                {'error': 'Invalid or expired reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        print("Debug: Password reset successful")

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

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """
        Change password endpoint that requires current password and validates new password.
        """
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Optionally invalidate user's existing tokens by updating token_version
            # This depends on how token validation is implemented in the application
            
            return Response(
                {"success": "Password changed successfully"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
