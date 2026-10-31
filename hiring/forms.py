from django import forms

from .models import Candidate, JobOpening


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
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}
