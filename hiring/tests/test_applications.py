import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from hiring.models import Application, Candidate, JobOpening, StageChange
from hiring.permissions import HIRING_MANAGER_GROUP


@pytest.fixture
def staff():
    return User.objects.create_user("staff", password="pw")


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


@pytest.mark.django_db
def test_new_application_starts_in_applied_with_one_history_entry(
    staff, candidate, job
):
    application = Application.objects.create_application(candidate, job, staff)

    assert application.stage == Application.Stage.APPLIED
    history = list(StageChange.objects.filter(application=application))
    assert len(history) == 1
    assert history[0].from_stage == ""
    assert history[0].to_stage == Application.Stage.APPLIED
    assert history[0].changed_by == staff
    assert history[0].changed_at is not None


@pytest.mark.django_db
@pytest.mark.parametrize("make_ineligible", ["close_job", "archive_candidate"])
def test_application_refused_for_closed_job_or_archived_candidate(
    staff, candidate, job, make_ineligible
):
    if make_ineligible == "close_job":
        job.status = JobOpening.Status.CLOSED
        job.save()
    else:
        candidate.is_archived = True
        candidate.save()

    with pytest.raises(ValidationError):
        Application.objects.create_application(candidate, job, staff)

    assert not Application.objects.exists()
    assert not StageChange.objects.exists()


@pytest.mark.django_db
def test_archiving_candidate_with_active_application_is_refused(
    client, manager, candidate, job
):
    Application.objects.create_application(candidate, job, manager)
    client.force_login(manager)

    response = client.post(reverse("hiring:candidate_archive", args=[candidate.pk]))

    candidate.refresh_from_db()
    assert not candidate.is_archived
    assert candidate.archived_at is None
    assertContains(
        response, "Withdraw or reject their active applications before archiving."
    )


@pytest.fixture
def staff_client(client, staff):
    client.force_login(staff)
    return client


@pytest.fixture
def other_job(manager):
    return JobOpening.objects.create(
        title="Data Analyst",
        department="Analytics",
        location="Remote",
        employment_type=JobOpening.EmploymentType.CONTRACT,
        description="Turn data into decisions.",
        hiring_manager=manager,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name", ["candidate_application_create", "job_application_create"]
)
def test_application_pages_require_login(client, candidate, job, name):
    pk = candidate.pk if name.startswith("candidate") else job.pk
    url = reverse(f"hiring:{name}", args=[pk])

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


@pytest.mark.django_db
def test_staff_can_add_application_from_candidate_page(
    staff_client, staff, candidate, job
):
    response = staff_client.post(
        reverse("hiring:candidate_application_create", args=[candidate.pk]),
        {"job_opening": job.pk},
    )

    assertRedirects(response, candidate.get_absolute_url())
    application = Application.objects.get(candidate=candidate, job_opening=job)
    assert application.stage == Application.Stage.APPLIED
    assert application.stage_changes.get().changed_by == staff


@pytest.mark.django_db
def test_staff_can_add_application_from_job_page(staff_client, staff, candidate, job):
    response = staff_client.post(
        reverse("hiring:job_application_create", args=[job.pk]),
        {"candidate": candidate.pk},
    )

    assertRedirects(response, job.get_absolute_url())
    application = Application.objects.get(candidate=candidate, job_opening=job)
    assert application.stage == Application.Stage.APPLIED
    assert application.stage_changes.get().changed_by == staff


@pytest.mark.django_db
def test_duplicate_application_is_refused_with_form_error(
    staff_client, staff, candidate, job
):
    Application.objects.create_application(candidate, job, staff)

    response = staff_client.post(
        reverse("hiring:job_application_create", args=[job.pk]),
        {"candidate": candidate.pk},
    )

    assertContains(response, "This candidate has already applied to this job opening.")
    assert Application.objects.count() == 1


@pytest.mark.django_db
def test_duplicate_application_is_refused_by_database(staff, candidate, job):
    Application.objects.create_application(candidate, job, staff)

    with pytest.raises(IntegrityError):
        Application.objects.create(candidate=candidate, job_opening=job)


@pytest.mark.django_db
def test_candidate_can_apply_to_several_openings(staff, candidate, job, other_job):
    Application.objects.create_application(candidate, job, staff)
    Application.objects.create_application(candidate, other_job, staff)

    assert candidate.applications.count() == 2


@pytest.mark.django_db
def test_archived_candidate_is_left_out_of_job_page_form_and_refused(
    staff_client, candidate, job
):
    active = Candidate.objects.create(
        first_name="Sam",
        last_name="Active",
        email="sam@example.com",
        source=Candidate.Source.REFERRAL,
    )
    candidate.is_archived = True
    candidate.save()
    url = reverse("hiring:job_application_create", args=[job.pk])

    choices = staff_client.get(url).context["form"].fields["candidate"].queryset
    response = staff_client.post(url, {"candidate": candidate.pk})

    assert list(choices) == [active]
    assert response.context["form"].errors["candidate"]
    assert not Application.objects.exists()


@pytest.mark.django_db
def test_closed_job_is_left_out_of_candidate_page_form_and_refused(
    staff_client, candidate, job, other_job
):
    job.status = JobOpening.Status.CLOSED
    job.save()
    url = reverse("hiring:candidate_application_create", args=[candidate.pk])

    choices = staff_client.get(url).context["form"].fields["job_opening"].queryset
    response = staff_client.post(url, {"job_opening": job.pk})

    assert list(choices) == [other_job]
    assert response.context["form"].errors["job_opening"]
    assert not Application.objects.exists()


@pytest.mark.django_db
def test_detail_pages_list_applications_with_stage(staff_client, staff, candidate, job):
    Application.objects.create_application(candidate, job, staff)

    candidate_page = staff_client.get(candidate.get_absolute_url())
    job_page = staff_client.get(job.get_absolute_url())

    assertContains(candidate_page, "Backend Engineer")
    assertContains(candidate_page, "Applied")
    assertContains(job_page, "Jane Doe")
    assertContains(job_page, "Applied")


@pytest.mark.django_db
def test_archiving_allowed_when_only_final_stage_applications(
    client, manager, candidate, job
):
    application = Application.objects.create_application(candidate, job, manager)
    application.stage = Application.Stage.REJECTED
    application.save()
    client.force_login(manager)

    client.post(reverse("hiring:candidate_archive", args=[candidate.pk]))

    candidate.refresh_from_db()
    assert candidate.is_archived


@pytest.mark.django_db
def test_admin_cannot_delete_candidate_with_applications(
    admin_client, admin_user, candidate, job
):
    Application.objects.create_application(candidate, job, admin_user)

    response = admin_client.post(
        reverse("admin:hiring_candidate_delete", args=[candidate.pk]),
        {"post": "yes"},
    )

    assertContains(response, "Cannot delete candidate")
    assert Candidate.objects.filter(pk=candidate.pk).exists()


@pytest.mark.django_db
def test_database_protects_candidate_with_applications(staff, candidate, job):
    Application.objects.create_application(candidate, job, staff)

    with pytest.raises(ProtectedError):
        candidate.delete()
