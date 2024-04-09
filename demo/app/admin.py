from django.contrib import admin

from mizdb_watchlist.actions import add_to_watchlist
from mizdb_watchlist.admin import WatchlistMixin

from .models import Company, Person

admin.site.add_action(add_to_watchlist)


@admin.register(Person)
class PersonAdmin(WatchlistMixin, admin.ModelAdmin):
    pass


@admin.register(Company)
class CompanyAdmin(WatchlistMixin, admin.ModelAdmin):
    pass
