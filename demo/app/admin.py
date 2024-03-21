from django.contrib import admin

from mizdb_watchlist.actions import add_to_watchlist
from mizdb_watchlist.manager import get_manager
from mizdb_watchlist.views import ON_WATCHLIST_VAR

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    actions = [add_to_watchlist]

    def get_queryset(self, request):
        manager = get_manager(request)
        queryset = manager.annotate_queryset(super().get_queryset(request))
        if ON_WATCHLIST_VAR in request.GET:
            queryset = manager.filter(queryset)
        return queryset
