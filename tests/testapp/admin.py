from django.contrib import admin

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    change_form_template = "admin/change_form_with_watchlist.html"
