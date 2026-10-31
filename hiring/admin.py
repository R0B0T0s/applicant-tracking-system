from django.contrib import admin

from .models import Application, Candidate, JobOpening, Skill, StageChange


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
    filter_horizontal = ["skills"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ["name"]


class StageChangeInline(admin.TabularInline):
    model = StageChange
    fields = ["from_stage", "to_stage", "changed_by", "changed_at"]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "job_opening", "stage", "applied_at"]
    list_filter = ["stage"]
    search_fields = [
        "candidate__first_name",
        "candidate__last_name",
        "candidate__email",
        "job_opening__title",
    ]
    inlines = [StageChangeInline]

    # Applications and their history are created and moved only in the app,
    # so every change is validated and recorded. The admin is read-only.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
