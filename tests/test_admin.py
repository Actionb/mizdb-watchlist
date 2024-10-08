from unittest.mock import patch

import pytest
from django.contrib import admin
from django.urls import include, path, reverse

from mizdb_watchlist.admin import WatchlistAdmin, WatchlistMixin
from mizdb_watchlist.models import Watchlist
from tests.testapp.models import Person

site = admin.AdminSite(name="test_admin")

admin.register(Watchlist, site=site)(WatchlistAdmin)

urlpatterns = [path("", site.urls), path("watchlist", include("mizdb_watchlist.urls"))]

pytestmark = [pytest.mark.urls(__name__)]


@pytest.fixture
def model_admin():
    """Return a WatchlistAdmin instance."""
    return WatchlistAdmin(Watchlist, site)


@pytest.fixture
def mock_get_watchlist_context(model_admin):
    with patch.object(model_admin, "get_watchlist_context") as m:
        yield m


@pytest.fixture
def mock_each_context():
    with patch.object(site, "each_context") as m:
        yield m


@pytest.fixture
def watchlist_response(http_request, model_admin):
    """Call model_admin.watchlist and return the response."""
    return model_admin.watchlist(http_request)


@pytest.mark.usefixtures("mock_each_context", "mock_get_watchlist_context")
class TestWatchlistAdmin:
    def test_get_urls_includes_watchlist_url(self, model_admin):
        pattern = model_admin.get_urls()[0]
        assert pattern.name == "watchlist"
        assert pattern.lookup_str == "mizdb_watchlist.admin.WatchlistAdmin.watchlist"

    def test_watchlist_url_reversible(self):
        assert reverse("admin:watchlist")

    def test_watchlist_context(self, watchlist_response):
        context = watchlist_response.context_data
        assert context["title"] == "My watchlist"

    def test_watchlist_calls_get_watchlist_context(self, mock_get_watchlist_context, watchlist_response):
        mock_get_watchlist_context.assert_called()

    def test_watchlist_calls_each_context(self, mock_each_context, watchlist_response):
        mock_each_context.assert_called()


@pytest.fixture
def add_watchlist_annotations():
    return True


class PersonAdmin(WatchlistMixin, admin.ModelAdmin):
    pass


class TestModelAdminMixin:
    @pytest.fixture
    def view(self, http_request, add_watchlist_annotations):
        view = PersonAdmin(Person, admin.site)
        view.add_watchlist_annotations = add_watchlist_annotations
        return view

    def test_get_queryset_add_annotations(self, view, http_request):
        assert "on_watchlist" in view.get_queryset(http_request).query.annotations

    @pytest.mark.parametrize("add_watchlist_annotations", [False])
    def test_get_queryset_not_add_annotations(self, view, http_request, add_watchlist_annotations):
        assert "on_watchlist" not in view.get_queryset(http_request).query.annotations

    @pytest.mark.parametrize("request_data", [{"on_watchlist": True}])
    def test_get_queryset_filtered(self, view, http_request, fill_watchlist, person_factory, request_data):
        person_on_watchlist = fill_watchlist[0]
        person_not_on_watchlist = person_factory()
        queryset = view.get_queryset(http_request)
        assert person_on_watchlist in queryset
        assert person_not_on_watchlist not in queryset

    def test_get_queryset_not_filtered(self, view, http_request, fill_watchlist, person_factory):
        person_on_watchlist = fill_watchlist[0]
        person_not_on_watchlist = person_factory()
        queryset = view.get_queryset(http_request)
        assert person_on_watchlist in queryset
        assert person_not_on_watchlist in queryset
