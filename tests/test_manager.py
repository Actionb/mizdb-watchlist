from operator import itemgetter
from typing import Union

import pytest
from django.contrib.auth.models import AnonymousUser

from mizdb_watchlist.manager import WATCHLIST_SESSION_KEY, ModelManager, SessionManager, get_manager

pytestmark = pytest.mark.django_db


@pytest.fixture
def session_watchlist(test_obj) -> list[dict]:
    """The watchlist to be used with a session watchlist."""
    return [{"object_id": test_obj.pk, "object_repr": str(test_obj)}]


@pytest.fixture
def model_watchlist(model_label, session_watchlist) -> dict:
    """The watchlist for the test model."""
    return {model_label: session_watchlist}


@pytest.fixture
def session_data(model_watchlist) -> dict:
    # Override session_data fixture to add the given model watchlist to the
    # default session data.
    if model_watchlist:
        return {WATCHLIST_SESSION_KEY: model_watchlist}
    return {}


@pytest.fixture
def manager(manager_class, http_request, add_session) -> Union[SessionManager, ModelManager]:
    """Return a watchlist manager instance for the current HTTP request."""
    return manager_class(http_request)


@pytest.fixture
def session_pks(model_label):
    """Return a list of all primary keys in the session watchlist."""

    def inner(request) -> list[int]:
        return list(map(itemgetter("object_id"), request.session[WATCHLIST_SESSION_KEY].get(model_label, [])))

    return inner


@pytest.mark.parametrize("user", [AnonymousUser()])
def test_get_manager_anonymous_user(http_request, user):
    """
    Assert that get_manager returns a SessionManager for requests made by
    unauthenticated users.
    """
    assert isinstance(get_manager(http_request), SessionManager)


@pytest.mark.parametrize("user", [None])
def test_get_manager_user_not_set(http_request, user):
    """
    Assert that get_manager returns a SessionManager for requests where the
    user attribute is not set.
    """
    assert isinstance(get_manager(http_request), SessionManager)


def test_get_manager_authenticated_user(http_request, user):
    """
    Assert that get_manager returns a ModelManager for requests made by
    authenticated users.
    """
    assert isinstance(get_manager(http_request), ModelManager)


@pytest.mark.usefixtures("add_session")
@pytest.mark.parametrize("manager_class", [SessionManager])
@pytest.mark.parametrize("user", [None])
class TestSessionManager:
    @pytest.mark.parametrize("session_watchlist", [[{"object_id": 42, "object_repr": "foo"}]])
    def test_get_model_watchlist(self, manager, model, session_watchlist):
        assert manager.get_model_watchlist(model) == [{"object_id": 42, "object_repr": "foo"}]

    @pytest.mark.parametrize("session_watchlist", [[]])
    def test_get_model_watchlist_no_session_watchlist(self, manager, model, session_watchlist):
        assert manager.get_model_watchlist(model) == []

    def test_on_watchlist(self, manager, test_obj):
        assert manager.on_watchlist(test_obj)

    @pytest.mark.parametrize("session_watchlist", [[]])
    def test_not_on_watchlist(self, manager, test_obj, session_watchlist):
        assert not manager.on_watchlist(test_obj)

    @pytest.mark.parametrize("session_watchlist", [[]])
    def test_add(self, manager, http_request, test_obj, session_pks, session_watchlist):
        manager.add(test_obj)
        assert test_obj.pk in session_pks(http_request)

    def test_add_already_on_watchlist(self, manager, http_request, test_obj, session_pks):
        manager.add(test_obj)
        assert session_pks(http_request).count(test_obj.pk) == 1

    def test_remove(self, manager, http_request, test_obj, session_pks):
        manager.remove(test_obj)
        assert test_obj.pk not in session_pks(http_request)

    @pytest.mark.parametrize("session_watchlist", [[]])
    def test_remove_not_on_watchlist(self, manager, http_request, test_obj, session_pks, session_watchlist):
        manager.remove(test_obj)
        assert test_obj.pk not in session_pks(http_request)

    def test_removing_last_item_removes_model_watchlist(self, manager, test_obj, session_pks):
        """
        Assert that removing the last item of a model watchlist also removes
        the model label key from the global watchlist.
        """
        manager.remove(test_obj)
        label = manager._get_watchlist_label(test_obj)
        assert label not in manager.get_watchlist()

    def test_annotate_queryset(self, manager, model, test_obj):
        queryset = model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert queryset.get(pk=test_obj.pk).on_watchlist

    @pytest.mark.parametrize("session_watchlist", [[]])
    def test_annotate_queryset_not_on_watchlist(self, manager, model, test_obj, session_watchlist):
        queryset = model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert not queryset.get(pk=test_obj.pk).on_watchlist

    def test_add_model_watchlist(self, manager, model, model_label):
        manager._add_model_watchlist(model)
        assert model_label in manager.get_watchlist()

    @pytest.mark.parametrize("model_watchlist", [{}])
    def test_add_model_watchlist_model_not_on_watchlist(self, manager, model, model_label, model_watchlist):
        manager._add_model_watchlist(model)
        assert model_label in manager.get_watchlist()


@pytest.mark.parametrize("manager_class", [ModelManager])
class TestModelManager:
    def test_on_watchlist(self, manager, add_to_watchlist, test_obj):
        assert manager.on_watchlist(test_obj)

    def test_not_on_watchlist(self, manager, test_obj):
        assert not manager.on_watchlist(test_obj)

    def test_add(self, manager, user, test_obj, watchlist_model):
        manager.add(test_obj)
        assert watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_add_already_on_watchlist(self, manager, user, add_to_watchlist, test_obj, watchlist_model):
        manager.add(test_obj)
        assert watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).count() == 1

    def test_remove(self, manager, user, add_to_watchlist, test_obj, watchlist_model):
        manager.remove(test_obj)
        assert not watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_toggle_on_watchlist(self, manager, user, add_to_watchlist, test_obj, watchlist_model):
        assert not manager.toggle(test_obj)
        assert not watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_toggle_not_on_watchlist(self, manager, user, test_obj, watchlist_model):
        assert manager.toggle(test_obj)
        assert watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_annotate_queryset(self, manager, model, test_obj, add_to_watchlist):
        queryset = model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert queryset.get(pk=test_obj.pk).on_watchlist

    def test_annotate_queryset_not_on_watchlist(self, manager, model, test_obj):
        queryset = model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert not queryset.get(pk=test_obj.pk).on_watchlist

    def test_as_dict(self, manager, model, model_label, test_obj, add_to_watchlist):
        as_dict = manager.as_dict()
        assert model_label in as_dict
        model_watchlist = as_dict[model_label]
        assert len(model_watchlist) == 1
        assert model_watchlist[0]["object_id"] == test_obj.pk
        assert model_watchlist[0]["object_repr"] == str(test_obj)
        assert model_watchlist[0]["notes"] == ""
