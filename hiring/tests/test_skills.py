import pytest
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from hiring.models import JobOpening, Skill
from hiring.permissions import HIRING_MANAGER_GROUP


@pytest.fixture
def manager():
    user = User.objects.create_user("manager", password="pw")
    user.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))
    return user


@pytest.fixture
def manager_client(client, manager):
    client.force_login(manager)
    return client


@pytest.fixture
def staff_client(client):
    client.force_login(User.objects.create_user("staff", password="pw"))
    return client


@pytest.fixture
def skill():
    return Skill.objects.create(name="Python")


def skill_urls(skill):
    return [
        reverse("hiring:skill_list"),
        reverse("hiring:skill_create"),
        reverse("hiring:skill_edit", args=[skill.pk]),
        reverse("hiring:skill_delete", args=[skill.pk]),
    ]


@pytest.mark.django_db
def test_skill_names_are_trimmed_and_unique_regardless_of_case():
    Skill.objects.create(name="Python")

    django = Skill.objects.create(name="  Django ")
    django.refresh_from_db()
    assert django.name == "Django"

    with pytest.raises(IntegrityError):
        Skill.objects.create(name=" python ")


@pytest.mark.django_db
def test_adding_a_duplicate_skill_name_shows_a_form_error(manager_client):
    Skill.objects.create(name="Python")

    response = manager_client.post(reverse("hiring:skill_create"), {"name": " python "})

    assert response.status_code == 200
    assert response.context["form"].errors == {
        "name": ["A skill with this name already exists."]
    }
    assert Skill.objects.count() == 1


@pytest.mark.django_db
def test_skill_pages_require_login(client, skill):
    for url in skill_urls(skill):
        assertRedirects(client.get(url), f"{reverse('login')}?next={url}")


@pytest.mark.django_db
def test_staff_get_403_on_skill_pages(staff_client, skill):
    for url in skill_urls(skill):
        assert staff_client.get(url).status_code == 403, url
        assert staff_client.post(url, {"name": "Go"}).status_code == 403, url

    assert list(Skill.objects.values_list("name", flat=True)) == ["Python"]


@pytest.mark.django_db
def test_skills_nav_link_is_shown_only_to_managers(client, manager):
    url = reverse("hiring:skill_list")
    client.force_login(User.objects.create_user("staff", password="pw"))
    assertNotContains(client.get(reverse("hiring:home")), f'href="{url}"')

    client.force_login(manager)
    assertContains(client.get(reverse("hiring:home")), f'href="{url}"')


@pytest.mark.django_db
def test_manager_can_add_rename_and_delete_skills(manager_client):
    response = manager_client.post(reverse("hiring:skill_create"), {"name": " SQL "})
    assertRedirects(response, reverse("hiring:skill_list"))
    skill = Skill.objects.get()
    assert skill.name == "SQL"
    assertContains(manager_client.get(reverse("hiring:skill_list")), "SQL")

    response = manager_client.post(
        reverse("hiring:skill_edit", args=[skill.pk]), {"name": "PostgreSQL"}
    )
    assertRedirects(response, reverse("hiring:skill_list"))
    skill.refresh_from_db()
    assert skill.name == "PostgreSQL"

    # The delete page asks for confirmation before deleting.
    delete_url = reverse("hiring:skill_delete", args=[skill.pk])
    assertContains(manager_client.get(delete_url), "Delete PostgreSQL?")
    assert Skill.objects.exists()

    assertRedirects(manager_client.post(delete_url), reverse("hiring:skill_list"))
    assert not Skill.objects.exists()


@pytest.mark.django_db
def test_renaming_a_skill_checks_duplicates_but_allows_a_case_change(
    manager_client, skill
):
    sql = Skill.objects.create(name="SQL")
    url = reverse("hiring:skill_edit", args=[sql.pk])

    response = manager_client.post(url, {"name": "PYTHON"})
    assert "name" in response.context["form"].errors
    sql.refresh_from_db()
    assert sql.name == "SQL"

    assertRedirects(
        manager_client.post(url, {"name": "sql"}), reverse("hiring:skill_list")
    )
    sql.refresh_from_db()
    assert sql.name == "sql"


@pytest.mark.django_db
def test_skill_name_is_required(manager_client):
    response = manager_client.post(reverse("hiring:skill_create"), {"name": "   "})

    assert "name" in response.context["form"].errors
    assert not Skill.objects.exists()


@pytest.fixture
def job_data(manager):
    return {
        "title": "Backend Engineer",
        "department": "Engineering",
        "location": "Austin, TX",
        "employment_type": JobOpening.EmploymentType.FULL_TIME,
        "hiring_manager": manager.pk,
        "number_of_positions": 1,
        "description": "Build and run our APIs.",
    }


@pytest.mark.django_db
def test_staff_can_attach_several_skills_to_a_job_and_see_them(
    staff_client, skill, job_data
):
    django = Skill.objects.create(name="Django")
    Skill.objects.create(name="Unused Skill")

    form = staff_client.get(reverse("hiring:job_create")).context["form"]
    assert set(form.fields["skills"].queryset) == set(Skill.objects.all())

    response = staff_client.post(
        reverse("hiring:job_create"),
        {**job_data, "skills": [skill.pk, django.pk]},
        follow=True,
    )

    job = JobOpening.objects.get()
    assert set(job.skills.all()) == {skill, django}
    assertContains(response, "Python")
    assertContains(response, "Django")
    assertNotContains(response, "Unused Skill")


@pytest.mark.django_db
def test_skills_are_optional_and_editable_on_a_job(staff_client, skill, job_data):
    staff_client.post(reverse("hiring:job_create"), job_data)
    job = JobOpening.objects.get()
    assert not job.skills.exists()

    staff_client.post(
        reverse("hiring:job_edit", args=[job.pk]), {**job_data, "skills": [skill.pk]}
    )
    assert list(job.skills.all()) == [skill]

    staff_client.post(reverse("hiring:job_edit", args=[job.pk]), job_data)
    assert not job.skills.exists()


@pytest.mark.django_db
def test_one_skill_can_be_used_on_many_openings(staff_client, skill, job_data):
    for title in ["Backend Engineer", "Data Engineer"]:
        staff_client.post(
            reverse("hiring:job_create"),
            {**job_data, "title": title, "skills": [skill.pk]},
        )

    assert set(skill.job_openings.values_list("title", flat=True)) == {
        "Backend Engineer",
        "Data Engineer",
    }
    assertContains(
        staff_client.get(
            reverse("hiring:job_edit", args=[JobOpening.objects.first().pk])
        ),
        f'value="{skill.pk}" class="checkbox checkbox-sm" checked',
    )


@pytest.mark.django_db
def test_deleting_a_skill_removes_it_from_openings_but_keeps_them(
    manager_client, skill, job_data
):
    manager_client.post(
        reverse("hiring:job_create"), {**job_data, "skills": [skill.pk]}
    )
    url = reverse("hiring:skill_delete", args=[skill.pk])
    assertContains(manager_client.get(url), "used on 1 job opening")

    manager_client.post(url)

    job = JobOpening.objects.get()
    assert not job.skills.exists()
