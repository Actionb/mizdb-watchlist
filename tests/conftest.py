import pytest
from django.contrib.contenttypes.models import ContentType

from mizdb_watchlist.models import Watchlist
from tests.factories import CompanyFactory, PersonFactory
from tests.testapp.models import Company, Person


def _try_getfixturevalue(request, name):
    """
    Try to return the value of the fixture given by `name`. If `name` is not the
    name of a fixture, return the name itself.
    """
    try:
        return request.getfixturevalue(name)
    except pytest.FixtureLookupError:
        return name


################################################################################
# Model objects
################################################################################


@pytest.fixture
def person_model() -> type[Person]:
    return Person


@pytest.fixture
def person_label() -> str:
    """Return the label_lower of the Person model."""
    return Person._meta.label_lower


@pytest.fixture
def person_factory():
    """Return the factory for the Person model."""
    return PersonFactory


@pytest.fixture
def person(person_factory) -> Person:
    """Create and return a Person instance."""
    return person_factory()


@pytest.fixture
def person_ct():
    """Return the ContentType for the Person model."""
    return ContentType.objects.get_for_model(Person)


@pytest.fixture
def company_factory():
    """Return the factory for the Company model."""
    return CompanyFactory


@pytest.fixture
def company(company_factory) -> Company:
    """Create and return a Company instance."""
    return company_factory()


@pytest.fixture
def watchlist_model():
    return Watchlist


@pytest.fixture
def fill_watchlist(add_to_watchlist, person, company):
    """Add the object returned by the `test_obj` fixture to the model watchlist."""
    add_to_watchlist(person)
    add_to_watchlist(company)


@pytest.fixture
def add_to_watchlist(watchlist_model, user):
    """Create a Watchlist model object for the given model object."""

    def inner(obj):
        return watchlist_model.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            object_repr=str(obj),
        )

    return inner


################################################################################
# USER
################################################################################


@pytest.fixture
def user(admin_user):
    """The default user."""
    return admin_user


@pytest.fixture
def login_user(client, user):
    """Log in the default user."""
    client.force_login(user)


################################################################################
# REQUESTS
################################################################################


@pytest.fixture
def http_request(rf, request, path, request_method, request_data, user):
    """
    Return an HTTP request from the Django RequestFactory.

    By default, this returns a GET request on path "/".

    Sets the `user` attribute on the request to replicate the effects of the
    AuthenticationMiddleware. By default, the user will be a superuser.

    To override the defaults, use test method parametrization:

        @pytest.mark.parametrize("path", ["/foo/bar/"])
        @pytest.mark.parametrize("request_method", ["POST"])
        @pytest.mark.parametrize("request_data", [{"foo": "bar"}])
        def test(http_request, request_data, request_method, path):
            assert http_request.method == "POST"
            assert http_request.POST == {"foo": "bar"}

    To override the user, either parametrize with the name of the fixture that
    provides the user:

        @pytest.fixture
        def my_user():
            return "Alice"

        @pytest.mark.parametrize("user", ["my_user"])
        def test_user(http_request, user):
            assert http_request.user == "Alice"

    Or pass the user directly:

        @pytest.mark.parametrize("user", [AnonymousUser()])
        def test(...): ...
    """
    if isinstance(user, str):
        user = _try_getfixturevalue(request, user)
    request = getattr(rf, request_method.lower())(path, data=request_data)
    request.user = user
    return request


@pytest.fixture
def ignore_csrf_protection(http_request):
    """Disable CSRF checks on the given request."""
    http_request.csrf_processing_done = True
    return http_request


@pytest.fixture
def path() -> str:
    """
    The default request path.

    Overwrite with test method parametrization:

        @pytest.mark.parametrize("path", ["/foo/bar/"])
        def test(...): ...
    """
    return "/"


@pytest.fixture
def request_method() -> str:
    """
    The default request method.

    Overwrite with test method parametrization:

        @pytest.mark.parametrize("request_method", ["POST"])
        def test(...): ...
    """
    return "GET"


@pytest.fixture
def request_data() -> dict:
    """
    The default request data.

    Overwrite with test method parametrization:

        @pytest.mark.parametrize("request_data", [{"foo": "bar"}])
        def test(...): ...
    """
    return {}


@pytest.fixture
def add_session(client, http_request, session_data):
    """
    Add a session to the HTTP request.

    To define the session data, use test method parametrization:

        @pytest.mark.parametrize("session_data", [{"foo": "bar"}])
        def test(http_request, add_session, session_data):
            assert http_request.session["foo"] == "bar"
    """
    session = client.session
    session.flush()
    session.update(session_data)
    http_request.session = session
    return http_request


@pytest.fixture
def session_data() -> dict:
    """
    The default data for the request session.

    Overwrite with test method parametrization:

        @pytest.mark.parametrize("session_data", [{"foo": "bar"}])
        def test(...): ...
    """
    return {}
