from django.contrib import admin

from mizdb_watchlist.models import Watchlist


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ["object_repr", "object_id", "user", "content_type", "time_added"]
    list_filter = ["user__username", "content_type"]
    # TODO: include the watchlist action
