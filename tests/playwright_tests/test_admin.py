import pytest
from django.contrib import admin
from django.urls import include, path
from playwright.sync_api import expect

from mizdb_watchlist.actions import add_to_watchlist
from mizdb_watchlist.admin import WatchlistAdmin
from mizdb_watchlist.models import Watchlist
from tests.testapp.models import Person

site = admin.AdminSite(name="admin")


@admin.register(Person, site=site)
class PersonAdmin(admin.ModelAdmin):
    actions = [add_to_watchlist]


@admin.register(Watchlist, site=site)
class WatchlistAdmin(WatchlistAdmin):
    pass


urlpatterns = [
    path("admin/", site.urls),
    path("mizdb_watchlist/", include("mizdb_watchlist.urls")),
]

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls(__name__),
    pytest.mark.usefixtures("session_login"),
    pytest.mark.pw,
]


@pytest.fixture
def change_view(page, get_url, test_obj):
    page.goto(get_url(f"admin:{test_obj._meta.app_label}_{test_obj._meta.model_name}_change", args=[test_obj.pk]))
    return page


class TestChangeView:
    """Test the toggle button on the admin change view page."""

    def test_has_toggle_button(self, change_view, get_toggle_button):
        expect(get_toggle_button(change_view)).to_be_visible()

    def test_can_toggle(
        self,
        change_view,
        get_toggle_button,
        assert_toggled_on,
        assert_toggled_off,
        on_watchlist_model,
        test_obj,
    ):
        toggle_button = get_toggle_button(change_view)
        toggle_button.click()
        assert_toggled_on(toggle_button)
        assert on_watchlist_model(test_obj)
        toggle_button = get_toggle_button(change_view)
        toggle_button.click()
        assert_toggled_off(toggle_button)
        assert not on_watchlist_model(test_obj)

    def test_button_toggled_when_on_watchlist(self, fill_watchlist, change_view, get_toggle_button, assert_toggled_on):
        assert_toggled_on(get_toggle_button(change_view))

    def test_watchlist_link(self, change_view, get_watchlist_link):
        watchlist_link = get_watchlist_link(change_view.locator("#user-tools"))
        expect(watchlist_link).to_be_visible()
        watchlist_link.click()
        change_view.wait_for_url("**/_watchlist/", timeout=1000)


@pytest.fixture
def changelist_view(page, get_url, model):
    page.goto(get_url(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"))
    return page


class TestAdminAction:
    """Test the 'add to watchlist' admin action."""

    def test_add_to_watchlist_action(self, test_obj, changelist_view, on_watchlist_model):
        checkboxes = changelist_view.locator(".action-checkbox").get_by_role("checkbox")
        checkboxes.first.click()
        changelist_form = changelist_view.locator("#changelist-form")
        changelist_form.get_by_label("Action").select_option(value="add_to_watchlist")
        changelist_form.get_by_role("button").click()
        assert on_watchlist_model(test_obj)
