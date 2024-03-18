from unittest.mock import patch

import pytest
from django.contrib import admin
from django.urls import include, path, reverse

from mizdb_watchlist.admin import WatchlistAdmin
from mizdb_watchlist.models import Watchlist

site = admin.AdminSite(name="test_admin")


@admin.register(Watchlist, site=site)
class WatchlistAdmin(WatchlistAdmin):
    pass


urlpatterns = [path("", site.urls), path("watchlist", include("mizdb_watchlist.urls"))]

pytestmark = [pytest.mark.urls(__name__)]


@pytest.fixture
def model_admin():
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
    return model_admin.watchlist(http_request)


@pytest.mark.usefixtures("mock_each_context", "mock_get_watchlist_context")
class TestWatchlistAdmin:

    def test_watchlist_url(self):
        assert reverse("admin:watchlist")

    def test_watchlist_context(self, watchlist_response):
        context = watchlist_response.context_data
        media = context["media"]
        assert "mizdb_watchlist/js/watchlist.js" in media._js
        assert "mizdb_watchlist/css/watchlist.css" in media._css["all"]
        assert context["title"] == "My watchlist"

    def test_watchlist_calls_get_watchlist_context(self, mock_get_watchlist_context, watchlist_response):
        mock_get_watchlist_context.assert_called()

    def test_watchlist_calls_each_context(self, mock_each_context, watchlist_response):
        mock_each_context.assert_called()
