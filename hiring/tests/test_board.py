import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertTemplateNotUsed,
    assertTemplateUsed,
)

from hiring.models import Application, Candidate, JobOpening
from hiring.permissions import HIRING_MANAGER_GROUP


@pytest.fixture
def staff():
    return User.objects.create_user("staff", password="pw")


@pytest.fixture
def staff_client(client, staff):
    client.force_login(staff)
    return client


@pytest.fixture
def job():
    manager = User.objects.create_user("manager", password="pw")
    manager.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    return JobOpening.objects.create(
        title="Backend Engineer",
        department="Engineering",
        location="Austin, TX",
        employment_type=JobOpening.EmploymentType.FULL_TIME,
        description="Build and run our APIs.",
        hiring_manager=manager,
    )


@pytest.fixture
def application(staff, job):
    candidate = Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        source=Candidate.Source.WEBSITE,
    )
    return Application.objects.create_application(candidate, job, staff)


@pytest.mark.django_db
def test_tampered_illegal_move_returns_board_with_inline_error(
    staff_client, application
):
    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"stage": Application.Stage.HIRED},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "hiring/_board.html")
    assertContains(response, "Can&#x27;t move from Applied to Hired.")
    card = response.context["active_columns"][0][1][0]
    assert card.pk == application.pk
    assert card.error == "Can't move from Applied to Hired."
    application.refresh_from_db()
    assert application.stage == Application.Stage.APPLIED
    assert application.stage_changes.count() == 1


def _card_names(column):
    return [str(application.candidate) for application in column[1]]


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["job_board", "application_move"])
def test_board_endpoints_require_login(client, application, name):
    pk = application.job_opening.pk if name == "job_board" else application.pk
    url = reverse(f"hiring:{name}", args=[pk])

    response = client.post(url) if name == "application_move" else client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_board_places_applicants_in_their_stage_columns(
    staff_client, staff, job, application
):
    rejected = Application.objects.create_application(
        Candidate.objects.create(
            first_name="Sam",
            last_name="Smith",
            email="sam@example.com",
            source=Candidate.Source.REFERRAL,
        ),
        job,
        staff,
    )
    rejected.move_to_stage(Application.Stage.REJECTED, staff)

    response = staff_client.get(reverse("hiring:job_board", args=[job.pk]))

    active = response.context["active_columns"]
    final = response.context["final_columns"]
    assert [label for label, _ in active] == [
        "Applied",
        "Screening",
        "Interview",
        "Final Review",
        "Offer",
    ]
    assert [label for label, _ in final] == ["Hired", "Rejected", "Withdrawn"]
    assert _card_names(active[0]) == ["Jane Doe"]
    assert _card_names(final[1]) == ["Sam Smith"]
    assertContains(response, "Final stages")


@pytest.mark.django_db
def test_dropdown_lists_only_allowed_moves(staff_client, staff, job, application):
    application.move_to_stage(Application.Stage.OFFER, staff)

    response = staff_client.get(reverse("hiring:job_board", args=[job.pk]))

    card = response.context["active_columns"][4][1][0]
    assert [value for value, _ in card.moves] == [
        "final_review",
        "hired",
        "rejected",
        "withdrawn",
    ]
    assertContains(response, '<option value="hired">Hired</option>', html=True)
    assertContains(response, '<option value="applied">Applied</option>', count=0)


@pytest.mark.django_db
def test_final_stage_card_has_no_dropdown(staff_client, staff, job, application):
    application.move_to_stage(Application.Stage.WITHDRAWN, staff)

    response = staff_client.get(reverse("hiring:job_board", args=[job.pk]))

    assert response.context["final_columns"][2][1][0].moves == []
    assertContains(response, 'name="stage"', count=0)


@pytest.mark.django_db
def test_legal_move_returns_updated_board_fragment(staff_client, staff, application):
    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"stage": Application.Stage.INTERVIEW},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "hiring/_board.html")
    assertTemplateNotUsed(response, "base.html")
    assert _card_names(response.context["active_columns"][2]) == ["Jane Doe"]
    assert _card_names(response.context["active_columns"][0]) == []
    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW
    latest = application.stage_changes.last()
    assert (latest.from_stage, latest.to_stage, latest.changed_by) == (
        Application.Stage.APPLIED,
        Application.Stage.INTERVIEW,
        staff,
    )


@pytest.mark.django_db
def test_move_endpoint_rejects_get(staff_client, application):
    response = staff_client.get(
        reverse("hiring:application_move", args=[application.pk])
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_job_detail_links_to_board(staff_client, job):
    response = staff_client.get(job.get_absolute_url())

    assertContains(response, reverse("hiring:job_board", args=[job.pk]))
