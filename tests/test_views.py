import json
from unittest.mock import Mock, patch

import pytest
from django.contrib import admin
from django.http import HttpResponse
from django.urls import NoReverseMatch, include, path, reverse
from django.views import View
from django.views.generic import ListView

from mizdb_watchlist.manager import ANNOTATION_FIELD
from mizdb_watchlist.views import (
    WatchlistMixin,
    WatchlistViewMixin,
    watchlist_remove,
    watchlist_remove_all,
    watchlist_toggle,
)
from tests.testapp.models import Company, Person


class WatchlistView(WatchlistViewMixin, View):
    pass


def dummy_view(*_args):
    return HttpResponse("This is a dummy view for tests")


admin_site = admin.AdminSite(name="test_site")


class URLConf:
    app_name = "test"  # Set the namespace for requests on these URLs
    urlpatterns = [
        path("watchlist/", WatchlistView.as_view(), name="watchlist"),
        path("person/<int:pk>/change/", dummy_view, name="testapp_person_change"),
        path("person/", dummy_view, name="testapp_person_changelist"),
    ]


urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include(URLConf)),
    path("watchlist/", include("mizdb_watchlist.urls")),
]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]


class TestWatchlistViewMixin:
    @pytest.fixture
    def view(self):
        return WatchlistViewMixin()

    @pytest.fixture
    def mock_get_manager(self):
        with patch("mizdb_watchlist.views.get_manager") as m:
            yield m

    @pytest.fixture
    def mock_get_watchlist(self, view):
        with patch.object(view, "get_watchlist") as m:
            yield m

    @pytest.fixture
    def mock_get_object_url(self, view):
        with patch.object(view, "get_object_url") as m:
            yield m

    @pytest.fixture
    def wsgi_request(self, client):
        return client.get(reverse("test:watchlist")).wsgi_request

    def test_get_object_url(self, view, wsgi_request, person_model, person):
        assert view.get_object_url(wsgi_request, person_model, person.pk) == f"/person/{person.pk}/change/"

    def test_get_object_url_fails_silently(self, view, wsgi_request, person_model):
        assert view.get_object_url(wsgi_request, person_model, -1) == ""

    def test_get_changelist_url(self, view, wsgi_request, person_model):
        assert view.get_changelist_url(wsgi_request, person_model) == "/person/"

    def test_get_changelist_url_fails_silently(self, view, wsgi_request):
        assert view.get_changelist_url(wsgi_request, Company) == ""

    def test_get_watchlist_calls_as_dict(self, view, mock_get_manager, wsgi_request):
        """Assert that get_watchlist calls manager.as_dict()."""
        as_dict_mock = Mock()
        mock_get_manager.return_value.as_dict = as_dict_mock
        view.get_watchlist(wsgi_request, prune=False)
        mock_get_manager.assert_called()
        as_dict_mock.assert_called()

    def test_get_watchlist_context(self, view, mock_get_watchlist, wsgi_request, person_model, person_label):
        """Assert that the `watchlist` item contains the expected data."""
        mock_get_watchlist.return_value = {
            person_label: [{"object_id": 1, "object_repr": "foo"}, {"object_id": 2, "object_repr": "bar"}]
        }
        context = view.get_watchlist_context(wsgi_request)
        assert person_model._meta.verbose_name in context["watchlist"]
        watchlist_data = context["watchlist"][person_model._meta.verbose_name]
        expected_url = f"{reverse('test:testapp_person_changelist')}?{ANNOTATION_FIELD}=True"
        assert watchlist_data["changelist_url"] == expected_url
        model_watchlist = watchlist_data["model_items"]
        assert len(model_watchlist) == 2
        obj1, obj2 = model_watchlist
        assert obj1["object_id"] == 1
        assert obj1["object_url"] == reverse("test:testapp_person_change", args=[1])
        assert obj1["model_label"] == person_label
        assert obj2["object_id"] == 2
        assert obj2["object_url"] == reverse("test:testapp_person_change", args=[2])
        assert obj2["model_label"] == person_label

    def test_get_watchlist_context_ignores_unknown_models(self, view, mock_get_watchlist, wsgi_request):
        """Assert that unknown models are not included in the `watchlist` item."""
        mock_get_watchlist.return_value = {"foo.bar": [{"object_id": 1}]}
        assert not view.get_watchlist_context(wsgi_request)["watchlist"]

    def test_get_watchlist_context_no_reverse_match(
        self,
        view,
        mock_get_watchlist,
        mock_get_object_url,
        person_label,
        wsgi_request,
    ):
        """
        Assert that items are skipped if `get_object_url` raises a
        NoReverseMatch.
        """
        mock_get_watchlist.return_value = {person_label: [{"object_id": 1}]}
        mock_get_object_url.side_effect = NoReverseMatch
        context = view.get_watchlist_context(wsgi_request)
        assert not context["watchlist"]


