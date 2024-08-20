import os
import re
from operator import itemgetter

import pytest
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse
from playwright.sync_api import expect

# https://github.com/microsoft/playwright-python/issues/439
# https://github.com/microsoft/playwright-pytest/issues/29#issuecomment-731515676
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def session_login(login_user, client, context):
    """
    Log in a user and add the session cookie for the logged-in user to the
    current context.
    """
    auth_cookie = client.cookies["sessionid"]
    pw_cookie = {
        "name": auth_cookie.key,
        "value": auth_cookie.value,
        "path": auth_cookie["path"],
        "domain": auth_cookie["domain"] or "localhost",
    }
    context.add_cookies([pw_cookie])


@pytest.fixture
def get_url(live_server):
    """Return the URL for a given view name on the current live server."""

    def inner(view_name, **reverse_kwargs):
        return live_server.url + reverse(view_name, **reverse_kwargs)

    return inner


################################################################################
# WATCHLIST
################################################################################


@pytest.fixture
def on_watchlist_model(watchlist_model):
    """Return whether the given object is on the model watchlist."""

    def inner(obj):
        return watchlist_model.objects.filter(
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        ).exists()

    return inner


@pytest.fixture
def get_session_cookie(context):
    """Return the cookie with the session id."""

    def inner():
        try:
            return next(c for c in context.cookies() if c["name"] == "sessionid")
        except StopIteration:
            raise Exception("No session cookie!")

    return inner


@pytest.fixture
def get_session(get_session_cookie):
    """Return the SessionStore object for the current request session."""

    def inner():
        return SessionStore(session_key=get_session_cookie()["value"])

    return inner


@pytest.fixture
def on_watchlist_session(get_session):
    """Return whether the given object is on the session watchlist."""

    def inner(obj):
        try:
            watchlist = get_session()["watchlist"][obj._meta.label_lower]
        except KeyError:
            return False
        return obj.pk in list(map(itemgetter("object_id"), watchlist))

    return inner


@pytest.fixture
def on_watchlist(logged_in, on_watchlist_session, on_watchlist_model):
    """
    Return whether the given model object is on either the model or the session
    watchlist, depending on value of the `logged_in` fixture.

    Declare the `logged_in` value with test method parametrization:

        @pytest.mark.parametrize("logged_in", [True, False])
        def test(on_watchlist, ...): ...
    """

    def inner(obj):
        if logged_in:
            return on_watchlist_model(obj)
        else:
            return on_watchlist_session(obj)

    return inner


################################################################################
# TOGGLE BUTTON
################################################################################


@pytest.fixture
def get_toggle_button():
    def inner(locator):
        return locator.locator(".watchlist-toggle-btn")

    return inner


@pytest.fixture
def assert_toggled_on():
    """
    Assert that the given toggle button has the CSS classes to display it as
    toggled on.
    """

    def inner(toggle_button):
        expect(toggle_button).to_have_class(re.compile("on-watchlist"))

    return inner


@pytest.fixture
def assert_toggled_off():
    """
    Assert that the given toggle button has the CSS classes to display it as
    toggled off.
    """

    def inner(toggle_button):
        expect(toggle_button).not_to_have_class(re.compile("on-watchlist"))

    return inner


################################################################################
# LOCATORS
################################################################################


@pytest.fixture
def get_remove_button():
    def inner(locator):
        return locator.locator(".watchlist-remove-btn")

    return inner


@pytest.fixture
def get_remove_all_button():
    def inner(locator):
        return locator.locator(".watchlist-remove-all-btn")

    return inner


@pytest.fixture
def get_watchlist_link():
    def inner(locator):
        return locator.get_by_role("link", name=re.compile("watchlist", re.IGNORECASE))

    return inner
