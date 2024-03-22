from django.contrib import admin, messages
from django.utils.translation import gettext, gettext_lazy

from mizdb_watchlist.manager import get_manager


@admin.action(description=gettext_lazy("Add selected %(verbose_name_plural)s to my watchlist"))
def add_to_watchlist(_view, request, queryset):
    """Add the items in the given queryset to the watchlist."""
    # Reminder: ModelAdmin calls this with these positional arguments:
    #   model_admin_instance, request, queryset
    manager = get_manager(request)
    manager.bulk_add(queryset)
    messages.add_message(request, level=messages.INFO, message=gettext("Successfully added to my watchlist."))
    return None
