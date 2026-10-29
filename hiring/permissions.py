from functools import wraps

from django.core.exceptions import PermissionDenied

HIRING_MANAGER_GROUP = "Hiring Manager"


def is_hiring_manager(user):
    """Return True if the user belongs to the Hiring Manager group."""
    return user.groups.filter(name=HIRING_MANAGER_GROUP).exists()


def hiring_manager_required(view_func):
    """Allow only Hiring Managers; everyone else gets 403 Forbidden."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_hiring_manager(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
