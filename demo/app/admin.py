from django.contrib import admin

from mizdb_watchlist.actions import add_to_watchlist

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    actions = [add_to_watchlist]
