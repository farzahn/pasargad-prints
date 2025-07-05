"""
Custom permissions for the application
"""
from rest_framework import permissions


class IsStaffOrSuperUser(permissions.BasePermission):
    """
    Permission that allows access only to staff or superuser accounts
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated and is staff or superuser
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission that allows access to owners of objects or staff members
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow staff/superuser full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if the object has a user attribute and user owns it
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For user objects, check if it's the same user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to everyone, 
    but write access only to owners or staff
    """
    
    def has_permission(self, request, view):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions for authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow staff/superuser full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False