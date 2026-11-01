import re

import pytest
from django.contrib.auth.models import Group, User
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils.html import strip_tags
from pytest_django.asserts import assertRedirects

from hiring.models import Application, Candidate, JobOpening
from hiring.permissions import HIRING_MANAGER_GROUP
from hiring.stages import REOPEN


@pytest.fixture
def staff():
    return User.objects.create_user("staff", password="pw")


@pytest.fixture
def staff_client(client, staff):
    client.force_login(staff)
    return client


@pytest.fixture
def manager():
    user = User.objects.create_user("manager", password="pw")
    user.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    return user


@pytest.fixture
def candidate():
    return Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        source=Candidate.Source.WEBSITE,
    )


@pytest.fixture
def job(manager):
    return JobOpening.objects.create(
        title="Backend Engineer",
        department="Engineering",
        location="Austin, TX",
        employment_type=JobOpening.EmploymentType.FULL_TIME,
        description="Build and run our APIs.",
        hiring_manager=manager,
    )


def timeline_entries(response, application):
    """The text of each entry in an application's timeline, in page order."""
    html = response.content.decode()
    match = re.search(
        rf'<ul id="timeline-{application.pk}".*?</ul>', html, flags=re.DOTALL
    )
    assert match, f"No timeline for application {application.pk}"
    items = re.findall(r"<li.*?</li>", match.group(0), flags=re.DOTALL)
    return [" ".join(strip_tags(item).split()) for item in items]


def when(change):
    return date_filter(change.changed_at, "M j, Y, g:i a")


@pytest.mark.django_db
def test_candidate_detail_shows_each_application_timeline_in_order(
    staff_client, staff, manager, candidate, job
):
    application = Application.objects.create_application(candidate, job, staff)
    application.move_to_stage(Application.Stage.INTERVIEW, manager)
    application.move_to_stage(Application.Stage.SCREENING, staff)

    response = staff_client.get(reverse("hiring:candidate_detail", args=[candidate.pk]))

    created, skipped, stepped_back = application.stage_changes.all()
    assert timeline_entries(response, application) == [
        f"→ Applied by staff on {when(created)}",
        f"Applied → Interview by manager on {when(skipped)}",
        f"Interview → Screening by staff on {when(stepped_back)}",
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("page", ["job_detail", "job_board"])
def test_timeline_is_reachable_from_job_side(staff_client, staff, candidate, job, page):
    application = Application.objects.create_application(candidate, job, staff)
    application.move_to_stage(Application.Stage.SCREENING, staff)
    history_url = reverse("hiring:application_detail", args=[application.pk])

    job_page = staff_client.get(reverse(f"hiring:{page}", args=[job.pk]))
    assert f'href="{history_url}"' in job_page.content.decode()

    response = staff_client.get(history_url)
    created, screened = application.stage_changes.all()
    assert timeline_entries(response, application) == [
        f"→ Applied by staff on {when(created)}",
        f"Applied → Screening by staff on {when(screened)}",
    ]


@pytest.mark.django_db
def test_timeline_shows_reopen_and_back_steps_as_entries(
    staff_client, staff, manager, candidate, job
):
    application = Application.objects.create_application(candidate, job, staff)
    application.move_to_stage(Application.Stage.OFFER, staff)
    application.move_to_stage(Application.Stage.HIRED, staff)
    application.move_to_stage(REOPEN, manager)
    application.move_to_stage(Application.Stage.FINAL_REVIEW, staff)
    application.move_to_stage(Application.Stage.REJECTED, staff)

    response = staff_client.get(
        reverse("hiring:application_detail", args=[application.pk])
    )

    changes = list(application.stage_changes.all())
    assert timeline_entries(response, application) == [
        f"→ Applied by staff on {when(changes[0])}",
        f"Applied → Offer by staff on {when(changes[1])}",
        f"Offer → Hired by staff on {when(changes[2])}",
        f"Hired → Offer by manager on {when(changes[3])}",
        f"Offer → Final Review by staff on {when(changes[4])}",
        f"Final Review → Rejected by staff on {when(changes[5])}",
    ]


@pytest.mark.django_db
def test_candidate_detail_shows_a_timeline_per_application(
    staff_client, staff, manager, candidate, job
):
    other_job = JobOpening.objects.create(
        title="Data Analyst",
        department="Analytics",
        location="Remote",
        employment_type=JobOpening.EmploymentType.FULL_TIME,
        description="Answer questions with data.",
        hiring_manager=manager,
    )
    first = Application.objects.create_application(candidate, job, staff)
    second = Application.objects.create_application(candidate, other_job, staff)
    second.move_to_stage(Application.Stage.WITHDRAWN, staff)

    response = staff_client.get(reverse("hiring:candidate_detail", args=[candidate.pk]))

    assert len(timeline_entries(response, first)) == 1
    assert timeline_entries(response, second)[-1].startswith("Applied → Withdrawn")


@pytest.mark.django_db
def test_application_detail_requires_login(client, staff, candidate, job):
    application = Application.objects.create_application(candidate, job, staff)
    url = reverse("hiring:application_detail", args=[application.pk])

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


@pytest.mark.django_db
def test_application_detail_404_for_unknown_application(staff_client):
    response = staff_client.get(reverse("hiring:application_detail", args=[999]))

    assert response.status_code == 404
