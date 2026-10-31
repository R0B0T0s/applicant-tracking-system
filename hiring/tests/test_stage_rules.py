import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from hiring.models import Application, Candidate, JobOpening
from hiring.permissions import HIRING_MANAGER_GROUP
from hiring.stages import REOPEN, allowed_moves


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


@pytest.mark.parametrize("stage", ["hired", "rejected", "withdrawn"])
def test_reopen_is_the_only_move_from_a_final_stage_for_managers(stage):
    assert allowed_moves(stage, can_reopen=True) == [REOPEN]
    assert allowed_moves(stage, can_reopen=False) == []


@pytest.mark.parametrize(
    "stage", ["applied", "screening", "interview", "final_review", "offer"]
)
def test_reopen_is_never_offered_from_an_active_stage(stage):
    assert REOPEN not in allowed_moves(stage, can_reopen=True)
    assert allowed_moves(stage, can_reopen=True) == allowed_moves(stage)


@pytest.fixture
def staff():
    return User.objects.create_user("staff", password="pw")


@pytest.fixture
def manager():
    manager = User.objects.create_user("manager", password="pw")
    manager.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    return manager


@pytest.fixture
def application(manager):
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


@pytest.mark.django_db
def test_manager_reopen_returns_to_the_previous_stage(staff, manager, application):
    application.move_to_stage(Application.Stage.INTERVIEW, staff)
    application.move_to_stage(Application.Stage.WITHDRAWN, staff)

    application.move_to_stage(REOPEN, manager)

    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW
    latest = application.stage_changes.last()
    assert (latest.from_stage, latest.to_stage, latest.changed_by) == (
        Application.Stage.WITHDRAWN,
        Application.Stage.INTERVIEW,
        manager,
    )

    # Reversing a hire: Hired -> Reopen (back to Offer) -> Rejected.
    application.move_to_stage(Application.Stage.OFFER, staff)
    application.move_to_stage(Application.Stage.HIRED, staff)
    application.move_to_stage(REOPEN, manager)
    application.move_to_stage(Application.Stage.REJECTED, staff)

    application.refresh_from_db()
    assert application.stage == Application.Stage.REJECTED
    assert [
        (change.from_stage, change.to_stage)
        for change in application.stage_changes.all()
    ] == [
        ("", "applied"),
        ("applied", "interview"),
        ("interview", "withdrawn"),
        ("withdrawn", "interview"),
        ("interview", "offer"),
        ("offer", "hired"),
        ("hired", "offer"),
        ("offer", "rejected"),
    ]


@pytest.mark.django_db
def test_reopen_is_refused_from_an_active_stage(manager, application):
    with pytest.raises(ValidationError):
        application.move_to_stage(REOPEN, manager)

    application.refresh_from_db()
    assert application.stage == Application.Stage.APPLIED
    assert application.stage_changes.count() == 1


@pytest.mark.django_db
def test_staff_cannot_reopen(staff, application):
    application.move_to_stage(Application.Stage.REJECTED, staff)

    with pytest.raises(ValidationError):
        application.move_to_stage(REOPEN, staff)

    application.refresh_from_db()
    assert application.stage == Application.Stage.REJECTED
    assert application.stage_changes.count() == 2
