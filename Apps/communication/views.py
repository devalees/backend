from django.http import HttpResponse, Http404, HttpResponseNotModified
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Audio, RichTextMessage
from .services.audio import AudioProcessingService
from .services.transcription import TranscriptionService
import os
import re
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from Apps.communication.models import EmailTemplate, EmailTracking, EmailAnalytics
from Apps.communication.serializers import EmailTemplateSerializer, EmailTrackingSerializer, EmailAnalyticsSerializer, RichTextMessageSerializer
from Apps.communication.services.email_service import EmailService
import base64
import logging
import tempfile
import shutil

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_audio(request):
    """Upload an audio file and process it."""
    if 'audio_file' not in request.FILES:
        return Response(
            {'error': 'No audio file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    audio_file = request.FILES['audio_file']
    audio_service = AudioProcessingService()
    
    # Validate the audio file
    is_valid, error_message = audio_service.validate_audio_file(audio_file)
    if not is_valid:
        return Response(
            {'error': error_message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Process the audio file
    features = audio_service.process_audio(audio_file)
    if not features:
        return Response(
            {'error': 'Failed to process audio file'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save the audio file
    audio = Audio.objects.create(
        file=audio_file,
        duration=features['duration'],
        sample_rate=features['sample_rate'],
        channels=features['channels']
    )
    
    return Response({
        'id': audio.id,
        'duration': audio.duration,
        'sample_rate': audio.sample_rate,
        'channels': audio.channels,
        'file_size': audio.get_file_size()
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def play_audio(request, audio_id):
    """Stream an audio file with support for range requests."""
    try:
        audio = Audio.objects.get(id=audio_id)
    except Audio.DoesNotExist:
        raise Http404("Audio file not found")
    
    file_path = audio.file.path
    file_size = int(audio.get_file_size())  # Ensure file_size is an integer
    content_type = audio.get_content_type()
    
    # Handle range requests
    range_header = request.META.get('HTTP_RANGE', '').strip()
    if range_header and not re.match(r'bytes=\d*-\d*$', range_header):
        return HttpResponse(
            status=400,
            reason='Invalid range format'
        )
    
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    
    if range_match:
        first_byte = int(range_match.group(1))  # Convert to integer
        last_byte_str = range_match.group(2)
        
        # Handle empty last_byte_str
        if last_byte_str:
            last_byte = int(last_byte_str)
            # Validate range values
            if first_byte >= file_size or first_byte > last_byte:
                return HttpResponse(
                    status=416,
                    reason='Requested range not satisfiable'
                )
        else:
            last_byte = file_size - 1
            # Validate first_byte
            if first_byte >= file_size:
                return HttpResponse(
                    status=416,
                    reason='Requested range not satisfiable'
                )
        
        length = last_byte - first_byte + 1
        # Ensure we don't read past the end of the file
        if last_byte >= file_size:
            last_byte = file_size - 1
            length = file_size - first_byte
        
        response = HttpResponse(
            status=206,
            content_type=content_type
        )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        
        with open(file_path, 'rb') as f:
            f.seek(first_byte)
            response.write(f.read(length))
    else:
        # Full file request
        response = HttpResponse(
            content_type=content_type
        )
        response['Content-Length'] = str(file_size)
        
        with open(file_path, 'rb') as f:
            response.write(f.read())
    
    response['Accept-Ranges'] = 'bytes'
    return response 

@api_view(['POST'])
def compress_audio(request, audio_id):
    try:
        # Get the audio file by ID instead of from request
        try:
            from Apps.communication.models import Audio
            audio_file_obj = Audio.objects.get(id=audio_id)
            audio_file = audio_file_obj.file
        except Audio.DoesNotExist:
            return Response({'error': 'Audio file not found'}, status=404)
            
        quality = float(request.data.get('quality', 0.5))
        
        if not 0 <= quality <= 1:
            return Response({'error': 'Quality must be between 0.0 and 1.0'}, status=400)
            
        service = AudioProcessingService()
        
        # Validate the audio file
        if not service.validate_audio_file(audio_file)[0]:
            return Response({'error': 'Invalid audio file format or size'}, status=400)
            
        # Process the audio file
        compressed_content = service.compress_audio(audio_file, quality)
        
        # Get original file info for comparison
        original_file_path = audio_file.path
        original_size = os.path.getsize(original_file_path)
        
        # Generate a unique filename for the compressed file
        filename = f"compressed_{os.path.splitext(audio_file.name)[0]}.mp3"
        
        # Save compressed file temporarily to get its size
        temp_compressed_path = os.path.join(tempfile.gettempdir(), 'compressed_audio', filename)
        os.makedirs(os.path.dirname(temp_compressed_path), exist_ok=True)
        
        with open(temp_compressed_path, 'wb') as f:
            f.write(compressed_content)
        compressed_size = os.path.getsize(temp_compressed_path)
        
        # Create URL for compressed file
        compressed_url = request.build_absolute_uri(f'/media/compressed/{filename}')
        
        # Save the compressed file
        compressed_dir = os.path.join(settings.MEDIA_ROOT, 'compressed')
        os.makedirs(compressed_dir, exist_ok=True)
        compressed_path = os.path.join(compressed_dir, filename)
        
        # Make sure the parent directories exist
        os.makedirs(os.path.dirname(compressed_path), exist_ok=True)
        
        shutil.copy(temp_compressed_path, compressed_path)
        
        # Clean up temp file
        os.remove(temp_compressed_path)
        
        return Response({
            'message': 'Audio compressed successfully',
            'compressed_file': compressed_url,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': f"{(original_size - compressed_size) / original_size * 100:.2f}%"
        })
        
    except ValueError as e:
        logger.error(f"Validation error in compress_audio: {str(e)}")
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error in compress_audio: {str(e)}")
        return Response({'error': 'Failed to compress audio file'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """
    Transcribe an audio file using OpenAI's Whisper model.
    Supports Arabic language and its various locales.
    """
    if 'audio_file' not in request.FILES:
        return Response(
            {"error": "No audio file provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    language = request.data.get('language', 'ar')
    
    try:
        transcription_service = TranscriptionService()
        result = transcription_service.transcribe_audio(
            request.FILES['audio_file'],
            language=language
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class RichTextMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing rich text messages"""
    queryset = RichTextMessage.objects.all()
    serializer_class = RichTextMessageSerializer
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )

class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email templates"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """Send a test email using the template"""
        template = self.get_object()
        test_email = request.data.get('test_email')
        context = request.data.get('context', {})
        
        if not test_email:
            return Response(
                {"error": "Test email address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            email_service = EmailService()
            email_service.send_templated_email(template.name, test_email, context)
            return Response({"status": "Test email sent successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmailTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email tracking data"""
    queryset = EmailTracking.objects.all()
    serializer_class = EmailTrackingSerializer
    
    @action(detail=True, methods=['post'])
    def track_open(self, request, pk=None):
        """Track email open event"""
        tracking = self.get_object()
        try:
            email_service = EmailService()
            email_service.track_email_open(str(tracking.tracking_id))
            return Response({"status": "Open tracked successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        """Track email click event"""
        tracking = self.get_object()
        try:
            email_service = EmailService()
            email_service.track_email_click(str(tracking.tracking_id))
            return Response({"status": "Click tracked successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmailAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email analytics"""
    queryset = EmailAnalytics.objects.all()
    serializer_class = EmailAnalyticsSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary analytics for all emails"""
        total_emails = self.queryset.count()
        total_opens = sum(analytics.opens for analytics in self.queryset)
        total_clicks = sum(analytics.clicks for analytics in self.queryset)
        total_bounces = sum(analytics.bounces for analytics in self.queryset)
        
        return Response({
            "total_emails": total_emails,
            "total_opens": total_opens,
            "total_clicks": total_clicks,
            "total_bounces": total_bounces,
            "open_rate": (total_opens / total_emails * 100) if total_emails > 0 else 0,
            "click_rate": (total_clicks / total_emails * 100) if total_emails > 0 else 0,
            "bounce_rate": (total_bounces / total_emails * 100) if total_emails > 0 else 0
        }) 