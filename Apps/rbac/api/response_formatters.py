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
    
    def format_list_response(self, data, paginator=None, page_number=1, page_size=10):
        """Format a list response according to JSON:API specifications"""
        response_data = {
            'data': [],
            'meta': {
                'pagination': {}  # Move pagination data under meta.pagination
            },
            'links': {}
        }

        # Format each item in the data list
        formatted_data = []
        for item in data:
            if isinstance(item, dict):
                formatted_item = item.copy()
                if 'attributes' not in formatted_item:
                    formatted_item['attributes'] = {}
                # Move fields to attributes
                fields_to_move = ['name', 'description', 'code', 'is_active', 'created_at', 'updated_at', 'id', 'message']
                for field in fields_to_move:
                    if field in formatted_item:
                        formatted_item['attributes'][field] = formatted_item[field]
                formatted_data.append(formatted_item)
            else:
                formatted_data.append(item)

        # Add pagination metadata under meta.pagination
        if paginator:
            response_data['meta']['pagination'].update({
                'count': paginator.page.paginator.count,
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'page_size': paginator.get_page_size(paginator.request),
                'has_next': paginator.page.has_next(),
                'has_previous': paginator.page.has_previous()
            })
            
            # Add pagination links
            response_data['links'].update({
                'self': paginator.request.build_absolute_uri(),
                'first': paginator.get_first_link(),
                'last': paginator.get_last_link(),
                'next': paginator.get_next_link(),
                'prev': paginator.get_previous_link()
            })
            
            response_data['data'] = formatted_data
        else:
            # Calculate pagination metadata manually
            total_pages = max(1, (len(data) + page_size - 1) // page_size)
            response_data['meta']['pagination'].update({
                'count': len(data),
                'total_pages': total_pages,
                'current_page': page_number,
                'page_size': page_size,
                'has_next': page_number < total_pages,
                'has_previous': page_number > 1
            })
            
            # Calculate pagination slices
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            paginated_data = formatted_data[start_idx:end_idx]
            
            response_data['data'] = paginated_data
            
            # Add pagination links
            response_data['links'].update({
                'self': self._get_page_url(page_number),
                'first': self._get_page_url(1),
                'last': self._get_page_url(total_pages),
                'next': self._get_page_url(page_number + 1) if page_number < total_pages else None,
                'prev': self._get_page_url(page_number - 1) if page_number > 1 else None
            })

        return Response(response_data)
    
    def format_detail_response(self, instance, status=None):
        """Format detail response according to JSON:API specification"""
        if isinstance(instance, dict):
            data = instance.copy()  # Create a copy to avoid modifying the original
            if 'attributes' not in data:
                data['attributes'] = {}
            # Move fields to attributes
            fields_to_move = ['name', 'description', 'code', 'is_active', 'created_at', 'updated_at', 'id', 'message']
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
            fields_to_move = ['name', 'description', 'code', 'is_active', 'created_at', 'updated_at', 'id', 'message']
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
        error_list = []
        
        # Convert errors to a list of error objects
        if isinstance(errors, dict):
            for key, value in errors.items():
                if isinstance(value, list):
                    for error in value:
                        error_list.append({'detail': f"{key}: {error}"})
                else:
                    error_list.append({'detail': f"{key}: {value}"})
        elif isinstance(errors, list):
            for error in errors:
                if isinstance(error, dict):
                    error_list.append({'detail': str(error)})
                else:
                    error_list.append({'detail': str(error)})
        else:
            error_list.append({'detail': str(errors)})
        
        response_data = {
            'errors': error_list,
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