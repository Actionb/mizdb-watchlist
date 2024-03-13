from django import forms, views

from mizdb_watchlist.manager import get_manager
from mizdb_watchlist.views import WatchlistViewMixin

from .models import Person


class Changelist(views.generic.ListView):
    queryset = Person.objects.all()
    template_name = "changelist.html"

    def get_queryset(self):
        return get_manager(self.request).annotate_queryset(super().get_queryset())


class EditView(views.generic.UpdateView):
    model = Person
    fields = forms.ALL_FIELDS
    template_name = "edit.html"


class WatchlistView(WatchlistViewMixin, views.generic.TemplateView):
    template_name = "watchlist.html"
