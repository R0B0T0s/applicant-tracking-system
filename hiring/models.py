from django.db import models
from django.urls import reverse


class Candidate(models.Model):
    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        JOB_BOARD = "job_board", "Job Board"
        REFERRAL = "referral", "Referral"
        OTHER = "other", "Other"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(
        unique=True,
        error_messages={"unique": "A candidate with this email already exists."},
    )
    phone = models.CharField(max_length=30, blank=True)
    url = models.URLField("LinkedIn/portfolio URL", blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    source_details = models.CharField(
        max_length=200,
        blank=True,
        help_text="For example, who referred them or which job board.",
    )
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("hiring:candidate_detail", args=[self.pk])
