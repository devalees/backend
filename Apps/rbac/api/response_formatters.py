from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from urllib.parse import urljoin
from django.conf import settings
from rest_framework import serializers

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

            # Handle relationships
            relationships = {}
            for field_name, field in serializer.fields.items():
                if isinstance(field, serializers.RelatedField):
                    relationships[field_name] = {
                        'data': None
                    }
                    related = getattr(instance, field_name, None)
                    if related:
                        if isinstance(field, serializers.ManyRelatedField):
                            relationships[field_name]['data'] = [
                                {
                                    'type': self._get_resource_type(field.child_relation),
                                    'id': str(item.id)
                                }
                                for item in related.all()
                            ]
                        else:
                            relationships[field_name]['data'] = {
                                'type': self._get_resource_type(field),
                                'id': str(related.id)
                            }
            if relationships:
                data['relationships'] = relationships

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
        """Format error response according to JSON:API specification"""
        error_list = []
        
        # Convert errors to a list of error objects
        if isinstance(errors, dict):
            for key, value in errors.items():
                if isinstance(value, list):
                    for error in value:
                        # Handle pre-formatted errors
                        if isinstance(error, dict) and 'source' in error:
                            error_list.append({
                                'status': str(status or '400'),
                                'source': error['source'],
                                'title': 'Validation Error',
                                'detail': error['detail']
                            })
                        # Handle unique constraint violations
                        elif key == 'non_field_errors' and 'unique set' in str(error):
                            fields = str(error).split('fields ')[1].split(' must')[0].split(', ')
                            for field in fields:
                                error_list.append({
                                    'status': str(status or '400'),
                                    'source': {'pointer': f"/data/attributes/{field}"},
                                    'title': 'Validation Error',
                                    'detail': str(error)
                                })
                        # Handle relationship errors
                        elif key in ['parent', 'organization', 'user', 'role', 'resource']:
                            error_list.append({
                                'status': str(status or '400'),
                                'source': {'pointer': f"/data/relationships/{key}"},
                                'title': 'Validation Error',
                                'detail': str(error)
                            })
                        # Handle other field errors
                        else:
                            pointer = f"/data/attributes/{key}"
                            if key.startswith('relationships.'):
                                field = key.split('.')[1]
                                pointer = f"/data/relationships/{field}"
                            error_list.append({
                                'status': str(status or '400'),
                                'source': {'pointer': pointer},
                                'title': 'Validation Error',
                                'detail': str(error)
                            })
                else:
                    # Handle pre-formatted errors
                    if isinstance(value, dict) and 'source' in value:
                        error_list.append({
                            'status': str(status or '400'),
                            'source': value['source'],
                            'title': 'Validation Error',
                            'detail': value['detail']
                        })
                    # Handle relationship errors
                    elif key in ['parent', 'organization', 'user', 'role', 'resource']:
                        error_list.append({
                            'status': str(status or '400'),
                            'source': {'pointer': f"/data/relationships/{key}"},
                            'title': 'Validation Error',
                            'detail': str(value)
                        })
                    # Handle other field errors
                    else:
                        pointer = f"/data/attributes/{key}"
                        if key.startswith('relationships.'):
                            field = key.split('.')[1]
                            pointer = f"/data/relationships/{field}"
                        error_list.append({
                            'status': str(status or '400'),
                            'source': {'pointer': pointer},
                            'title': 'Validation Error',
                            'detail': str(value)
                        })
        elif isinstance(errors, list):
            for error in errors:
                # Handle pre-formatted errors
                if isinstance(error, dict) and 'source' in error:
                    error_list.append({
                        'status': str(status or '400'),
                        'source': error['source'],
                        'title': 'Validation Error',
                        'detail': error['detail']
                    })
                else:
                    error_list.append({
                        'status': str(status or '400'),
                        'source': {'pointer': '/data/attributes/non_field_errors'},
                        'title': 'Validation Error',
                        'detail': str(error)
                    })
        else:
            error_list.append({
                'status': str(status or '400'),
                'source': {'pointer': '/data/attributes/non_field_errors'},
                'title': 'Validation Error',
                'detail': str(errors)
            })

        return Response({'errors': error_list}, status=status)
    
    def _get_page_url(self, page_number):
        """Get URL for a specific page number"""
        if not self.request:
            return None
        return self.request.build_absolute_uri(f'?page={page_number}')
    
    def _get_resource_type(self, serializer):
        """Get resource type from serializer"""
        if hasattr(serializer.Meta, 'resource_name'):
            return serializer.Meta.resource_name
        return serializer.Meta.model._meta.model_name + 's'
    
    def _get_relationships(self, data, serializer):
        """Get relationships from serializer data"""
        relationships = {}
        for field_name, field in serializer.fields.items():
            if isinstance(field, serializers.RelatedField):
                relationships[field_name] = {
                    'data': None
                }
                related = getattr(data, field_name, None)
                if related:
                    if isinstance(field, serializers.ManyRelatedField):
                        relationships[field_name]['data'] = [
                            {
                                'type': self._get_resource_type(field.child_relation),
                                'id': str(item.id)
                            }
                            for item in related.all()
                        ]
                    else:
                        relationships[field_name]['data'] = {
                            'type': self._get_resource_type(field),
                            'id': str(related.id)
                        }
        return relationships 