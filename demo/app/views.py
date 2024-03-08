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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        print(ctx.keys())
        return ctx


class WatchlistView(WatchlistViewMixin, views.generic.TemplateView):
    template_name = "watchlist.html"
