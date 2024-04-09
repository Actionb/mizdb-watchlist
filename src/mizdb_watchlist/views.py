from collections import OrderedDict

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import NoReverseMatch, reverse
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import ContextMixin

from mizdb_watchlist.manager import ANNOTATION_FIELD, get_manager

ON_WATCHLIST_VAR = ANNOTATION_FIELD


def _get_model_object(model_label, pk):
    model = apps.get_model(model_label)
    return model.objects.get(pk=pk)


class WatchlistViewMixin(ContextMixin):
    """A view mixin that adds template context items for displaying the watchlist."""

    def get_watchlist(self, request, prune=True):
        """Return the watchlist in dictionary form for the given request."""
        manager = get_manager(request)
        if prune:
            manager.prune()
        return manager.as_dict()

    def get_watchlist_context(self, request):
        """Return template context items for display the watchlist."""
        context = {}
        watchlist = {}
        for model_label, watchlist_items in self.get_watchlist(request).items():
            model_items = []
            try:
                model = apps.get_model(model_label)
            except LookupError:
                continue

            # Add the URL to the change page of each item:
            for watchlist_item in watchlist_items:
                try:
                    watchlist_item["object_url"] = self.get_object_url(request, model, watchlist_item["object_id"])
                except NoReverseMatch:
                    continue
                watchlist_item["model_label"] = model_label
                model_items.append(watchlist_item)

            if model_items:
                if changelist_url := self.get_changelist_url(request, model):
                    changelist_url = f"{self.get_changelist_url(request, model)}?{ON_WATCHLIST_VAR}=True"
                data = {"model_items": model_items, "changelist_url": changelist_url, "model_label": model_label}
                watchlist[model._meta.verbose_name.capitalize()] = data
        context["watchlist"] = OrderedDict(sorted(watchlist.items()))
        return context

    def _get_url_for_watchlist_link(self, request, viewname, args=None, kwargs=None):
        if app_name := request.resolver_match.app_name:
            viewname = f"{app_name}:{viewname}"
        try:
            return reverse(viewname, args=args, kwargs=kwargs, current_app=request.resolver_match.namespace)
        except NoReverseMatch:
            # Fail silently if the name cannot be reversed. The template will
            # then simply not render any links.
            return ""

    def get_object_url(self, request, model, pk):
        """
        Return the URL to the change page of the object described by the given
        model and primary key.
        """
        viewname = f"{model._meta.app_label}_{model._meta.model_name}_change"
        return self._get_url_for_watchlist_link(request, viewname, args=[pk])

    def get_changelist_url(self, request, model):
        """Return the URL to the changelist of the given model."""
        viewname = f"{model._meta.app_label}_{model._meta.model_name}_changelist"
        return self._get_url_for_watchlist_link(request, viewname)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_watchlist_context(self.request))  # noqa
        return context


def annotate_view_queryset(request, queryset):
    """
    Add an 'on_watchlist' attribute to each object in the given queryset that
    denotes whether the object is on a watchlist. If ``ON_WATCHLIST_VAR`` is
    present in the request GET parameters, filter the queryset to only include
    items that are on the watchlist.
    """
    manager = get_manager(request)
    queryset = manager.annotate_queryset(queryset)
    if ON_WATCHLIST_VAR in request.GET:
        queryset = manager.filter(queryset)
    return queryset


class WatchlistMixin:
    """
    A mixin that adds annotations and filtering specific to the watchlist to
    the view's queryset.

    If ``ON_WATCHLIST_VAR`` (defaults to: ``on_watchlist``) is present in the
    request GET parameters, the queryset will be filtered to only include
    objects that are currently on the user's watchlist.

    Set ``add_watchlist_annotations`` to ``False`` to skip adding annotations
    and disable filtering.

    Add this mixin to your list views for models that use the watchlist.
    """

    add_watchlist_annotations = True

    def get_queryset(self):
        queryset = super().get_queryset()  # noqa
        if self.add_watchlist_annotations:
            queryset = annotate_view_queryset(self.request, queryset)  # noqa
        return queryset


@csrf_protect
def watchlist_toggle(request):
    """
    Add an object to the watchlist, or remove an object if it already exists on
    the watchlist.

    Used on the change pages of objects.
    """
    try:
        pk = int(request.POST["object_id"])
        model_label = request.POST["model_label"]
    except (KeyError, ValueError):
        return HttpResponseBadRequest()
    try:
        obj = _get_model_object(model_label, pk)
    except (LookupError, ObjectDoesNotExist):
        on_watchlist = False
    else:
        manager = get_manager(request)
        on_watchlist = manager.toggle(obj)
    return JsonResponse({"on_watchlist": on_watchlist})


@csrf_protect
def watchlist_remove(request):
    """
    Remove an object from the watchlist.

    Used on the watchlist overview to remove items.
    """
    try:
        pk = int(request.POST["object_id"])
        model_label = request.POST["model_label"]
    except (KeyError, ValueError):
        return HttpResponseBadRequest()
    try:
        manager = get_manager(request)
        manager.remove(_get_model_object(model_label, pk))
    except (LookupError, ObjectDoesNotExist):
        pass
    return HttpResponse()


@csrf_protect
def watchlist_remove_all(request):
    """Remove all objects of a given model from the watchlist."""
    try:
        model = apps.get_model(request.POST["model_label"])
    except (KeyError, LookupError):
        return HttpResponseBadRequest()
    get_manager(request).remove_model(model)
    return HttpResponse()
