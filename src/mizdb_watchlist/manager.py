from operator import itemgetter

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ExpressionWrapper, Q, QuerySet

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
        raise NotImplementedError  # pragma: no cover

    def get_model_watchlist(self, model):
        """Return the watchlist for the given model."""
        return self._get_model_watchlist(model)

    def _get_model_watchlist(self, model):
        raise NotImplementedError  # pragma: no cover

    def on_watchlist(self, obj):
        """Return whether the given model object is on the watchlist."""
        return self._on_watchlist(obj)

    def _on_watchlist(self, obj):
        raise NotImplementedError  # pragma: no cover

    def add(self, obj):
        """Add the given model object to the watchlist."""
        raise NotImplementedError  # pragma: no cover

    def remove(self, obj):
        """Remove the given model object from the watchlist."""
        raise NotImplementedError  # pragma: no cover

    def remove_object_id(self, model_watchlist, object_id):
        """Remove the item with the given object_id from the model watchlist."""
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def pks(self, model_watchlist):
        """Return the primary keys of the items of the given model watchlist."""
        raise NotImplementedError  # pragma: no cover

    def annotate_queryset(self, queryset):
        """
        Add an 'on_watchlist' attribute to each object in the given queryset
        that denotes whether the object is on a watchlist.
        """
        watchlist_pks = self.pks(self.get_model_watchlist(queryset.model))
        expression = ExpressionWrapper(Q(pk__in=watchlist_pks), output_field=models.BooleanField())
        return queryset.annotate(on_watchlist=expression)

    def prune(self):
        """
        Remove watchlist items that reference stale models or stale model
        objects (i.e. objects that have since been deleted).
        """
        self._prune_models()
        self._prune_model_objects()

    def _prune_models(self):
        """Remove watchlist items that reference stale models."""
        raise NotImplementedError  # pragma: no cover

    def _prune_model_objects(self):
        """Remove watchlist items that reference stale model objects."""
        raise NotImplementedError  # pragma: no cover

    def _get_stale_pks(self, model):
        """
        Return the primary keys of stale model objects referenced by watchlist
        items.
        """
        model_watchlist = self.get_model_watchlist(model)
        pks = self.pks(model_watchlist)
        existing = model.objects.filter(pk__in=pks).values_list("pk", flat=True)
        return set(pks) - set(existing)

    def bulk_add(self, objects):
        """Add the objects in `objects` to the watchlist."""
        for obj in objects:
            self.add(obj)

    def remove_model(self, model):
        """Remove all watchlist items of the given model."""
        raise NotImplementedError  # pragma: no cover


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

    def _get_watchlist_label(self, model):
        """Return the label to use for a watchlist for the given model."""
        return model._meta.label_lower

    def _add_model_watchlist(self, model):
        """
        Add a model watchlist for the given model if the current watchlist does
        not already contain one.
        """
        watchlist = self.get_watchlist()
        label = self._get_watchlist_label(model)
        if label not in watchlist:
            watchlist[label] = []

    def _get_model_watchlist(self, model):
        watchlist = self.get_watchlist()
        return watchlist.get(self._get_watchlist_label(model), [])

    def _on_watchlist(self, obj):
        return obj.pk in self.pks(self.get_model_watchlist(obj))

    def add(self, obj):
        if not self.on_watchlist(obj):
            self._add_model_watchlist(obj)
            model_watchlist = self.get_model_watchlist(obj)
            model_watchlist.append({"object_id": obj.pk, "object_repr": str(obj)})
            self.request.session.modified = True

    def remove(self, obj):
        if self.on_watchlist(obj):
            model_watchlist = self.get_model_watchlist(obj)
            self.remove_object_id(model_watchlist, obj.pk)
            if not model_watchlist:
                self.remove_model(obj)
            self.request.session.modified = True

    def remove_object_id(self, model_watchlist, object_id):
        model_watchlist.pop(self.pks(model_watchlist).index(object_id))
        self.request.session.modified = True

    def as_dict(self):
        return self.get_watchlist()  # pragma: no cover

    def pks(self, model_watchlist):
        return list(map(itemgetter("object_id"), model_watchlist))

    def _prune_models(self):
        watchlist = self.get_watchlist()
        for model_label in list(watchlist.keys()):
            try:
                apps.get_model(model_label)
            except LookupError:
                self._remove_model(model_label)

    def _prune_model_objects(self):
        for model_label in self.get_watchlist():
            model = apps.get_model(model_label)
            model_watchlist = self.get_model_watchlist(model)
            pks = self.pks(model_watchlist)
            existing = model.objects.filter(pk__in=pks).values_list("pk", flat=True)
            orphaned = set(pks) - set(existing)
            for orphan_pk in orphaned:
                self.remove_object_id(model_watchlist, orphan_pk)

    def remove_model(self, model):
        self._remove_model(self._get_watchlist_label(model))

    def _remove_model(self, model_label):
        del self.get_watchlist()[model_label]
        self.request.session.modified = True


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
            self._create(obj).save()

    def remove(self, obj):
        self.remove_object_id(self.get_model_watchlist(obj), obj.pk)

    def remove_object_id(self, model_watchlist, object_id):
        model_watchlist.filter(object_id=object_id).delete()

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

    def _prune_models(self):
        watchlist = self.get_watchlist()
        ct_pks = watchlist.values("content_type").order_by("content_type").distinct()
        for content_type in ContentType.objects.filter(pk__in=ct_pks):
            if content_type.model_class() is None:
                watchlist.filter(content_type=content_type).delete()

    def _prune_model_objects(self):
        ct_pks = self.get_watchlist().values("content_type").order_by("content_type").distinct()
        for content_type in ContentType.objects.filter(pk__in=ct_pks):
            model = content_type.model_class()
            model_watchlist = self.get_model_watchlist(model)
            pks = self.pks(model_watchlist)
            existing = model.objects.filter(pk__in=pks).values_list("pk", flat=True)
            orphaned = set(pks) - set(existing)
            model_watchlist.filter(object_id__in=orphaned).delete()

    def _create(self, obj):
        """Create a Watchlist item instance for the given object."""
        return Watchlist(
            user=self.request.user,
            content_type=self.get_content_type(obj),
            object_id=obj.pk,
            object_repr=str(obj),
        )

    def bulk_add(self, objects):
        if not len(objects):
            return
        if isinstance(objects, QuerySet):
            _models = [objects.model]
        else:
            _models = set(obj._meta.model for obj in objects)

        existing = {model: self.get_model_watchlist(model).values_list("object_id", flat=True) for model in _models}
        new = []
        for obj in objects:
            if obj.pk not in existing[obj._meta.model]:
                new.append(self._create(obj))
        Watchlist.objects.bulk_create(new)

    def remove_model(self, model):
        content_type = self.get_content_type(model)
        self.get_watchlist().filter(content_type=content_type).delete()
