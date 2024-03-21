from django import forms, views

from mizdb_watchlist.manager import get_manager
from mizdb_watchlist.views import ON_WATCHLIST_VAR, WatchlistViewMixin

from .models import Person


class Changelist(views.generic.ListView):
    queryset = Person.objects.all()
    template_name = "changelist.html"

    def get_queryset(self):
        manager = get_manager(self.request)
        queryset = manager.annotate_queryset(super().get_queryset())
        if ON_WATCHLIST_VAR in self.request.GET:
            queryset = manager.filter(queryset)
        return queryset


class EditView(views.generic.UpdateView):
    model = Person
    fields = forms.ALL_FIELDS
    template_name = "edit.html"


class WatchlistView(WatchlistViewMixin, views.generic.TemplateView):
    template_name = "watchlist.html"
