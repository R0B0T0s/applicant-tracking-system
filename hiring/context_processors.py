from .permissions import is_hiring_manager


def roles(request):
    return {"is_hiring_manager": is_hiring_manager(request.user)}
