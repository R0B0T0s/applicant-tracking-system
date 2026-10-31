from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone

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

    def archive_blocked_reason(self):
        """Return why this candidate can't be archived, or None if they can."""
        if self.applications.filter(stage__in=Application.ACTIVE_STAGES).exists():
            return (
                f"{self} has active applications. Withdraw or reject their "
                "active applications before archiving."
            )
        return None

    def archive(self):
        reason = self.archive_blocked_reason()
        if reason:
            raise ValidationError(reason)
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save()

    def unarchive(self):
        self.is_archived = False
        self.archived_at = None
        self.save()


class Skill(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_skill_name_ci",
                violation_error_message="A skill with this name already exists.",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def validate_constraints(self, exclude=None):
        try:
            super().validate_constraints(exclude=exclude)
        except ValidationError as error:
            # The Lower("name") constraint can't name its field, so Django
            # reports it as a non-field error. Put it on the name field.
            raise ValidationError({"name": error.messages}) from error


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
    skills = models.ManyToManyField(Skill, blank=True, related_name="job_openings")

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


class ApplicationManager(models.Manager):
    def create_application(self, candidate, job_opening, user):
        """Create an application in Applied and record its first history entry."""
        application = self.model(candidate=candidate, job_opening=job_opening)
        application.full_clean()
        with transaction.atomic():
            application.save()
            application.stage_changes.create(
                to_stage=Application.Stage.APPLIED, changed_by=user
            )
        return application


class Application(models.Model):
    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interview"
        FINAL_REVIEW = "final_review", "Final Review"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    ACTIVE_STAGES = [
        Stage.APPLIED,
        Stage.SCREENING,
        Stage.INTERVIEW,
        Stage.FINAL_REVIEW,
        Stage.OFFER,
    ]

    candidate = models.ForeignKey(
        Candidate, on_delete=models.PROTECT, related_name="applications"
    )
    job_opening = models.ForeignKey(
        JobOpening, on_delete=models.PROTECT, related_name="applications"
    )
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.APPLIED
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    objects = ApplicationManager()

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job_opening"],
                name="unique_application_per_candidate_job",
                violation_error_message=(
                    "This candidate has already applied to this job opening."
                ),
            )
        ]

    def __str__(self):
        return f"{self.candidate} → {self.job_opening}"

    def clean(self):
        # Only new applications are refused; existing ones keep moving.
        if self.pk is not None:
            return
        errors = []
        if self.job_opening_id and self.job_opening.status == JobOpening.Status.CLOSED:
            errors.append("This job opening is closed and not accepting applications.")
        if self.candidate_id and self.candidate.is_archived:
            errors.append("Archived candidates cannot receive new applications.")
        if errors:
            raise ValidationError(errors)


class StageChange(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="stage_changes"
    )
    # Empty for the first entry, when the application is created.
    from_stage = models.CharField(
        max_length=20, choices=Application.Stage.choices, blank=True
    )
    to_stage = models.CharField(max_length=20, choices=Application.Stage.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at", "pk"]

    def __str__(self):
        return f"{self.from_stage or '—'} → {self.to_stage}"
