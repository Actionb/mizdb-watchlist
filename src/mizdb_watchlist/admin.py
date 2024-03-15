from django import forms
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

    # TODO: include the watchlist action
    @property
    def media(self):
        media = super().media
        media += forms.Media(js=["mizdb_watchlist/js/watchlist.js"], css={"all": ["mizdb_watchlist/css/watchlist.css"]})
        return media

    def get_urls(self):
        urls = super().get_urls()
        urls.insert(0, path("_watchlist/", self.admin_site.admin_view(self.watchlist), name="watchlist"))
        return urls

    def watchlist(self, request):
        """View that displays the overview of the user's watchlist items."""
        context = {
            "media": self.media,
            "title": gettext("My watchlist"),
            **self.get_watchlist_context(request),
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/watchlist.html", context)
