from rest_framework.response import Response
from rest_framework import status
from typing import Any, Dict, List, Optional, Union

def create_response(
    data: Optional[Union[Dict, List]] = None,
    message: str = "",
    success: bool = True,
    status_code: int = status.HTTP_200_OK,
    errors: Optional[Union[Dict, List]] = None,
    meta: Optional[Dict] = None
) -> Response:
    """
    Create a standardized API response.
    
    Args:
        data: The main response data
        message: A human-readable message about the response
        success: Whether the request was successful
        status_code: The HTTP status code
        errors: Any errors that occurred
        meta: Additional metadata about the response
    
    Returns:
        Response: A DRF Response object with standardized format
    """
    response_data = {
        "success": success,
        "message": message,
        "data": data or {},
    }

    if errors is not None:
        response_data["errors"] = errors

    if meta is not None:
        response_data["meta"] = meta

    return Response(response_data, status=status_code)

def create_success_response(
    data: Optional[Union[Dict, List]] = None,
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict] = None
) -> Response:
    """Create a standardized success response."""
    return create_response(
        data=data,
        message=message,
        success=True,
        status_code=status_code,
        meta=meta
    )

def create_error_response(
    message: str = "Operation failed",
    errors: Optional[Union[Dict, List]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    meta: Optional[Dict] = None
) -> Response:
    """Create a standardized error response."""
    return create_response(
        message=message,
        success=False,
        status_code=status_code,
        errors=errors,
        meta=meta
    )

def get_paginated_response(
    data: List[Any],
    count: int,
    page: int,
    page_size: int,
    message: str = "Data retrieved successfully"
) -> Response:
    """
    Create a standardized paginated response.
    
    Args:
        data: The paginated data
        count: Total number of items
        page: Current page number
        page_size: Number of items per page
        message: Response message
    
    Returns:
        Response: A DRF Response object with pagination metadata
    """
    total_pages = (count + page_size - 1) // page_size
    
    meta = {
        "pagination": {
            "count": count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    }
    
    return create_success_response(
        data=data,
        message=message,
        meta=meta
    ) 