from django.contrib import admin

from mizdb_watchlist.views import ModelAdminMixin

from .models import Company, Person


@admin.register(Person)
class PersonAdmin(ModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Company)
class CompanyAdmin(ModelAdminMixin, admin.ModelAdmin):
    pass
