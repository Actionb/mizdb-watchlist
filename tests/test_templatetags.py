from unittest.mock import Mock, patch

import pytest

from mizdb_watchlist.templatetags.mizdb_watchlist import toggle_button

pytestmark = [pytest.mark.django_db]


def test_toggle_button(http_request, test_obj):
    result = toggle_button(http_request, test_obj, text="foo", url="bar", on_watchlist=True)
    assert result["object_id"] == test_obj.pk
    assert result["model_label"] == test_obj._meta.label_lower
    assert result["text"] == "foo"
    assert result["toggle_url"] == "bar"
    assert result["on_watchlist"]


@patch("mizdb_watchlist.templatetags.mizdb_watchlist.reverse")
def test_toggle_button_on_watchlist_is_none(http_request, test_obj):
    """
    Assert that toggle_button calls manager.on_watchlist() if 'on_watchlist'
    parameter is None.
    """
    with patch("mizdb_watchlist.templatetags.mizdb_watchlist.get_manager") as get_manager_mock:
        on_watchlist_mock = Mock()
        get_manager_mock.return_value.on_watchlist = on_watchlist_mock
        toggle_button(http_request, test_obj, on_watchlist=None)
        on_watchlist_mock.assert_called_with(test_obj)


@patch("mizdb_watchlist.templatetags.mizdb_watchlist.get_manager")
def test_toggle_button_url_is_none(http_request, test_obj):
    """
    Assert that toggle_button returns the URL for 'watchlist:toggle' if no URL
    was passed in.
    """
    with patch("mizdb_watchlist.templatetags.mizdb_watchlist.reverse") as reverse_mock:
        toggle_button(http_request, test_obj, url=None)
        reverse_mock.assert_called_with("watchlist:toggle")
