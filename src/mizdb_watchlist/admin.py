from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext

from mizdb_watchlist.models import Watchlist
from mizdb_watchlist.views import WatchlistViewMixin


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
