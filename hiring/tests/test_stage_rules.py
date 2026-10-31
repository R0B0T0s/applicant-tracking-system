import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from hiring.models import Application, Candidate, JobOpening
from hiring.permissions import HIRING_MANAGER_GROUP
from hiring.stages import allowed_moves


@pytest.mark.parametrize(
    "stage, expected",
    [
        # Forward any number of stages up to Offer, back one, or exit.
        (
            "applied",
            [
                "screening",
                "interview",
                "final_review",
                "offer",
                "rejected",
                "withdrawn",
            ],
        ),
        (
            "screening",
            ["applied", "interview", "final_review", "offer", "rejected", "withdrawn"],
        ),
        ("interview", ["screening", "final_review", "offer", "rejected", "withdrawn"]),
        ("final_review", ["interview", "offer", "rejected", "withdrawn"]),
        # Hired is reachable only from Offer.
        ("offer", ["final_review", "hired", "rejected", "withdrawn"]),
        # Final stages have no normal moves.
        ("hired", []),
        ("rejected", []),
        ("withdrawn", []),
    ],
)
def test_allowed_moves_match_the_rules(stage, expected):
    assert sorted(allowed_moves(stage)) == sorted(expected)


@pytest.fixture
def staff():
    return User.objects.create_user("staff", password="pw")


@pytest.fixture
def application(staff):
    manager = User.objects.create_user("manager", password="pw")
    manager.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    candidate = Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        source=Candidate.Source.WEBSITE,
    )
    job = JobOpening.objects.create(
        title="Backend Engineer",
        department="Engineering",
        location="Austin, TX",
        employment_type=JobOpening.EmploymentType.FULL_TIME,
        description="Build and run our APIs.",
        hiring_manager=manager,
    )
    return Application.objects.create_application(candidate, job, manager)


@pytest.mark.django_db
def test_move_to_stage_updates_stage_and_records_history(staff, application):
    application.move_to_stage(Application.Stage.INTERVIEW, staff)

    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW
    latest = application.stage_changes.last()
    assert application.stage_changes.count() == 2
    assert latest.from_stage == Application.Stage.APPLIED
    assert latest.to_stage == Application.Stage.INTERVIEW
    assert latest.changed_by == staff
    assert latest.changed_at is not None

    # Hired is not reachable from Interview: refused, nothing changes.
    with pytest.raises(ValidationError):
        application.move_to_stage(Application.Stage.HIRED, staff)

    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW
    assert application.stage_changes.count() == 2


@pytest.mark.django_db
def test_applications_on_closed_openings_can_still_move(staff, application):
    application.job_opening.status = JobOpening.Status.CLOSED
    application.job_opening.save()

    application.move_to_stage(Application.Stage.SCREENING, staff)

    application.refresh_from_db()
    assert application.stage == Application.Stage.SCREENING


@pytest.mark.django_db
def test_unknown_stage_is_refused(staff, application):
    with pytest.raises(ValidationError):
        application.move_to_stage("bogus", staff)

    application.refresh_from_db()
    assert application.stage == Application.Stage.APPLIED
