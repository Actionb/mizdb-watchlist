from django import template
from django.urls import reverse

from mizdb_watchlist.manager import get_manager

register = template.Library()


@register.inclusion_tag("mizdb_watchlist/toggle_button.html")
def toggle_button(request, obj, text="", url=None, on_watchlist=None):
    """
    Render a watchlist toggle button for the given model object.

    This inclusion tag renders the template for the toggle button.
    The button is used to add or remove the given model object from the user's
    watchlist, depending on whether it is already on the watchlist.

    By default, the button is rendered with an icon only. Use the `text`
    parameter to also include text.

    Args:
        request (HttpRequest): the view's request
        obj (model object): the model object to add or remove
        text (str): the text displayed next to the watchlist/bookmark icon
        url (str): the URL for the view that handles the toggling. If None, the
            URL with the name `watchlist:toggle` will be used.
        on_watchlist (bool): indicates whether the model object is already on
            the user's watchlist. If None, the tag will check the watchlist
            storage. This will generate a database query if the watchlist uses
            the Watchlist model!

    Example:
        In the template for a generic ListView:

        {% for object in object_list %}
            {{ object }}{% toggle_button view.request object text='foobar' %}
        {% endfor %}

    Example:
        To avoid generating a database hit for every button rendered, annotate
        the ListView's queryset:

        # views.py

        def get_queryset(self):
            return get_manager(self.request).annotate_queryset(super().get_queryset())

        # template.html

        {% for object in object_list %}
            {% toggle_button view.request object on_watchlist=object.on_watchlist %}
        {% endfor %}
    """
    if url is None:
        url = reverse("watchlist:toggle")
    if on_watchlist is None:
        on_watchlist = get_manager(request).on_watchlist(obj)
    return {
        "object_id": obj.pk,
        "model_label": obj._meta.label_lower,
        "text": text,
        "toggle_url": url,
        "on_watchlist": on_watchlist,
    }
