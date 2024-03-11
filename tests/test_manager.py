from operator import itemgetter

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from mizdb_watchlist.manager import WATCHLIST_SESSION_KEY, ModelManager, SessionManager, get_manager
from mizdb_watchlist.models import Watchlist
from tests.factories import PersonFactory
from tests.testapp.models import Person

pytestmark = pytest.mark.django_db


@pytest.fixture
def model():
    return Person


@pytest.fixture
def test_obj():
    return PersonFactory()


@pytest.fixture
def user():
    return get_user_model().objects.create_superuser(
        username="superuser", password="foobar", email="testtest@test.test"
    )


@pytest.fixture
def session_watchlist(test_obj):
    """Default session watchlist. Overwrite with test method parametrization."""
    return [{"object_id": test_obj.pk, "object_repr": str(test_obj)}]


@pytest.fixture
def get_request(client, user, model, session_watchlist):
    request = RequestFactory().get("")
    request.user = user
    session = client.session
    session.flush()
    if session_watchlist:
        session[WATCHLIST_SESSION_KEY] = {}
        session[WATCHLIST_SESSION_KEY][model._meta.label_lower] = session_watchlist
    request.session = session
    return request


@pytest.fixture
def manager(manager_class, get_request):
    return manager_class(get_request)


@pytest.fixture
def session_pks(model):
    """Return a list of all primary keys in the session watchlist."""

    def inner(request):
        return list(
            map(itemgetter("object_id"), request.session[WATCHLIST_SESSION_KEY].get(model._meta.label_lower, []))
        )

    return inner


@pytest.mark.parametrize("user", [AnonymousUser()])
def test_get_manager_anonymous_user(get_request, user):
    """
    Assert that get_manager returns a SessionManager for requests made by
    unauthenticated users.
    """
    assert isinstance(get_manager(get_request), SessionManager)


@pytest.mark.parametrize("user", [None])
def test_get_manager_user_not_set(get_request, user):
    """
    Assert that get_manager returns a SessionManager for requests where the
    user attribute is not set.
    """
    assert isinstance(get_manager(get_request), SessionManager)


def test_get_manager_authenticated_user(get_request, user):
    """
    Assert that get_manager returns a ModelManager for requests made by
    authenticated users.
    """
    assert isinstance(get_manager(get_request), ModelManager)


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
    def test_add(self, manager, get_request, test_obj, session_pks, session_watchlist):
        manager.add(test_obj)
        assert test_obj.pk in session_pks(get_request)

    def test_add_already_on_watchlist(self, manager, get_request, test_obj, session_pks):
        manager.add(test_obj)
        assert session_pks(get_request).count(test_obj.pk) == 1

    def test_remove(self, manager, get_request, test_obj, session_pks):
        manager.remove(test_obj)
        assert test_obj.pk not in session_pks(get_request)

    def test_removing_last_item_removes_model_watchlist(self, manager, get_request, test_obj, session_pks):
        """
        Assert that removing the last item of a model watchlist also removes
        the model label key from the global watchlist.
        """
        manager.remove(test_obj)
        label = manager._get_watchlist_label(test_obj)
        assert label not in manager.get_watchlist()


@pytest.fixture
def watchlist_model():
    return Watchlist


@pytest.fixture
def add_to_watchlist(watchlist_model, user, test_obj):
    return watchlist_model.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(test_obj),
        object_id=test_obj.pk,
        object_repr=repr(test_obj),
    )


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
