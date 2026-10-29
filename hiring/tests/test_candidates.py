import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from hiring.models import Candidate


@pytest.fixture
def staff_client(client):
    client.force_login(User.objects.create_user("staff", password="pw"))
    return client


@pytest.fixture
def candidate():
    return Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        source=Candidate.Source.WEBSITE,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, needs_pk",
    [
        ("candidate_list", False),
        ("candidate_create", False),
        ("candidate_detail", True),
        ("candidate_edit", True),
    ],
)
def test_candidate_pages_require_login(client, candidate, name, needs_pk):
    url = reverse(f"hiring:{name}", args=[candidate.pk] if needs_pk else [])

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


@pytest.mark.django_db
def test_candidate_pages_render_for_staff(staff_client, candidate):
    pages = [
        (reverse("hiring:candidate_list"), "Jane Doe"),
        (reverse("hiring:candidate_create"), "New candidate"),
        (
            reverse("hiring:candidate_detail", args=[candidate.pk]),
            "jane.doe@example.com",
        ),
        (reverse("hiring:candidate_edit", args=[candidate.pk]), "Edit Jane Doe"),
    ]

    for url, text in pages:
        assertContains(staff_client.get(url), text)


@pytest.mark.django_db
def test_staff_can_create_candidate_and_see_it_on_detail_page(staff_client):
    response = staff_client.post(
        reverse("hiring:candidate_create"),
        {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "phone": "555-0100",
            "url": "https://example.com/ada",
            "location": "London",
            "source": Candidate.Source.REFERRAL,
            "source_details": "Referred by Charles Babbage",
            "notes": "Strong analytical background.",
        },
        follow=True,
    )

    created = Candidate.objects.get(email="ada@example.com")
    assertRedirects(response, created.get_absolute_url())
    for text in [
        "Ada Lovelace",
        "555-0100",
        "London",
        "Referral",
        "Referred by Charles Babbage",
        "Strong analytical background.",
    ]:
        assertContains(response, text)


@pytest.mark.django_db
def test_candidate_create_requires_names_email_and_source(staff_client):
    response = staff_client.post(reverse("hiring:candidate_create"), {})

    assert set(response.context["form"].errors) == {
        "first_name",
        "last_name",
        "email",
        "source",
    }
    assert not Candidate.objects.exists()


@pytest.mark.django_db
def test_staff_can_edit_candidate(staff_client, candidate):
    url = reverse("hiring:candidate_edit", args=[candidate.pk])

    response = staff_client.post(
        url,
        {
            "first_name": "Janet",
            "last_name": "Doe",
            "email": candidate.email,
            "source": Candidate.Source.JOB_BOARD,
            "source_details": "Indeed",
        },
    )

    assertRedirects(response, candidate.get_absolute_url())
    candidate.refresh_from_db()
    assert candidate.first_name == "Janet"
    assert candidate.source == Candidate.Source.JOB_BOARD
    assert candidate.source_details == "Indeed"


@pytest.mark.django_db
def test_editing_cannot_take_another_candidates_email(staff_client, candidate):
    other = Candidate.objects.create(
        first_name="Other",
        last_name="Person",
        email="other@example.com",
        source=Candidate.Source.OTHER,
    )

    response = staff_client.post(
        reverse("hiring:candidate_edit", args=[other.pk]),
        {
            "first_name": "Other",
            "last_name": "Person",
            "email": "Jane.Doe@example.com",
            "source": Candidate.Source.OTHER,
        },
    )

    assertContains(response, "A candidate with this email already exists.")
    other.refresh_from_db()
    assert other.email == "other@example.com"


@pytest.mark.django_db
def test_email_is_stored_lowercase():
    candidate = Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="Jane.Doe@Example.COM",
        source=Candidate.Source.WEBSITE,
    )

    candidate.refresh_from_db()
    assert candidate.email == "jane.doe@example.com"


@pytest.mark.django_db
def test_duplicate_email_in_different_case_is_refused_with_form_error(client):
    Candidate.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        source=Candidate.Source.WEBSITE,
    )
    client.force_login(User.objects.create_user("staff", password="pw"))
    client.raise_request_exception = False

    response = client.post(
        reverse("hiring:candidate_create"),
        {
            "first_name": "Janet",
            "last_name": "Doe",
            "email": "JANE.DOE@Example.com",
            "source": Candidate.Source.REFERRAL,
        },
    )

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert Candidate.objects.count() == 1


@pytest.mark.django_db
def test_candidate_search_matches_name_and_email(client):
    def make(first, last, email):
        return Candidate.objects.create(
            first_name=first,
            last_name=last,
            email=email,
            source=Candidate.Source.WEBSITE,
        )

    ada = make("Ada", "Lovelace", "ada@example.com")
    alan = make("Alan", "Turing", "alan@bletchley.org")
    grace = make("Grace", "Hopper", "grace@navy.mil")
    client.force_login(User.objects.create_user("staff", password="pw"))

    def search(q):
        response = client.get(reverse("hiring:candidate_list"), {"q": q})
        return set(response.context["candidates"])

    assert search("ada") == {ada}
    assert search("TURING") == {alan}
    assert search("navy.mil") == {grace}
    assert search("a") == {ada, alan, grace}
    assert search("nobody") == set()
