from django import forms

from .models import Candidate


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
