from django.contrib import admin

from mizdb_watchlist.actions import add_to_watchlist
from mizdb_watchlist.views import ModelAdminMixin

from .models import Company, Person

admin.site.add_action(add_to_watchlist)


@admin.register(Person)
class PersonAdmin(ModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Company)
class CompanyAdmin(ModelAdminMixin, admin.ModelAdmin):
    pass
