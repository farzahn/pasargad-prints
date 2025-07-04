"""
Custom decorators for logging and monitoring
"""
import logging
import time
import functools
from django.db import transaction
from django.core.cache import cache

logger = logging.getLogger(__name__)


def log_execution_time(func):
    """
    Decorator to log function execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed successfully in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    return wrapper


def log_payment_operation(func):
    """
    Decorator specifically for payment operations with detailed logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract relevant information
        request = None
        for arg in args:
            if hasattr(arg, 'user') and hasattr(arg, 'method'):
                request = arg
                break
        
        user_id = None
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        operation_id = f"{func.__name__}_{int(time.time())}"
        
        logger.info(f"Payment operation started: {operation_id} - {func.__name__} - User: {user_id}")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"Payment operation completed: {operation_id} - {func.__name__} - "
                f"User: {user_id} - Duration: {execution_time:.3f}s"
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"Payment operation failed: {operation_id} - {func.__name__} - "
                f"User: {user_id} - Duration: {execution_time:.3f}s - "
                f"Error: {str(e)}",
                exc_info=True
            )
            raise
    return wrapper


def retry_on_exception(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Decorator to retry a function on specified exceptions
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_retries}): {str(e)}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(cache_key_prefix, timeout=300):
    """
    Decorator to cache function results
    
    Args:
        cache_key_prefix: Prefix for the cache key
        timeout: Cache timeout in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            cache_key = f"{cache_key_prefix}:{func.__name__}"
            
            # Add args to cache key
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args)}"
            
            # Add kwargs to cache key
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set for {cache_key} with timeout {timeout}s")
            
            return result
        return wrapper
    return decorator


def require_lock(lock_key_prefix, timeout=10):
    """
    Decorator to ensure only one instance of a function runs at a time
    using cache-based locking
    
    Args:
        lock_key_prefix: Prefix for the lock key
        timeout: Lock timeout in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_key = f"{lock_key_prefix}:{func.__name__}"
            
            # Try to acquire lock
            if cache.add(lock_key, "locked", timeout):
                try:
                    return func(*args, **kwargs)
                finally:
                    cache.delete(lock_key)
            else:
                logger.warning(f"Could not acquire lock for {func.__name__}")
                raise Exception(f"Function {func.__name__} is already running")
        return wrapper
    return decorator