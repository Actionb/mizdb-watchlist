from operator import itemgetter
from typing import Union

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType

from mizdb_watchlist.manager import WATCHLIST_SESSION_KEY, ModelManager, SessionManager, get_manager

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
    def watchlist_items(self, person) -> list[dict]:
        """Default items for the session watchlist."""
        return [{"object_id": person.pk, "object_repr": str(person)}]

    @pytest.fixture
    def person_watchlist(self, person_label, watchlist_items) -> dict:
        """The session watchlist for the Person model."""
        return {person_label: watchlist_items}

    @pytest.fixture
    def session_data(self, person_watchlist) -> dict:
        # Override session_data fixture to add the given person watchlist to
        # the default session data.
        if person_watchlist:
            return {WATCHLIST_SESSION_KEY: person_watchlist}
        return {}

    @pytest.fixture
    def session_pks(self, person_label):
        """Return a list of all primary keys in the session watchlist."""

        def inner(request) -> list[int]:
            return list(map(itemgetter("object_id"), request.session[WATCHLIST_SESSION_KEY].get(person_label, [])))

        return inner

    @pytest.mark.parametrize("watchlist_items", [[{"object_id": 42, "object_repr": "foo"}]])
    def test_get_model_watchlist(self, manager, person_model, watchlist_items):
        assert manager.get_model_watchlist(person_model) == [{"object_id": 42, "object_repr": "foo"}]

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_get_model_watchlist_no_session_watchlist(self, manager, person_model, watchlist_items):
        assert manager.get_model_watchlist(person_model) == []

    def test_on_watchlist(self, manager, person):
        assert manager.on_watchlist(person)

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_not_on_watchlist(self, manager, person, watchlist_items):
        assert not manager.on_watchlist(person)

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_add(self, manager, http_request, person, session_pks, watchlist_items):
        manager.add(person)
        assert person.pk in session_pks(http_request)

    def test_add_already_on_watchlist(self, manager, http_request, person, session_pks):
        manager.add(person)
        assert session_pks(http_request).count(person.pk) == 1

    def test_remove(self, manager, http_request, person, session_pks):
        manager.remove(person)
        assert person.pk not in session_pks(http_request)

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_remove_not_on_watchlist(self, manager, http_request, person, session_pks, watchlist_items):
        manager.remove(person)
        assert person.pk not in session_pks(http_request)

    def test_removing_last_item_removes_model_watchlist(self, manager, person, session_pks):
        """
        Assert that removing the last item of a model watchlist also removes
        the model label key from the session watchlist.
        """
        manager.remove(person)
        label = manager._get_watchlist_label(person)
        assert label not in manager.get_watchlist()

    def test_annotate_queryset(self, manager, person_model, person):
        queryset = person_model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert queryset.get(pk=person.pk).on_watchlist

    @pytest.mark.parametrize("watchlist_items", [[]])
    def test_annotate_queryset_not_on_watchlist(self, manager, person_model, person, watchlist_items):
        queryset = person_model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert not queryset.get(pk=person.pk).on_watchlist

    def test_add_model_watchlist(self, manager, person_model, person_label):
        manager._add_model_watchlist(person_model)
        assert person_label in manager.get_watchlist()

    @pytest.mark.parametrize("person_watchlist", [{}])
    def test_add_model_watchlist_model_not_on_watchlist(self, manager, person_model, person_label, person_watchlist):
        manager._add_model_watchlist(person_model)
        assert person_label in manager.get_watchlist()

    def test_prune_models(self, manager, person_watchlist):
        person_watchlist["foo.bar"] = []
        manager._prune_models()
        assert "foo.bar" not in manager.get_watchlist()

    def test_prune_model_objects(self, manager, watchlist_items, person_model):
        watchlist_items.append({"object_id": 0, "object_repr": "Foo"})
        manager._prune_model_objects()
        assert {"object_id": 0, "object_repr": "Foo"} not in manager.get_model_watchlist(person_model)

    def test_get_stale_pks(self, manager, person_model, watchlist_items):
        watchlist_items.append({"object_id": 0, "objet_repr": "foo"})
        assert manager._get_stale_pks(person_model) == {0}

    def test_bulk_add_list(self, manager, person_factory, session_pks, http_request):
        new1 = person_factory()
        new2 = person_factory()
        manager.bulk_add([new1, new2])
        assert new1.pk in session_pks(http_request)

    def test_bulk_add_queryset(self, manager, person_factory, person_model, session_pks, http_request):
        new1 = person_factory()
        new2 = person_factory()
        queryset = person_model.objects.filter(pk__in=[new1.pk, new2.pk])
        manager.bulk_add(queryset)
        assert new1.pk in session_pks(http_request)

    def test_remove_model(self, manager, person_model, person_label, http_request):
        manager.remove_model(person_model)
        assert not manager.get_model_watchlist(person_model)

    def test_filter(self, manager, person_factory, person_model, person):
        new1 = person_factory()
        queryset = person_model.objects.all()
        filtered_queryset = manager.filter(queryset)
        assert person in filtered_queryset
        assert new1 not in filtered_queryset


