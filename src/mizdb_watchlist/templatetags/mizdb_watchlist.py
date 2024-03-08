from django import template
from django.urls import reverse

from mizdb_watchlist.manager import get_manager

register = template.Library()


@register.inclusion_tag("mizdb_watchlist/toggle_button.html")
def toggle_button(request, obj, url=None, on_watchlist=None):
    """Render the watchlist toggle button for the given model object."""
    if url is None:
        url = reverse("watchlist:toggle")
    if on_watchlist is None:
        on_watchlist = get_manager(request).on_watchlist(obj)
    return {"object_id": obj.pk, "model_label": obj._meta.label_lower, "toggle_url": url, "on_watchlist": on_watchlist}
