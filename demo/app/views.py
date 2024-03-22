from django import forms, views

from mizdb_watchlist.views import ListViewMixin, WatchlistViewMixin

from .models import Company, Person


class PersonListView(ListViewMixin, views.generic.ListView):
    queryset = Person.objects.all()
    template_name = "changelist.html"


class CompanyListView(ListViewMixin, views.generic.ListView):
    queryset = Company.objects.all()
    template_name = "changelist.html"


class PersonEditView(views.generic.UpdateView):
    model = Person
    fields = forms.ALL_FIELDS
    template_name = "edit.html"


class CompanyEditView(views.generic.UpdateView):
    model = Company
    fields = forms.ALL_FIELDS
    template_name = "edit.html"


class WatchlistView(WatchlistViewMixin, views.generic.TemplateView):
    template_name = "watchlist.html"