@pytest.mark.parametrize("manager_class", [ModelManager])
class TestModelManager:
    @pytest.fixture
    def person_watchlist(self, watchlist_model, person_ct, user):
        return watchlist_model.objects.filter(content_type=person_ct, user_id=user.pk)

    def test_on_watchlist(self, manager, fill_watchlist, person):
        assert manager.on_watchlist(person)

    def test_not_on_watchlist(self, manager, person):
        assert not manager.on_watchlist(person)

    def test_add(self, manager, person, person_watchlist):
        manager.add(person)
        assert person_watchlist.filter(object_id=person.pk).exists()

    def test_add_already_on_watchlist(self, manager, fill_watchlist, person, person_watchlist):
        manager.add(person)
        assert person_watchlist.filter(object_id=person.pk).count() == 1

    def test_remove(self, manager, fill_watchlist, person, person_watchlist):
        manager.remove(person)
        assert not person_watchlist.filter(object_id=person.pk).exists()

    def test_toggle_on_watchlist(self, manager, fill_watchlist, person, person_watchlist):
        assert not manager.toggle(person)
        assert not person_watchlist.filter(object_id=person.pk).exists()

    def test_toggle_not_on_watchlist(self, manager, person, person_watchlist):
        assert manager.toggle(person)
        assert person_watchlist.filter(object_id=person.pk).exists()

    def test_annotate_queryset(self, manager, fill_watchlist, person, person_model):
        queryset = person_model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert queryset.get(pk=person.pk).on_watchlist

    def test_annotate_queryset_not_on_watchlist(self, manager, person_model, person):
        queryset = person_model.objects.all()
        queryset = manager.annotate_queryset(queryset)
        assert not queryset.get(pk=person.pk).on_watchlist

    def test_as_dict(self, manager, fill_watchlist, person_label, person):
        as_dict = manager.as_dict()
        assert person_label in as_dict
        model_watchlist = as_dict[person_label]
        assert len(model_watchlist) == 1
        assert model_watchlist[0]["object_id"] == person.pk
        assert model_watchlist[0]["object_repr"] == str(person)

    def test_prune_models(self, watchlist_model, manager, fill_watchlist, user, person_ct):
        ct = ContentType.objects.create(app_label="foo", model="bar")
        watchlist_model.objects.create(user=user, content_type=ct, object_id=0, object_repr="foo")
        manager._prune_models()
        assert not watchlist_model.objects.filter(content_type=ct).exists()
        assert watchlist_model.objects.filter(content_type=person_ct).exists()

    def test_prune_model_objects(self, manager, fill_watchlist, person_factory, add_to_watchlist, person_watchlist):
        new = person_factory()
        new_pk = new.pk
        add_to_watchlist(new)
        new.delete()
        manager._prune_model_objects()
        assert not person_watchlist.filter(object_id=new_pk).exists()

    def test_get_stale_pks(self, manager, fill_watchlist, person_factory, add_to_watchlist, person_model):
        new = person_factory()
        new_pk = new.pk
        add_to_watchlist(new)
        new.delete()
        assert new_pk in manager._get_stale_pks(person_model)

    def test_bulk_add_list(self, manager, person_factory, person_watchlist):
        new1 = person_factory()
        new2 = person_factory()
        manager.bulk_add([new1, new2])
        assert person_watchlist.filter(object_id=new1.pk)
        assert person_watchlist.filter(object_id=new2.pk)

    def test_bulk_add_queryset(self, manager, person_factory, person_model, person_watchlist):
        new1 = person_factory()
        new2 = person_factory()
        queryset = person_model.objects.filter(pk__in=[new1.pk, new2.pk])
        manager.bulk_add(queryset)
        assert person_watchlist.filter(object_id=new1.pk)
        assert person_watchlist.filter(object_id=new2.pk)

    def test_bulk_add_empty_list(self, manager, django_assert_num_queries):
        with django_assert_num_queries(0):
            manager.bulk_add([])

    def test_bulk_add_empty_queryset(self, manager, django_assert_num_queries, person_model):
        with django_assert_num_queries(0):
            manager.bulk_add(person_model.objects.none())

    def test_bulk_add_skips_existing(self, manager, person_factory, add_to_watchlist, person_watchlist):
        obj = person_factory(id=420)
        add_to_watchlist(obj)
        manager.bulk_add([obj])
        assert person_watchlist.filter(object_id=obj.pk).count() == 1

    def test_remove_model(self, manager, fill_watchlist, person_model, person_watchlist):
        manager.remove_model(person_model)
        assert not person_watchlist.exists()

    def test_filter(self, manager, fill_watchlist, person_factory, person_model, person):
        new1 = person_factory()
        queryset = person_model.objects.all()
        filtered_queryset = manager.filter(queryset)
        assert person in filtered_queryset
        assert new1 not in filtered_queryset
