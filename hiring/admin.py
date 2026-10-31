from django.contrib import admin

from .models import Candidate, JobOpening


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "email", "source", "is_archived"]
    list_filter = ["source", "is_archived"]
    search_fields = ["first_name", "last_name", "email"]

    def has_delete_permission(self, request, obj=None):
        # Hard deletion is a superuser-only escape hatch; the app has no delete.
        return request.user.is_superuser


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "location", "hiring_manager", "status"]
    list_filter = ["status", "employment_type", "department"]
    search_fields = ["title", "department", "location"]
