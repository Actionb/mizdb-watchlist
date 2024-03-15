from django.urls import path

from mizdb_watchlist.views import watchlist_remove, watchlist_toggle

app_name = "watchlist"
urlpatterns = [
    path("remove/", watchlist_remove, name="remove"),
    path("toggle/", watchlist_toggle, name="toggle"),
]
