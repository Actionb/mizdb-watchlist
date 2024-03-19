from operator import itemgetter
from typing import Union

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType

from mizdb_watchlist.manager import WATCHLIST_SESSION_KEY, ModelManager, SessionManager, get_manager
from mizdb_watchlist.models import Watchlist

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(manager_class, http_request, add_session) -> Union[SessionManager, ModelManager]:
    """Return a watchlist manager instance for the current HTTP request."""
    return manager_class(http_request)


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

    @pytest.fixture
    def watchlist_items(self, test_obj) -> list[dict]:
        """Default items for the session watchlist."""
        return [{"object_id": test_obj.pk, "object_repr": str(test_obj)}]

    @pytest.fixture
    def model_watchlist(self, model_label, watchlist_items) -> dict:
        """The session watchlist for the test model."""
        return {model_label: watchlist_items}

    @pytest.fixture
    def session_data(self, model_watchlist) -> dict:
        # Override session_data fixture to add the given model watchlist to the
        # default session data.
        if model_watchlist:
            return {WATCHLIST_SESSION_KEY: model_watchlist}
        return {}

    @pytest.fixture
    def session_pks(self, model_label):
        """Return a list of all primary keys in the session watchlist."""

        def inner(request) -> list[int]:
            return list(map(itemgetter("object_id"), request.session[WATCHLIST_SESSION_KEY].get(model_label, [])))

        return inner

    @pytest.mark.parametrize("watchlist_items", [[{"object_id": 42, "object_repr": "foo"}]])
    def test_get_model_watchlist(self, manager, model, watchlist_items):
        assert manager.get_model_watchlist(model) == [{"object_id": 42, "object_repr": "foo"}]

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_get_model_watchlist_no_session_watchlist(self, manager, model, watchlist_items):
        assert manager.get_model_watchlist(model) == []

    def test_on_watchlist(self, manager, test_obj):
        assert manager.on_watchlist(test_obj)

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_not_on_watchlist(self, manager, test_obj, watchlist_items):
        assert not manager.on_watchlist(test_obj)

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_add(self, manager, http_request, test_obj, session_pks, watchlist_items):
        manager.add(test_obj)
        assert test_obj.pk in session_pks(http_request)

    def test_add_already_on_watchlist(self, manager, http_request, test_obj, session_pks):
        manager.add(test_obj)
        assert session_pks(http_request).count(test_obj.pk) == 1

    def test_remove(self, manager, http_request, test_obj, session_pks):
        manager.remove(test_obj)
        assert test_obj.pk not in session_pks(http_request)

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_remove_not_on_watchlist(self, manager, http_request, test_obj, session_pks, watchlist_items):
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

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_annotate_queryset_not_on_watchlist(self, manager, model, test_obj, watchlist_items):
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

    def test_prune_models(self, manager, model_watchlist):
        model_watchlist["foo.bar"] = []
        manager._prune_models()
        assert "foo.bar" not in manager.get_watchlist()

    def test_prune_model_objects(self, manager, watchlist_items, model):
        watchlist_items.append({"object_id": 0, "object_repr": "Foo"})
        manager._prune_model_objects()
        assert {"object_id": 0, "object_repr": "Foo"} not in manager.get_model_watchlist(model)

    def test_get_stale_pks(self, manager, model, watchlist_items):
        watchlist_items.append({"object_id": 0, "objet_repr": "foo"})
        assert manager._get_stale_pks(model) == {0}

    def test_bulk_add_list(self, manager, person_factory, session_pks, http_request):
        new1 = person_factory()
        new2 = person_factory()
        manager.bulk_add([new1, new2])
        assert new1.pk in session_pks(http_request)

    def test_bulk_add_queryset(self, manager, person_factory, model, session_pks, http_request):
        new1 = person_factory()
        new2 = person_factory()
        queryset = model.objects.filter(pk__in=[new1.pk, new2.pk])
        manager.bulk_add(queryset)
        assert new1.pk in session_pks(http_request)

    def test_remove_model(self, manager, model, model_label, http_request):
        manager.remove_model(model)
        assert not manager.get_model_watchlist(model)


