"""
Custom exception handlers and error classes for Pasargad Prints
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    and proper logging for all exceptions.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request information for logging
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception with context
    logger.error(
        f"Exception in {view.__class__.__name__ if view else 'Unknown'}: {exc}",
        exc_info=True,
        extra={
            'request_method': request.method if request else None,
            'request_path': request.path if request else None,
            'request_user': request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else None,
        }
    )
    
    # Now add custom handling for specific exceptions
    if response is not None:
        # Standardize the error response format
        custom_response_data = {
            'error': True,
            'message': _get_error_message(exc, response),
            'status_code': response.status_code,
        }
        
        # Add field errors if available
        if hasattr(response, 'data') and isinstance(response.data, dict):
            if 'detail' not in response.data:
                custom_response_data['errors'] = response.data
            
        response.data = custom_response_data
    else:
        # Handle non-DRF exceptions
        if isinstance(exc, DjangoValidationError):
            response = Response({
                'error': True,
                'message': 'Validation error',
                'status_code': 400,
                'errors': exc.message_dict if hasattr(exc, 'message_dict') else {'detail': str(exc)}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif isinstance(exc, IntegrityError):
            response = Response({
                'error': True,
                'message': 'Database integrity error. This operation would violate data constraints.',
                'status_code': 409,
            }, status=status.HTTP_409_CONFLICT)
        
        elif isinstance(exc, Http404):
            response = Response({
                'error': True,
                'message': 'Resource not found',
                'status_code': 404,
            }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            # Generic server error for unhandled exceptions
            response = Response({
                'error': True,
                'message': 'An unexpected error occurred. Please try again later.',
                'status_code': 500,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response


def _get_error_message(exc, response):
    """
    Extract a user-friendly error message from the exception
    """
    if hasattr(response, 'data'):
        if isinstance(response.data, dict) and 'detail' in response.data:
            return str(response.data['detail'])
        elif isinstance(response.data, list) and response.data:
            return str(response.data[0])
    
    # Default messages for common status codes
    status_messages = {
        400: 'Bad request. Please check your input.',
        401: 'Authentication required. Please log in.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        405: 'Method not allowed.',
        409: 'Conflict. The resource already exists or cannot be modified.',
        429: 'Too many requests. Please slow down.',
        500: 'Internal server error. Please try again later.',
        503: 'Service temporarily unavailable. Please try again later.',
    }
    
    return status_messages.get(
        response.status_code,
        f'Error {response.status_code}: {exc.__class__.__name__}'
    )


class PaymentError(Exception):
    """Base exception for payment-related errors"""
    pass


class InsufficientStockError(Exception):
    """Raised when trying to purchase more items than available in stock"""
    pass


class InvalidOrderStateError(Exception):
    """Raised when an invalid order state transition is attempted"""
    pass


class EmailError(Exception):
    """Base exception for email-related errors"""
    pass