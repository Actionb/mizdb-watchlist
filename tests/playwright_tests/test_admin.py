import pytest
from django.contrib import admin
from django.urls import include, path, reverse
from playwright.sync_api import expect

urlpatterns = [
    path("admin/", admin.site.urls),
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

    def test_is_toggled_when_already_on_watchlist(
        self,
        add_to_watchlist,
        change_view,
        get_toggle_button,
        assert_toggled_on,
    ):
        assert_toggled_on(get_toggle_button(change_view))


@pytest.fixture
def changelist_view(page, get_url, model):
    page.goto(get_url(reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")))
    return page


class TestAdminAction:
    """Test the 'add to watchlist' admin action."""

    # TODO: add tests for 'add to watchlist' admin action
