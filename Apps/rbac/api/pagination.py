from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .response_formatters import BaseResponseFormatter

class RBACPagination(PageNumberPagination):
    """Custom pagination for RBAC API responses"""
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Override to use our custom response format"""
        formatter = BaseResponseFormatter(self.request)
        return formatter.format_list_response(
            data=data,
            paginator=self
        )

    def get_first_link(self):
        """Get the URL for the first page"""
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, 1)

    def get_last_link(self):
        """Get the URL for the last page"""
        if not self.page.has_next():
            return None
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, self.page.paginator.num_pages)

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for consistent pagination across the API.
    
    Attributes:
        page_size: Default number of items per page
        page_size_query_param: Query parameter to override page size
        max_page_size: Maximum allowed page size
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data, message="Data retrieved successfully"):
        """
        Create a standardized paginated response.
        
        Args:
            data: The serialized data to be paginated
            message: Optional message to include in the response
        
        Returns:
            Response: A standardized paginated response
        """
        return get_paginated_response(
            data=data,
            count=self.page.paginator.count,
            page=self.page.number,
            page_size=self.get_page_size(self.request),
            message=message
        ) 