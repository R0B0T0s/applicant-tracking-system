from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .permissions import HIRING_MANAGER_GROUP


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


class JobOpening(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    description = models.TextField()
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    hiring_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        # Applies to both the form's choices and model validation.
        limit_choices_to={"groups__name": HIRING_MANAGER_GROUP},
        related_name="managed_job_openings",
    )
    number_of_positions = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("hiring:job_detail", args=[self.pk])

    def clean(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValidationError(
                {"salary_min": "Minimum salary cannot be greater than the maximum."}
            )
