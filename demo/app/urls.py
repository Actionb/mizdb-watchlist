from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

from .views import CompanyEditView, CompanyListView, PersonEditView, PersonListView, WatchlistView

app_name = "demo"
urlpatterns = [
    path("", PersonListView.as_view(), name="app_person_changelist"),
    path(
        "person/edit/<int:pk>/",
        PersonEditView.as_view(success_url=reverse_lazy("demo:app_person_changelist")),
        name="app_person_change",
    ),
    path("company/", CompanyListView.as_view(), name="app_company_changelist"),
    path(
        "company/edit/<int:pk>/",
        CompanyEditView.as_view(success_url=reverse_lazy("demo:app_company_changelist")),
        name="app_company_change",
    ),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("login/", LoginView.as_view(next_page="demo:app_person_changelist"), name="login"),
    path("logout/", LogoutView.as_view(next_page="demo:app_person_changelist"), name="logout"),
]