@pytest.fixture
def request_data(request, object_id, person_label):
    # Overwrites the default data for the http_request fixture.
    return {"object_id": object_id, "model_label": person_label}


@pytest.fixture
def object_id(person):
    return person.pk


@pytest.mark.usefixtures("login_user", "ignore_csrf_protection")
@pytest.mark.parametrize("request_method", ["POST"])
class TestWatchlistToggle:
    def test_watchlist_toggle(self, http_request):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert json.loads(response.content)["on_watchlist"]

    def test_watchlist_toggle_already_on_watchlist(self, http_request, fill_watchlist):
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

    @pytest.mark.parametrize("person_label", ["foo.bar"])
    def test_watchlist_toggle_unknown_model(self, http_request, person_label):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]

    @pytest.mark.parametrize("object_id", [-1])
    def test_watchlist_toggle_object_does_not_exist(self, http_request, object_id):
        response = watchlist_toggle(http_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]


@pytest.mark.usefixtures("login_user", "ignore_csrf_protection")
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

    @pytest.mark.parametrize("person_label", ["foo.bar"])
    def test_watchlist_remove_unknown_model(self, http_request, person_label):
        response = watchlist_remove(http_request)
        assert response.status_code == 200

    @pytest.mark.parametrize("object_id", [-1])
    def test_watchlist_remove_object_does_not_exist(self, http_request, object_id):
        response = watchlist_remove(http_request)
        assert response.status_code == 200


@pytest.mark.usefixtures("login_user", "ignore_csrf_protection")
@pytest.mark.parametrize("request_method", ["POST"])
class TestWatchlistRemoveAll:
    def test_watchlist_remove_all(self, http_request):
        response = watchlist_remove_all(http_request)
        assert response.status_code == 200

    @pytest.mark.parametrize("request_data", [{}])
    def test_watchlist_remove_missing_parameters(self, http_request, request_data):
        response = watchlist_remove_all(http_request)
        assert response.status_code == 400

    @pytest.mark.parametrize("person_label", ["foo.bar"])
    def test_watchlist_remove_all_unknown_model(self, http_request, person_label):
        response = watchlist_remove_all(http_request)
        assert response.status_code == 400


@pytest.fixture
def add_watchlist_annotations():
    return True


class DummyListView(WatchlistMixin, ListView):
    queryset = Person.objects.all()


class TestListViewMixin:
    @pytest.fixture
    def view(self, http_request, add_watchlist_annotations):
        view = DummyListView()
        view.request = http_request
        view.add_watchlist_annotations = add_watchlist_annotations
        return view

    def test_get_queryset_add_annotations(self, view):
        assert "on_watchlist" in view.get_queryset().query.annotations

    @pytest.mark.parametrize("add_watchlist_annotations", [False])
    def test_get_queryset_not_add_annotations(self, view, add_watchlist_annotations):
        assert "on_watchlist" not in view.get_queryset().query.annotations

    @pytest.mark.parametrize("request_data", [{"on_watchlist": True}])
    def test_get_queryset_filtered(self, view, fill_watchlist, person_factory, request_data):
        person_on_watchlist = fill_watchlist[0]
        person_not_on_watchlist = person_factory()
        queryset = view.get_queryset()
        assert person_on_watchlist in queryset
        assert person_not_on_watchlist not in queryset

    def test_get_queryset_not_filtered(self, view, fill_watchlist, person_factory):
        person_on_watchlist = fill_watchlist[0]
        person_not_on_watchlist = person_factory()
        queryset = view.get_queryset()
        assert person_on_watchlist in queryset
        assert person_not_on_watchlist in queryset
