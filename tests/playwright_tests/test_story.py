import pytest
from django.urls import include, path, reverse, reverse_lazy

from tests.factories import PersonFactory
from tests.testapp.views import Changelist, EditView, WatchlistView

urlpatterns = [
    path("", Changelist.as_view(), name="changelist"),
    path("edit/<int:pk>/", EditView.as_view(success_url=reverse_lazy("changelist")), name="testapp_person_change"),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("mizdb_watchlist/", include("mizdb_watchlist.urls")),
]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__), pytest.mark.pw]


@pytest.fixture
def edit_url(live_server):
    def inner(pk):
        return live_server.url + reverse("testapp_person_change", args=[pk])

    return inner


@pytest.fixture(autouse=True)
def test_data(model):
    objects = []
    for _ in range(20):
        objects.append(PersonFactory.build())
    model.objects.bulk_create(objects)


def get_changelist_items(page):
    return page.locator(".changelist-item")


def get_watchlist_items(page):
    return page.locator("#watchlist li")


def get_object_id(button):
    return button.get_attribute("data-object-id")


@pytest.mark.parametrize("logged_in", [True, False])
def test_story(
    request,
    page,
    get_url,
    edit_url,
    get_toggle_button,
    get_remove_button,
    assert_toggled_on,
    assert_toggled_off,
    model,
    on_watchlist,
    logged_in,
):
    if logged_in:
        request.getfixturevalue("session_login")

    # Toggle a few items on the changelist:
    page.goto(get_url("changelist"))
    added_ids = []

    toggle_button = get_toggle_button(get_changelist_items(page).nth(5))
    toggle_button.click()
    added = model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    toggle_button = get_toggle_button(get_changelist_items(page).nth(9))
    toggle_button.click()
    added = model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    toggle_button = get_toggle_button(get_changelist_items(page).nth(13))
    toggle_button.click()
    added = model.objects.get(pk=get_object_id(toggle_button))
    assert_toggled_on(toggle_button)
    assert on_watchlist(added)
    added_ids.append(added.pk)

    # Go to the watchlist and confirm that the items have been added:
    page.goto(get_url("watchlist"))
    watchlist_items = get_watchlist_items(page)
    assert watchlist_items.count() == 3
    watchlist_object_ids = [
        int(get_object_id(get_remove_button(watchlist_item))) for watchlist_item in get_watchlist_items(page).all()
    ]
    assert sorted(watchlist_object_ids) == sorted(added_ids)

    # Remove a watchlist item by clicking the remove button:
    remove_button = get_remove_button(watchlist_items.first)
    removed = model.objects.get(pk=get_object_id(remove_button))
    remove_button.click()
    watchlist_items = get_watchlist_items(page)
    assert watchlist_items.count() == 2
    assert not on_watchlist(removed)

    # Go to the edit page of a watchlist item and use the toggle button there:
    pk = get_object_id(watchlist_items.first.locator("button"))
    page.goto(edit_url(pk))
    removed = model.objects.get(pk=pk)
    toggle_button = get_toggle_button(page)
    assert_toggled_on(toggle_button)
    toggle_button.click()
    assert_toggled_off(toggle_button)
    assert not on_watchlist(removed)

    # Go back to the changelist, check that only the toggle buttons of
    # watchlist items are toggled.
    page.goto(get_url("changelist"))
    assert page.locator(".on-watchlist").count() == 1

    # Go to the watchlist again, and use the 'remove all' button:
    page.goto(get_url("watchlist"))
    watchlist_items = get_watchlist_items(page)
    assert watchlist_items.count() == 1
    # TODO: enable the rest of this test after the 'remove all' button was added
    # remove_button = watchlist_items.first.locator("button")
    # removed = model.objects.get(pk=get_object_id(remove_button))
    # page.locator(".remove-all").click()
    # assert get_watchlist_items(page).count() == 0
    # assert not on_watchlist(removed)
