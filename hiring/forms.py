from django import forms
from django.core.exceptions import ValidationError

from .models import Application, Candidate, JobOpening, Skill


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "url",
            "location",
            "source",
            "source_details",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}

    def clean_email(self):
        # Lowercase before the unique check so it matches the stored value.
        return self.cleaned_data["email"].lower()


class JobOpeningForm(forms.ModelForm):
    class Meta:
        model = JobOpening
        # Status is changed only by the manager close/reopen actions.
        fields = [
            "title",
            "department",
            "location",
            "employment_type",
            "hiring_manager",
            "number_of_positions",
            "salary_min",
            "salary_max",
            "description",
            "skills",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "skills": forms.CheckboxSelectMultiple,
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]


class ApplicationForm(forms.ModelForm):
    """Record an application with either the candidate or the job opening fixed."""

    class Meta:
        model = Application
        fields = ["candidate", "job_opening"]

    def __init__(self, *args, candidate=None, job_opening=None, **kwargs):
        super().__init__(*args, **kwargs)
        if candidate is not None:
            self.instance.candidate = candidate
            del self.fields["candidate"]
            self.fields["job_opening"].queryset = JobOpening.objects.filter(
                status=JobOpening.Status.OPEN
            )
        else:
            self.instance.job_opening = job_opening
            del self.fields["job_opening"]
            self.fields["candidate"].queryset = Candidate.objects.filter(
                is_archived=False
            )

    def validate_constraints(self):
        # Django skips constraints on fields missing from the form, which would
        # skip the one-application-per-candidate-and-job check. Check them all.
        try:
            self.instance.validate_constraints()
        except ValidationError as error:
            self.add_error(None, error)
