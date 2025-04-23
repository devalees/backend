from rest_framework import serializers
from .models import RichTextMessage
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from Apps.communication.models import EmailTemplate, EmailTracking, EmailAnalytics

class RichTextMessageSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = RichTextMessage
        fields = ['id', 'content', 'sender', 'thread', 'created_at', 'updated_at', 
                 'created_by', 'created_by_name', 'updated_by', 'updated_by_name']
        read_only_fields = ['sender', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate_content(self, value):
        soup = BeautifulSoup(value, 'html.parser')
        
        # Check for script tags
        if soup.find('script'):
            raise serializers.ValidationError('Script tags are not allowed')
        
        # Check for event handlers on any tag
        for tag in soup.find_all(True):
            for attr in tag.attrs:
                if attr.startswith('on'):
                    raise serializers.ValidationError('Event handlers are not allowed in HTML content')
        
        # Check for javascript: URLs in img and iframe tags
        for img in soup.find_all('img'):
            if not img.get('src'):
                raise serializers.ValidationError('Image tags must have a src attribute')
            if img['src'].lower().startswith('javascript:'):
                raise serializers.ValidationError('JavaScript URLs are not allowed in image src')
        
        for iframe in soup.find_all('iframe'):
            if not iframe.get('src'):
                raise serializers.ValidationError('Iframe tags must have a src attribute')
            if iframe['src'].lower().startswith('javascript:'):
                raise serializers.ValidationError('JavaScript URLs are not allowed in iframe src')
        
        # Remove disallowed attributes (style, class) from all tags
        for tag in soup.find_all(True):
            if 'style' in tag.attrs:
                del tag['style']
            if 'class' in tag.attrs:
                del tag['class']

        return str(soup)

    def create(self, validated_data):
        # Ensure sender is set from the request user
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'subject', 'body', 'is_active', 'created_at', 'updated_at',
                 'created_by', 'created_by_name', 'updated_by', 'updated_by_name']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

class EmailTrackingSerializer(serializers.ModelSerializer):
    """Serializer for EmailTracking model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = EmailTracking
        fields = [
            'id', 'tracking_id', 'recipient_email', 'subject', 'status',
            'sent_at', 'opened_at', 'clicked_at', 'bounce_reason',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = [
            'tracking_id', 'sent_at', 'opened_at', 'clicked_at',
            'bounce_reason', 'created_by', 'updated_by'
        ]

class EmailAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for EmailAnalytics model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = EmailAnalytics
        fields = [
            'id', 'email_id', 'opens', 'clicks', 'bounces',
            'created_at', 'updated_at', 'created_by', 'created_by_name', 
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by'] 