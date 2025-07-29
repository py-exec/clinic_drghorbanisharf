from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or not user.is_verified:
                raise PermissionDenied("دسترسی غیرمجاز")
            if not user.groups.filter(name__in=roles).exists():
                raise PermissionDenied("اجازه دسترسی ندارید")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator