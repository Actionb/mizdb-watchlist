import json
from unittest.mock import Mock, patch

import pytest
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, reverse
from django.views import View
from pytest_django.asserts import assertRedirects

from mizdb_watchlist.views import AdminWatchlistView, WatchlistViewMixin, watchlist_remove, watchlist_toggle


class WatchlistView(WatchlistViewMixin, View):
    pass


def dummy_view(*_args):
    return HttpResponse("This is a dummy view for tests")


admin_site = admin.AdminSite(name="test_site")


class URLConf:
    app_name = "test"  # Set the namespace for requests on these URLs
    urlpatterns = [
        path("watchlist/", WatchlistView.as_view(), name="watchlist"),
        path("admin/watchlist/", AdminWatchlistView.as_view(), name="admin_watchlist"),
        path("person/<int:pk>/change/", dummy_view, name="testapp_person_change"),
    ]


urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include(URLConf)),
    path("watchlist/", include("mizdb_watchlist.urls")),
]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]


class TestWatchlistViewMixin:

    @pytest.fixture
    def view(self, client):
        view = WatchlistViewMixin()
        view.request = client.get(reverse("test:watchlist")).wsgi_request
        return view

    def test_get_url_namespace(self, view):
        assert view.get_url_namespace() == "test"

    def test_get_object_url(self, view, model, test_obj):
        assert view.get_object_url(model, test_obj.pk) == f"/person/{test_obj.pk}/change/"

    def test_get_remove_url(self, view):
        assert view.get_remove_url() == reverse("watchlist:remove")

    def test_get_watchlist(self, view, add_to_watchlist):
        """Assert that get_watchlist calls manager.as_dict()."""
        as_dict_mock = Mock()
        get_manager_mock = Mock()
        get_manager_mock.return_value.as_dict = as_dict_mock
        with patch("mizdb_watchlist.views.get_manager", new=get_manager_mock):
            view.get_watchlist()
            get_manager_mock.assert_called()
            as_dict_mock.assert_called()

    def test_get_context_data(self, view, model, model_label):
        """Assert that the `watchlist` item contains the expected data."""
        watchlist = {model_label: [{"object_id": 1}, {"object_id": 2}]}
        with patch.object(view, "get_watchlist", new=Mock(return_value=watchlist)):
            context = view.get_context_data()
            assert model._meta.verbose_name in context["watchlist"]
            model_watchlist = context["watchlist"][model._meta.verbose_name]
            assert len(model_watchlist) == 2
            obj1, obj2 = model_watchlist
            assert obj1["object_id"] == 1
            assert obj1["object_url"] == reverse("test:testapp_person_change", args=[1])
            assert obj1["model_label"] == model_label
            assert obj2["object_id"] == 2
            assert obj2["object_url"] == reverse("test:testapp_person_change", args=[2])
            assert obj2["model_label"] == model_label

    def test_get_context_data_ignores_unknown_models(self, view):
        """Assert that unknown models are not included in the `watchlist` item."""
        watchlist = {"foo.bar": [{"object_id": 1}]}
        with patch.object(view, "get_watchlist", new=Mock(return_value=watchlist)):
            assert not view.get_context_data()["watchlist"]


@pytest.mark.usefixtures("login_user")
class TestAdminWatchlistView:

    @pytest.fixture
    def view(self, client):
        view = AdminWatchlistView()
        view.admin_site = admin_site
        view.request = client.get(reverse("test:admin_watchlist")).wsgi_request
        return view

    def test_media(self, view):
        """
        Assert that the media property contains URLs for the required static
        files.
        """
        media = view.media
        assert "mizdb_watchlist/js/watchlist.js" in media._js
        assert "mizdb_watchlist/css/watchlist.css" in media._css["all"]

    def test_get_url_namespace(self, view):
        """Assert that the URL namespace is set to the name of the admin site."""
        assert view.get_url_namespace() == admin_site.name

    def test_get_context_data_adds_each_context(self, view):
        """Assert that get_context_data includes admin_site.each_context()."""
        with patch.object(admin_site, "each_context") as each_context_mock:
            each_context_mock.return_value = {"foo": "bar"}
            context = view.get_context_data()
            each_context_mock.assert_called()
            assert context["foo"] == "bar"

    @pytest.mark.parametrize("login_user", [None])
    def test_permission_required(self, client, login_user):
        response = client.get(reverse("test:admin_watchlist"))
        assertRedirects(response, reverse("test_site:login") + "?next=%2Fadmin%2Fwatchlist%2F")


@pytest.fixture
def request_data(request, object_id, model_label):
    # Overwrites the default data for the http_request fixture.
    return {"object_id": object_id, "model_label": model_label}


@pytest.fixture
def object_id(test_obj):
    return test_obj.pk


@pytest.mark.usefixtures("login_user")
@pytest.mark.parametrize("request_method", ["POST"])
class TestWatchlistToggle:

    def test_watchlist_toggle(self, http_request):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert json.loads(response.content)["on_watchlist"]

    def test_watchlist_toggle_already_on_watchlist(self, add_to_watchlist, http_request):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]

    @pytest.mark.parametrize("request_data", [{}])
    def test_watchlist_toggle_missing_parameters(self, http_request, request_data):
        response = watchlist_toggle(http_request)
        assert response.status_code == 400

    @pytest.mark.parametrize("object_id", ["foo"])
    def test_watchlist_toggle_invalid_pk(self, http_request, object_id):
        response = watchlist_toggle(http_request)
        assert response.status_code == 400

    @pytest.mark.parametrize("model_label", ["foo.bar"])
    def test_watchlist_toggle_unknown_model(self, http_request, model_label):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]

    @pytest.mark.parametrize("object_id", [-1])
    def test_watchlist_toggle_object_does_not_exist(self, http_request, object_id):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]


@pytest.mark.usefixtures("login_user")
@pytest.mark.parametrize("request_method", ["POST"])
class TestWatchlistRemove:

    def test_watchlist_remove(self, http_request):
        response = watchlist_remove(http_request)
        assert response.status_code == 200

    @pytest.mark.parametrize("request_data", [{}])
    def test_watchlist_remove_missing_parameters(self, http_request, request_data):
        response = watchlist_remove(http_request)
        assert response.status_code == 400

    @pytest.mark.parametrize("object_id", ["foo"])
    def test_watchlist_remove_invalid_pk(self, http_request, object_id):
        response = watchlist_remove(http_request)
        assert response.status_code == 400

    @pytest.mark.parametrize("model_label", ["foo.bar"])
    def test_watchlist_remove_unknown_model(self, http_request, model_label):
        response = watchlist_remove(http_request)
        assert response.status_code == 200

    @pytest.mark.parametrize("object_id", [-1])
    def test_watchlist_remove_object_does_not_exist(self, http_request, object_id):
        response = watchlist_remove(http_request)
        assert response.status_code == 200
