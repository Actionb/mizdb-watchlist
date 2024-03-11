from functools import cache
from operator import itemgetter

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ExpressionWrapper, Q

from mizdb_watchlist.models import Watchlist

WATCHLIST_SESSION_KEY = "watchlist"


def get_manager(request):
    """
    Return a watchlist manager for the given request.

    If the user is authenticated, return a ModelManager instance. Otherwise,
    return a SessionManager instance.
    """
    try:
        if request.user.is_authenticated:
            return ModelManager(request)
    except AttributeError:
        # request.user was not set or request.user was None
        pass
    return SessionManager(request)


class BaseManager:
    def __init__(self, request):
        self.request = request

    def get_watchlist(self):
        """Return the watchlist for the current request."""
        raise NotImplementedError

    @cache
    def get_model_watchlist(self, model):
        """Return the watchlist for the given model."""
        return self._get_model_watchlist(model)

    def _get_model_watchlist(self, model):
        raise NotImplementedError

    @cache
    def on_watchlist(self, obj):
        """Return whether the given model object is on the watchlist."""
        return self._on_watchlist(obj)

    def _on_watchlist(self, obj):
        raise NotImplementedError

    def add(self, obj):
        """Add the given model object to the watchlist."""
        raise NotImplementedError

    def remove(self, obj):
        """Remove the given model object from the watchlist."""
        raise NotImplementedError

    def toggle(self, obj):
        """
        Add the given model object to the watchlist, if it is not already on it.
        Otherwise, remove it.
        """
        if self.on_watchlist(obj):
            self.remove(obj)
            return False
        else:
            self.add(obj)
            return True

    def as_dict(self):
        """Return the watchlist as a dictionary."""
        raise NotImplementedError

    def pks(self, model_watchlist):
        """Return the primary keys of the items of the given model watchlist."""
        raise NotImplementedError

    def annotate_queryset(self, queryset):
        """
        Add an 'on_watchlist' attribute to each object in the given queryset
        that denotes whether the object is on a watchlist.
        """
        watchlist_pks = self.pks(self.get_model_watchlist(queryset.model))
        expression = ExpressionWrapper(Q(pk__in=watchlist_pks), output_field=models.BooleanField())
        return queryset.annotate(on_watchlist=expression)


class SessionManager(BaseManager):
    """
    Manager for watchlists stored in local session.

    Watchlist items are stored as dicts in a list under their respective model
    label:
        session[WATCHLIST_SESSION_KEY] = {<model_label>: <model_watchlist>}
        model_watchlist = [{"object_id": 1, "object_repr": "foo"}, ...]
    """

    def get_watchlist(self):
        if WATCHLIST_SESSION_KEY not in self.request.session:
            self.request.session[WATCHLIST_SESSION_KEY] = {}
        return self.request.session[WATCHLIST_SESSION_KEY]

    def _get_model_watchlist(self, model):
        watchlist = self.get_watchlist()
        label = model._meta.label_lower
        # FIXME: this will add the model label to the watchlist even if no
        #  objects are going to be added (f.ex. in remove())
        if label not in watchlist:  # pragma: no cover
            watchlist[label] = []
        return watchlist[label]

    def _on_watchlist(self, obj):
        return obj.pk in self.pks(self.get_model_watchlist(obj))

    def add(self, obj):
        if not self.on_watchlist(obj):
            self.get_model_watchlist(obj).append({"object_id": obj.pk, "object_repr": str(obj)})
            self.request.session.modified = True

    def remove(self, obj):
        if self.on_watchlist(obj):
            model_watchlist = self.get_model_watchlist(obj)
            model_watchlist.pop(self.pks(model_watchlist).index(obj.pk))
            # TODO: remove model watchlist entirely when this was the last item
            self.request.session.modified = True

    def as_dict(self):
        return self.get_watchlist()

    def pks(self, model_watchlist):
        return list(map(itemgetter("object_id"), model_watchlist))


class ModelManager(BaseManager):
    """Manager for watchlists stored via the Watchlist model."""

    def get_watchlist(self):
        return Watchlist.objects.filter(user=self.request.user)

    def _get_model_watchlist(self, model):
        return self.get_watchlist().filter(content_type=self.get_content_type(model))

    def get_content_type(self, model):
        return ContentType.objects.get_for_model(model)

    def _on_watchlist(self, obj):
        return self.get_model_watchlist(obj).filter(object_id=obj.pk).exists()

    def add(self, obj):
        if not self.on_watchlist(obj):
            self.get_model_watchlist(obj).create(
                user=self.request.user,
                content_type=self.get_content_type(obj),
                object_id=obj.pk,
                object_repr=str(obj),
            )

    def remove(self, obj):
        self.get_model_watchlist(obj).filter(object_id=obj.pk).delete()

    def as_dict(self):
        watchlist = self.get_watchlist()
        result = {}
        for ct_id in watchlist.values_list("content_type", flat=True).distinct():
            ct = ContentType.objects.get(pk=ct_id)
            model = ct.model_class()
            model_watchlist = self.get_model_watchlist(model)
            result[model._meta.label_lower] = list(model_watchlist.values("object_id", "object_repr", "notes"))
        return result

    def pks(self, model_watchlist):
        return list(model_watchlist.values_list("object_id", flat=True))
