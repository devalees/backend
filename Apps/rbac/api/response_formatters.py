from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from urllib.parse import urljoin
from django.conf import settings

class BaseResponseFormatter:
    """Base class for standardizing API responses"""
    
    def __init__(self, request=None, serializer_class=None):
        self.request = request
        self.base_url = request.build_absolute_uri('/') if request else settings.BASE_URL
        self.serializer_class = serializer_class
    
    def get_serializer(self, instance, many=False):
        """Get serializer for the instance"""
        if not self.serializer_class:
            raise AttributeError("Serializer class not provided")
        return self.serializer_class(instance, many=many)
    
    def format_list_response(self, data, paginator=None):
        """Format list response according to JSON:API specification"""
        response_data = {
            'data': [],
            'meta': {},
            'links': {}
        }

        # Format data
        if isinstance(data, list):
            response_data['data'] = data
        else:
            response_data['data'] = self.get_serializer(data, many=True).data

        # Add pagination metadata if paginator is provided
        if paginator:
            response_data['meta'].update({
                'count': paginator.page.paginator.count,
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'page_size': paginator.get_page_size(self.request)
            })

            # Add pagination links
            response_data['links'] = {
                'self': self.request.build_absolute_uri(),
                'first': paginator.get_first_link(),
                'last': paginator.get_last_link(),
                'next': paginator.get_next_link(),
                'prev': paginator.get_previous_link()
            }

        return Response(response_data)
    
    def format_detail_response(self, instance, status=None):
        """Format detail response according to JSON:API specification"""
        if isinstance(instance, dict):
            data = instance.copy()  # Create a copy to avoid modifying the original
            if 'attributes' not in data:
                data['attributes'] = {}
            # Move fields to attributes
            fields_to_move = ['name', 'description', 'code', 'is_active', 'created_at', 'updated_at', 'id']
            for field in fields_to_move:
                if field in data:
                    data['attributes'][field] = data[field]
        else:
            serializer = self.get_serializer(instance)
            data = serializer.data
            
            # Ensure attributes exists
            if 'attributes' not in data:
                data['attributes'] = {}

            # Move fields to attributes
            fields_to_move = ['name', 'description', 'code', 'is_active', 'created_at', 'updated_at', 'id']
            for field in fields_to_move:
                if field in data:
                    data['attributes'][field] = data.pop(field)

            # Add name to attributes if it exists in the instance
            if hasattr(instance, 'name'):
                data['attributes']['name'] = instance.name

        response_data = {
            'data': data,
            'meta': {},
            'included': []
        }

        # Add related resources to included
        if hasattr(instance, '_prefetched_objects_cache'):
            for field_name, related_objects in instance._prefetched_objects_cache.items():
                if related_objects:
                    if isinstance(related_objects, list):
                        for obj in related_objects:
                            if hasattr(obj, 'id'):
                                response_data['included'].append({
                                    'id': str(obj.id),
                                    'type': obj._meta.model_name + 's',
                                    'attributes': self.get_serializer(obj).data
                                })
                    elif hasattr(related_objects, 'id'):
                        response_data['included'].append({
                            'id': str(related_objects.id),
                            'type': related_objects._meta.model_name + 's',
                            'attributes': self.get_serializer(related_objects).data
                        })

        return Response(response_data, status=status)
    
    def format_error_response(self, errors, status=None):
        """Format error response"""
        # If errors is already a dict, use it directly
        if isinstance(errors, dict):
            error_data = errors
        # If errors is a list, convert it to a dict
        elif isinstance(errors, list):
            error_data = {}
            for error in errors:
                if isinstance(error, dict):
                    error_data.update(error)
                else:
                    error_data['detail'] = error
        # If errors is a string or other type, wrap it in a dict
        else:
            error_data = {'detail': errors}
        
        response_data = {
            'errors': error_data,
            'meta': {},
            'links': {}
        }
        return Response(response_data, status=status)
    
    def _get_page_url(self, page_number):
        """Generate URL for a specific page"""
        if not self.request:
            return None
            
        query_params = self.request.GET.copy()
        query_params['page'] = page_number
        return f"{self.request.path}?{query_params.urlencode()}"
    
    def _get_resource_type(self, serializer):
        """Get the resource type from serializer"""
        if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
            return serializer.Meta.model._meta.model_name + 's'
        return None
    
    def _get_relationships(self, data, serializer):
        """Get relationships from serializer"""
        relationships = {}
        if hasattr(serializer, 'get_fields'):
            for field_name, field in serializer.get_fields().items():
                if hasattr(field, 'get_attribute'):
                    value = field.get_attribute(data)
                    if value is not None:
                        relationships[field_name] = {
                            'data': {
                                'id': str(value.id),
                                'type': self._get_resource_type(field)
                            }
                        }
        return relationships 