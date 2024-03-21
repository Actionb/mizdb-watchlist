from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

from .views import Changelist, EditView, WatchlistView

app_name = "demo"
urlpatterns = [
    path("", Changelist.as_view(), name="app_person_changelist"),
    path(
        "edit/<int:pk>/",
        EditView.as_view(success_url=reverse_lazy("demo:app_person_changelist")),
        name="app_person_change",
    ),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("login/", LoginView.as_view(next_page="demo:app_person_changelist"), name="login"),
    path("logout/", LogoutView.as_view(next_page="demo:app_person_changelist"), name="logout"),
]
