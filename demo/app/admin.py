from django.contrib import admin

from mizdb_watchlist.views import ModelAdminMixin

from .models import Person


@admin.register(Person)
class PersonAdmin(ModelAdminMixin, admin.ModelAdmin):
    pass
