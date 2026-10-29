import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from hiring.permissions import HIRING_MANAGER_GROUP


@pytest.mark.django_db
def test_anonymous_user_is_redirected_to_login(client):
    home = reverse("hiring:home")

    response = client.get(home)

    assertRedirects(response, f"{reverse('login')}?next={home}")


@pytest.mark.django_db
def test_hiring_manager_group_exists_after_migrate():
    assert Group.objects.filter(name=HIRING_MANAGER_GROUP).exists()
