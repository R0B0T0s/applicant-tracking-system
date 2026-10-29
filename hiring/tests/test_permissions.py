import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from pytest_django.asserts import assertContains

from hiring.permissions import HIRING_MANAGER_GROUP, is_hiring_manager


@pytest.mark.django_db
def test_is_hiring_manager_only_for_group_members():
    group = Group.objects.get(name=HIRING_MANAGER_GROUP)
    manager = User.objects.create_user("manager", password="pw")
    manager.groups.add(group)
    staff = User.objects.create_user("staff", password="pw")
    admin_only = User.objects.create_user("admin_only", password="pw", is_staff=True)

    assert is_hiring_manager(manager) is True
    assert is_hiring_manager(staff) is False
    assert is_hiring_manager(admin_only) is False


@pytest.mark.django_db
def test_manager_only_view_forbids_staff_and_allows_managers(client):
    url = reverse("hiring:manager_tools")
    staff = User.objects.create_user("staff", password="pw")
    manager = User.objects.create_user("manager", password="pw")
    manager.groups.add(Group.objects.get(name=HIRING_MANAGER_GROUP))

    client.force_login(staff)
    assertContains(client.get(url), "not allowed", status_code=403)

    client.force_login(manager)
    assert client.get(url).status_code == 200
