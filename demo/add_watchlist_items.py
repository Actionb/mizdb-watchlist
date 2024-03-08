import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
django.setup()


class Request:
    pass


def add_watchlist_items():
    from app.models import Person
    from django.contrib.auth import get_user_model

    from mizdb_watchlist.manager import get_manager

    request = Request()
    # Add items to the watchlist model
    request.user = get_user_model().objects.first()
    manager = get_manager(request)
    for p in Person.objects.all()[:5]:
        manager.add(p)


if __name__ == "__main__":
    add_watchlist_items()