@pytest.mark.parametrize("manager_class", [ModelManager])
class TestModelManager:
    def test_on_watchlist(self, manager, fill_watchlist, test_obj):
        assert manager.on_watchlist(test_obj)

    def test_not_on_watchlist(self, manager, test_obj):
        assert not manager.on_watchlist(test_obj)

    def test_add(self, manager, test_obj, watchlist_model, user):
        manager.add(test_obj)
        assert watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_add_already_on_watchlist(self, manager, fill_watchlist, test_obj, watchlist_model, user):
        manager.add(test_obj)
        assert watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).count() == 1

    def test_remove(self, manager, fill_watchlist, test_obj, watchlist_model, user):
        manager.remove(test_obj)
        assert not watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_toggle_on_watchlist(self, manager, fill_watchlist, test_obj, watchlist_model, user):
        assert not manager.toggle(test_obj)
        assert not watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_toggle_not_on_watchlist(self, manager, test_obj, watchlist_model, user):
        assert manager.toggle(test_obj)
        assert watchlist_model.objects.filter(object_id=test_obj.pk, user_id=user.pk).exists()

    def test_annotate_queryset(self, manager, fill_watchlist, test_obj, model):
        queryset = model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert queryset.get(pk=test_obj.pk).on_watchlist

    def test_annotate_queryset_not_on_watchlist(self, manager, model, test_obj):
        queryset = model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert not queryset.get(pk=test_obj.pk).on_watchlist

    def test_as_dict(self, manager, fill_watchlist, model_label, test_obj):
        as_dict = manager.as_dict()
        assert model_label in as_dict
        model_watchlist = as_dict[model_label]
        assert len(model_watchlist) == 1
        assert model_watchlist[0]["object_id"] == test_obj.pk
        assert model_watchlist[0]["object_repr"] == str(test_obj)
        assert model_watchlist[0]["notes"] == ""

    def test_prune_models(self, manager, user):
        ct = ContentType.objects.create(app_label="foo", model="bar")
        Watchlist.objects.create(user=user, content_type=ct, object_id=0, object_repr="foo")
        manager._prune_models()
        assert not Watchlist.objects.filter(content_type=ct).exists()

    def test_prune_model_objects(self, manager, fill_watchlist, person_factory, add_to_watchlist):
        new = person_factory()
        new_pk = new.pk
        add_to_watchlist(new)
        new.delete()
        manager._prune_model_objects()
        assert not Watchlist.objects.filter(object_id=new_pk).exists()

    def test_get_stale_pks(self, manager, fill_watchlist, person_factory, add_to_watchlist, model):
        new = person_factory()
        new_pk = new.pk
        add_to_watchlist(new)
        new.delete()
        assert new_pk in manager._get_stale_pks(model)

    def test_bulk_add_list(self, manager, person_factory, user):
        new1 = person_factory()
        new2 = person_factory()
        manager.bulk_add([new1, new2])
        assert Watchlist.objects.filter(object_id=new1.pk, user=user.pk)
        assert Watchlist.objects.filter(object_id=new2.pk, user=user.pk)

    def test_bulk_add_queryset(self, manager, person_factory, model, user):
        new1 = person_factory()
        new2 = person_factory()
        queryset = model.objects.filter(pk__in=[new1.pk, new2.pk])
        manager.bulk_add(queryset)
        assert Watchlist.objects.filter(object_id=new1.pk, user=user.pk)
        assert Watchlist.objects.filter(object_id=new2.pk, user=user.pk)

    def test_bulk_add_empty_list(self, manager, django_assert_num_queries):
        with django_assert_num_queries(0):
            manager.bulk_add([])

    def test_bulk_add_empty_queryset(self, manager, django_assert_num_queries, model):
        with django_assert_num_queries(0):
            manager.bulk_add(model.objects.none())

    def test_bulk_add_skips_existing(self, manager, person_factory, add_to_watchlist, user):
        obj = person_factory(id=420)
        add_to_watchlist(obj)
        manager.bulk_add([obj])
        assert Watchlist.objects.filter(object_id=obj.pk, user=user.pk).count() == 1

    def test_remove_model(self, manager, fill_watchlist, model):
        manager.remove_model(model)
        assert not Watchlist.objects.exists()
