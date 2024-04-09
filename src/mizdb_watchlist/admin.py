from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext

from mizdb_watchlist.models import Watchlist
from mizdb_watchlist.views import WatchlistViewMixin, annotate_view_queryset


@admin.register(Watchlist)
class WatchlistAdmin(WatchlistViewMixin, admin.ModelAdmin):
    list_display = ["object_repr", "object_id", "user", "content_type", "time_added"]
    list_filter = ["user__username", "content_type"]

    def get_urls(self):
        urls = super().get_urls()
        urls.insert(0, path("_watchlist/", self.admin_site.admin_view(self.watchlist), name="watchlist"))
        return urls

    def watchlist(self, request):
        """The overview of the user's watchlist items."""
        context = {
            "media": self.media,
            "title": gettext("My watchlist"),
            **self.get_watchlist_context(request),
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/watchlist.html", context)


class WatchlistMixin:
    """
    A mixin that adds annotations and filtering specific to the watchlist to
    the model admin's queryset.

    If ``ON_WATCHLIST_VAR`` (defaults to: ``on_watchlist``) is present in the
    request GET parameters, the queryset will be filtered to only include
    objects that are currently on the user's watchlist.

    Set ``add_watchlist_annotations`` to ``False`` to skip adding annotations
    and disable filtering.

    Add this mixin to your model admins for models that use the watchlist.
    """

    add_watchlist_annotations = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)  # noqa
        if self.add_watchlist_annotations:
            queryset = annotate_view_queryset(request, queryset)
        return queryset
