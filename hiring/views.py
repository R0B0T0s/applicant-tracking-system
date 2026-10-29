from django.shortcuts import render

from .permissions import hiring_manager_required


def home(request):
    return render(request, "hiring/home.html")


@hiring_manager_required
def manager_tools(request):
    return render(request, "hiring/manager_tools.html")
