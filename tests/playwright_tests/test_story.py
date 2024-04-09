import re

import pytest
from django import forms, views
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.urls import include, path, reverse
from playwright.sync_api import expect

from mizdb_watchlist.manager import get_manager
from mizdb_watchlist.views import WatchlistMixin, WatchlistViewMixin
from tests.factories import PersonFactory
from tests.testapp.models import Person


def dummy_view(*_args):
    return HttpResponse("This is a dummy view for tests")


class Changelist(WatchlistMixin, views.generic.ListView):
    queryset = Person.objects.all()
    template_name = "changelist.html"


class EditView(views.generic.UpdateView):
    model = Person
    fields = forms.ALL_FIELDS
    template_name = "edit.html"


class WatchlistView(WatchlistViewMixin, views.generic.TemplateView):
    template_name = "watchlist.html"


class URLconf:
    app_name = "test"
    urlpatterns = [
        path("person/", Changelist.as_view(), name="testapp_person_changelist"),
        path("person/<int:pk>/edit/", EditView.as_view(), name="testapp_person_change"),
        path("company/", dummy_view, name="testapp_company_changelist"),
        path("company/<int:pk>/edit/", dummy_view, name="testapp_company_change"),
        path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    ]


urlpatterns = [
    path("", include(URLconf)),
    path("mizdb_watchlist/", include("mizdb_watchlist.urls")),
]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__), pytest.mark.pw]


@pytest.fixture
def edit_url(live_server):
    def inner(pk):
        return live_server.url + reverse("test:testapp_person_change", args=[pk])

    return inner


@pytest.fixture(autouse=True)
def test_data(person_model):
    objects = []
    for _ in range(20):
        objects.append(PersonFactory.build())
    person_model.objects.bulk_create(objects)


def get_changelist_items(locator):
    return locator.locator(".changelist-item")


def get_watchlist_items(locator):
    return locator.locator(".watchlist-item")


def get_person_watchlist(locator):
    return locator.locator("#Person-watchlist")


def get_person_watchlist_items(locator):
    return get_watchlist_items(get_person_watchlist(locator))


def get_object_id(button):
    return button.get_attribute("data-object-id")


def get_changelist_link(locator):
    """Return the changelist link of the model watchlist."""
    return locator.locator(".watchlist-changelist-btn")


@pytest.fixture
def add_company(rf, user, get_session_cookie, company, logged_in):
    """Add a Company object to the watchlist."""

    # This is a 'factory fixture' because it needs to be called after the page
    # was loaded and the session cookie was set.
    def inner():
        request = rf.get("")
        if logged_in:
            request.user = user
        request.session = SessionStore(session_key=get_session_cookie()["value"])
        get_manager(request).add(company)
        # Need to explicitly call save():
        # (despite manager.add setting session.modified to true)
        request.session.save()

    return inner


@pytest.fixture
def changelist_url(get_url):
    return get_url("test:testapp_person_changelist")


@pytest.mark.parametrize("logged_in", [True, False])
def test_story(
    request,
    page,
    changelist_url,
    edit_url,
    get_toggle_button,
    get_remove_button,
    get_watchlist_link,
    assert_toggled_on,
    assert_toggled_off,
    person_model,
    on_watchlist,
    logged_in,
    add_company,
):
    if logged_in:
        request.getfixturevalue("session_login")
    # Toggle a few items on the changelist:
    page.goto(changelist_url)
    # Add a company to the watchlist:
    add_company()

    added_ids = []

    toggle_button = get_toggle_button(get_changelist_items(page).nth(5))
    toggle_button.click()
    added = person_model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    toggle_button = get_toggle_button(get_changelist_items(page).nth(9))
    toggle_button.click()
    added = person_model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    toggle_button = get_toggle_button(get_changelist_items(page).nth(13))
    toggle_button.click()
    added = person_model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    toggle_button = get_toggle_button(get_changelist_items(page).nth(17))
    toggle_button.click()
    added = person_model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    # Go to the watchlist and confirm that the items have been added:
    get_watchlist_link(page).click()
    watchlist_items = get_person_watchlist_items(page)
    expect(watchlist_items).to_have_count(4)
    watchlist_object_ids = [
        int(get_object_id(get_remove_button(watchlist_item)))
        for watchlist_item in get_person_watchlist_items(page).all()
    ]
    assert sorted(watchlist_object_ids) == sorted(added_ids)

    # Remove a watchlist item by clicking the remove button:
    remove_button = get_remove_button(watchlist_items.first)
    removed = person_model.objects.get(pk=get_object_id(remove_button))
    remove_button.click()
    watchlist_items = get_person_watchlist_items(page)
    expect(watchlist_items).to_have_count(3)
    assert not on_watchlist(removed)

    # Go to the edit page of a watchlist item and use the toggle button there:
    pk = get_object_id(watchlist_items.first.locator("button"))
    page.goto(edit_url(pk))
    removed = person_model.objects.get(pk=pk)
    toggle_button = get_toggle_button(page)
    assert_toggled_on(toggle_button)
    toggle_button.click()
    assert_toggled_off(toggle_button)
    assert not on_watchlist(removed)

    # Go back to the watchlist, use the changelist button there to go back to
    # a changelist filtered to only show the watchlist items:
    get_watchlist_link(page).click()
    get_changelist_link(get_person_watchlist(page)).click()
    expect(get_changelist_items(page)).to_have_count(2)
    expect(page.locator(".on-watchlist")).to_have_count(2)

    # Go to the watchlist again, and use the 'remove all' button:
    get_watchlist_link(page).click()
    watchlist_items = get_person_watchlist_items(page)
    expect(watchlist_items).to_have_count(2)
    get_person_watchlist(page).get_by_text(re.compile("remove all", re.IGNORECASE)).click()
    # Reload the watchlist:
    get_watchlist_link(page).click()
    expect(watchlist_items).to_have_count(0)

    # The company should still be listed:
    expect(page.locator("#Company-watchlist")).to_be_attached()
