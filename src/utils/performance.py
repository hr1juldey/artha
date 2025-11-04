"""Performance monitoring"""
import time
from functools import wraps

def time_it(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        if elapsed > 1.0:  # Log slow operations
            print(f"[SLOW] {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper