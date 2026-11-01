import itertools

import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from hiring.models import Application, Candidate, JobOpening
from hiring.permissions import HIRING_MANAGER_GROUP


@pytest.fixture
def manager():
    user = User.objects.create_user("manager", password="pw")
    user.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    return user


@pytest.fixture
def staff_client(client):
    client.force_login(User.objects.create_user("staff", password="pw"))
    return client


@pytest.fixture
def manager_client(client, manager):
    client.force_login(manager)
    return client


@pytest.fixture
def job(manager):
    return JobOpening.objects.create(
        title="Backend Engineer",
        department="Engineering",
        location="Austin, TX",
        employment_type=JobOpening.EmploymentType.FULL_TIME,
        description="Build and run our APIs.",
        hiring_manager=manager,
        number_of_positions=2,
    )


@pytest.fixture
def apply(manager, job):
    """Create an application for a new candidate and put it in `stage`."""
    numbers = itertools.count(1)

    def make(stage):
        n = next(numbers)
        candidate = Candidate.objects.create(
            first_name="Candidate",
            last_name=str(n),
            email=f"candidate{n}@example.com",
            source=Candidate.Source.WEBSITE,
        )
        application = Application.objects.create_application(candidate, job, manager)
        Application.objects.filter(pk=application.pk).update(stage=stage)
        return application

    return make


@pytest.fixture
def closed_job(job):
    job.close()
    return job


@pytest.mark.django_db
def test_manager_close_sets_closed_at_and_reopen_clears_it(manager_client, job):
    response = manager_client.post(reverse("hiring:job_close", args=[job.pk]))

    assertRedirects(response, job.get_absolute_url())
    job.refresh_from_db()
    assert job.status == JobOpening.Status.CLOSED
    assert job.closed_at is not None

    response = manager_client.post(reverse("hiring:job_reopen", args=[job.pk]))

    assertRedirects(response, job.get_absolute_url())
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN
    assert job.closed_at is None


@pytest.mark.django_db
def test_close_confirmation_counts_only_active_applications(manager_client, job, apply):
    for stage in [
        Application.Stage.APPLIED,
        Application.Stage.INTERVIEW,
        Application.Stage.OFFER,
        Application.Stage.HIRED,
        Application.Stage.REJECTED,
        Application.Stage.WITHDRAWN,
    ]:
        apply(stage)

    response = manager_client.get(reverse("hiring:job_close", args=[job.pk]))

    assert response.context["active_count"] == 3
    assertContains(response, "still has 3 active applications")


@pytest.mark.django_db
def test_job_page_shows_positions_filled_counting_only_hired(
    manager_client, job, apply
):
    for stage in [
        Application.Stage.HIRED,
        Application.Stage.OFFER,
        Application.Stage.REJECTED,
        Application.Stage.WITHDRAWN,
    ]:
        apply(stage)

    response = manager_client.get(job.get_absolute_url())

    assertContains(response, "1 of 2 positions filled")


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["job_close", "job_reopen"])
def test_close_and_reopen_require_login(client, job, name):
    url = reverse(f"hiring:{name}", args=[job.pk])

    assertRedirects(client.get(url), f"{reverse('login')}?next={url}")


@pytest.mark.django_db
def test_staff_get_403_on_close_and_reopen(staff_client, job):
    close_url = reverse("hiring:job_close", args=[job.pk])
    assertContains(staff_client.get(close_url), "not allowed", status_code=403)
    assert staff_client.post(close_url).status_code == 403
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN

    job.close()
    reopen_url = reverse("hiring:job_reopen", args=[job.pk])
    assertContains(staff_client.get(reopen_url), "not allowed", status_code=403)
    assert staff_client.post(reopen_url).status_code == 403
    job.refresh_from_db()
    assert job.status == JobOpening.Status.CLOSED


@pytest.mark.django_db
def test_closing_does_not_change_applications(manager_client, job, apply):
    application = apply(Application.Stage.INTERVIEW)

    manager_client.post(reverse("hiring:job_close", args=[job.pk]))

    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW
    assert application.stage_changes.count() == 1


@pytest.mark.django_db
def test_close_and_reopen_buttons_shown_only_to_managers(client, manager, job):
    close_url = reverse("hiring:job_close", args=[job.pk])
    reopen_url = reverse("hiring:job_reopen", args=[job.pk])

    client.force_login(manager)
    response = client.get(job.get_absolute_url())
    assertContains(response, close_url)
    assertNotContains(response, reopen_url)

    job.close()
    response = client.get(job.get_absolute_url())
    assertContains(response, reopen_url)
    assertNotContains(response, close_url)

    client.force_login(User.objects.create_user("staff", password="pw"))
    response = client.get(job.get_absolute_url())
    assertNotContains(response, reopen_url)
    assertNotContains(response, close_url)


@pytest.mark.django_db
def test_closed_job_page_and_board_show_closed_marker(staff_client, closed_job):
    detail = staff_client.get(closed_job.get_absolute_url())
    board = staff_client.get(reverse("hiring:job_board", args=[closed_job.pk]))

    for response in [detail, board]:
        assertContains(response, "<strong>Closed</strong>", html=False)
    assertNotContains(
        detail, reverse("hiring:job_application_create", args=[closed_job.pk])
    )


@pytest.mark.django_db
def test_open_job_page_has_no_closed_marker(staff_client, job):
    response = staff_client.get(job.get_absolute_url())

    assertNotContains(response, "<strong>Closed</strong>", html=False)


@pytest.mark.django_db
def test_job_page_application_form_refuses_closed_job(staff_client, closed_job):
    candidate = Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        source=Candidate.Source.WEBSITE,
    )

    response = staff_client.post(
        reverse("hiring:job_application_create", args=[closed_job.pk]),
        {"candidate": candidate.pk},
    )

    assertContains(response, "This job opening is closed")
    assert not Application.objects.exists()


@pytest.mark.django_db
def test_board_moves_on_closed_job_still_work_including_to_hired(
    staff_client, job, apply
):
    application = apply(Application.Stage.OFFER)
    job.close()

    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"stage": Application.Stage.HIRED},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Application.Stage.HIRED
    hired = dict(response.context["final_columns"])["Hired"]
    assert [a.pk for a in hired] == [application.pk]
    assertContains(staff_client.get(job.get_absolute_url()), "1 of 2 positions filled")
