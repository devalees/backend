from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
import base64
import logging
from .models import User

logger = logging.getLogger(__name__)

@login_required
def two_factor_page(request):
    """Display the 2FA management page"""
    logger.info(f"2FA page accessed by user {request.user.username}. 2FA enabled: {request.user.two_factor_enabled}")
    return render(request, 'users/2fa.html')

@login_required
def setup_2fa(request):
    """Start the 2FA setup process"""
    logger.info(f"Starting 2FA setup for user {request.user}")
    
    if request.method == 'POST':
        # Generate a new 2FA secret
        secret = request.user.generate_2fa_secret()
        request.user.two_factor_secret = secret
        request.user.save()
        logger.info(f"Generated 2FA secret for user {request.user}")
        
        # Generate QR code
        qr_code = request.user.generate_2fa_qr_code()
        logger.info(f"Generated QR code for user {request.user}")
        
        # Refresh user from database to ensure we have the latest data
        request.user.refresh_from_db()
        
        return render(request, 'users/2fa.html', {
            'qr_code': qr_code,
            'secret': request.user.two_factor_secret
        })
    
    return render(request, 'users/2fa.html')

@login_required
def verify_2fa(request):
    """Verify 2FA code and enable 2FA"""
    logger.info(f"Verifying 2FA code for user {request.user}")
    
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            if request.user.verify_2fa_code(code):
                request.user.enable_2fa()
                messages.success(request, '2FA has been enabled successfully')
                return redirect('2fa_page')
            else:
                messages.error(request, 'Invalid verification code')
                return redirect('2fa_page')
        except ValidationError as e:
            logger.error(f"Validation error during 2FA verification for user {request.user}: {str(e)}")
            messages.error(request, str(e))
            return redirect('2fa_page')
    
    return redirect('2fa_page')

@login_required
def disable_2fa(request):
    """Disable 2FA"""
    if request.method == 'POST':
        try:
            logger.info(f"Disabling 2FA for user {request.user.username}")
            request.user.disable_2fa()
            logger.info(f"2FA disabled for user {request.user.username}")
            messages.success(request, '2FA disabled successfully')
        except Exception as e:
            logger.error(f"Error disabling 2FA for user {request.user.username}: {str(e)}")
            messages.error(request, f'Error disabling 2FA: {str(e)}')
        return redirect('2fa_page')
    return redirect('2fa_page')

@login_required
def generate_backup_codes(request):
    """Generate new backup codes for 2FA"""
    logger.info(f"Generating new backup codes for user {request.user}")
    
    if not request.user.two_factor_enabled:
        messages.error(request, '2FA must be enabled to generate backup codes')
        return redirect('2fa_page')
    
    try:
        backup_codes = request.user.generate_backup_codes()
        logger.info(f"Generated new backup codes for user {request.user}")
        messages.success(request, 'New backup codes generated successfully')
        return render(request, 'users/2fa.html', {
            'backup_codes': backup_codes,
            'messages': messages.get_messages(request)
        })
    except Exception as e:
        logger.error(f"Error generating backup codes for user {request.user}: {str(e)}")
        messages.error(request, f'Error generating backup codes: {str(e)}')
        return redirect('2fa_page') 