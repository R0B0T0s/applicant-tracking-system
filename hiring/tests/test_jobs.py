import pytest
from django.contrib.auth.models import Group, User
from django.db.models import ProtectedError
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from hiring.models import JobOpening
from hiring.permissions import HIRING_MANAGER_GROUP


@pytest.fixture
def staff_client(client):
    client.force_login(User.objects.create_user("staff", password="pw"))
    return client


@pytest.fixture
def manager():
    user = User.objects.create_user("manager", password="pw")
    user.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    return user


@pytest.fixture
def job_data(manager):
    return {
        "title": "Backend Engineer",
        "department": "Engineering",
        "location": "Austin, TX",
        "employment_type": JobOpening.EmploymentType.FULL_TIME,
        "hiring_manager": manager.pk,
        "number_of_positions": 2,
        "salary_min": 90000,
        "salary_max": 120000,
        "description": "Build and run our APIs.",
    }


@pytest.mark.django_db
def test_salary_min_greater_than_max_is_rejected_with_form_error(
    staff_client, job_data
):
    url = reverse("hiring:job_create")

    response = staff_client.post(
        url, {**job_data, "salary_min": 130000, "salary_max": 120000}
    )

    assert response.status_code == 200
    assert "salary_min" in response.context["form"].errors
    assert not JobOpening.objects.exists()

    # Equal bounds, or only one bound given, are fine.
    for salary in [
        {"salary_min": 100000, "salary_max": 100000},
        {"salary_min": 100000, "salary_max": ""},
        {"salary_min": "", "salary_max": 100000},
    ]:
        response = staff_client.post(url, {**job_data, **salary})
        assert response.status_code == 302, salary
    assert JobOpening.objects.count() == 3


@pytest.mark.django_db
def test_hiring_manager_choices_are_group_members_and_non_members_are_rejected(
    staff_client, manager, job_data
):
    non_member = User.objects.create_user("regular", password="pw")
    admin_only = User.objects.create_user("admin_only", password="pw", is_staff=True)
    url = reverse("hiring:job_create")

    choices = set(
        staff_client.get(url).context["form"].fields["hiring_manager"].queryset
    )
    assert choices == {manager}

    # Tampered POSTs naming a non-member are refused by validation.
    for user in [non_member, admin_only]:
        response = staff_client.post(url, {**job_data, "hiring_manager": user.pk})
        assert response.status_code == 200
        assert "hiring_manager" in response.context["form"].errors
    assert not JobOpening.objects.exists()

    # The field is required.
    response = staff_client.post(url, {**job_data, "hiring_manager": ""})
    assert "hiring_manager" in response.context["form"].errors


@pytest.fixture
def job(manager):
    return JobOpening.objects.create(
        title="Data Analyst",
        department="Finance",
        location="Remote",
        employment_type=JobOpening.EmploymentType.CONTRACT,
        description="Analyze numbers.",
        hiring_manager=manager,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, needs_pk",
    [
        ("job_list", False),
        ("job_create", False),
        ("job_detail", True),
        ("job_edit", True),
    ],
)
def test_job_pages_require_login(client, job, name, needs_pk):
    url = reverse(f"hiring:{name}", args=[job.pk] if needs_pk else [])

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


@pytest.mark.django_db
def test_job_pages_render_for_staff(staff_client, job):
    pages = [
        (reverse("hiring:job_list"), "Data Analyst"),
        (reverse("hiring:job_create"), "New job opening"),
        (reverse("hiring:job_detail", args=[job.pk]), "Analyze numbers."),
        (reverse("hiring:job_edit", args=[job.pk]), "Edit Data Analyst"),
    ]

    for url, text in pages:
        assertContains(staff_client.get(url), text)


@pytest.mark.django_db
def test_staff_can_create_job_and_see_it_on_detail_page(staff_client, job_data):
    response = staff_client.post(reverse("hiring:job_create"), job_data, follow=True)

    created = JobOpening.objects.get(title="Backend Engineer")
    assertRedirects(response, created.get_absolute_url())
    assert created.status == JobOpening.Status.OPEN
    assert created.closed_at is None
    for text in [
        "Backend Engineer",
        "Engineering",
        "Austin, TX",
        "Full-time",
        "manager",
        "$90,000 – $120,000",
        "Build and run our APIs.",
        "Open",
    ]:
        assertContains(response, text)


@pytest.mark.django_db
def test_job_create_requires_core_fields(staff_client):
    response = staff_client.post(reverse("hiring:job_create"), {})

    assert set(response.context["form"].errors) == {
        "title",
        "department",
        "location",
        "employment_type",
        "hiring_manager",
        "number_of_positions",
        "description",
    }


@pytest.mark.django_db
def test_number_of_positions_defaults_to_one_and_must_be_positive(
    staff_client, job_data
):
    url = reverse("hiring:job_create")
    assert staff_client.get(url).context["form"]["number_of_positions"].value() == 1

    response = staff_client.post(url, {**job_data, "number_of_positions": 0})

    assert "number_of_positions" in response.context["form"].errors
    assert not JobOpening.objects.exists()


@pytest.mark.django_db
def test_staff_can_edit_job(staff_client, job, job_data):
    response = staff_client.post(
        reverse("hiring:job_edit", args=[job.pk]),
        {**job_data, "title": "Senior Data Analyst"},
    )

    assertRedirects(response, job.get_absolute_url())
    job.refresh_from_db()
    assert job.title == "Senior Data Analyst"
    assert job.number_of_positions == 2


@pytest.mark.django_db
def test_edit_form_has_no_status_field_and_ignores_tampered_status(
    staff_client, job, job_data
):
    url = reverse("hiring:job_edit", args=[job.pk])

    response = staff_client.get(url)
    assert "status" not in response.context["form"].fields
    assert 'name="status"' not in response.content.decode()

    staff_client.post(url, {**job_data, "status": JobOpening.Status.CLOSED})
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN


@pytest.mark.django_db
def test_deleting_a_user_who_is_hiring_manager_fails(manager, job):
    with pytest.raises(ProtectedError):
        manager.delete()

    assert User.objects.filter(pk=manager.pk).exists()


@pytest.mark.django_db
def test_job_search_matches_title_department_and_location(staff_client, manager):
    def make(title, department, location):
        return JobOpening.objects.create(
            title=title,
            department=department,
            location=location,
            employment_type=JobOpening.EmploymentType.FULL_TIME,
            description="-",
            hiring_manager=manager,
        )

    engineer = make("Backend Engineer", "Engineering", "Austin, TX")
    analyst = make("Data Analyst", "Finance", "Remote")
    designer = make("Product Designer", "Design", "Denver, CO")

    def search(q):
        response = staff_client.get(reverse("hiring:job_list"), {"q": q})
        return set(response.context["jobs"])

    assert search("engineer") == {engineer}
    assert search("FINANCE") == {analyst}
    assert search("denver") == {designer}
    assert search("e") == {engineer, analyst, designer}
    assert search("nothing") == set()
