from django.urls import path

from mizdb_watchlist.views import watchlist_remove, watchlist_remove_all, watchlist_toggle

app_name = "watchlist"
urlpatterns = [
    path("remove/", watchlist_remove, name="remove"),
    path("remove_all/", watchlist_remove_all, name="remove_all"),
    path("toggle/", watchlist_toggle, name="toggle"),
]
