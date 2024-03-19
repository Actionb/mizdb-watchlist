from collections import OrderedDict

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import NoReverseMatch, reverse
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import ContextMixin

from mizdb_watchlist.manager import get_manager


def _get_model_object(model_label, pk):
    model = apps.get_model(model_label)
    return model.objects.get(pk=pk)


class WatchlistViewMixin(ContextMixin):
    """A view mixin that adds template context items for displaying the watchlist."""

    def get_url_namespace(self, request):
        """Return the namespace of the given request."""
        return request.resolver_match.namespace

    def get_object_url(self, request, model, pk):
        """
        Return the URL to the change page of the object described by the given
        model and primary key.
        """
        opts = model._meta
        viewname = f"{opts.app_label}_{opts.model_name}_change"
        namespace = self.get_url_namespace(request)
        if namespace:
            viewname = f"{namespace}:{viewname}"
        return reverse(viewname, args=[pk])

    def get_remove_url(self):
        """Return the URL for the view that removes items from the watchlist."""
        return reverse("watchlist:remove")

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
                watchlist[model._meta.verbose_name.capitalize()] = model_items
        context["watchlist"] = OrderedDict(sorted(watchlist.items()))
        context["remove_url"] = self.get_remove_url()
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_watchlist_context(self.request))  # noqa
        return context


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
