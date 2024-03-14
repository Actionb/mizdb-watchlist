from collections import OrderedDict

from django import forms
from django.apps import apps
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin

from mizdb_watchlist.manager import get_manager


def _get_model_object(model_label, pk):
    model = apps.get_model(model_label)
    return model.objects.get(pk=pk)


class WatchlistViewMixin(ContextMixin):
    """View for viewing and editing the watchlist of the current user."""

    def get_url_namespace(self):
        return self.request.resolver_match.namespace  # noqa

    def get_object_url(self, model, pk):
        opts = model._meta
        viewname = f"{opts.app_label}_{opts.model_name}_change"
        namespace = self.get_url_namespace()
        if namespace:
            viewname = f"{namespace}:{viewname}"
        return reverse(viewname, args=[pk])

    def get_remove_url(self):
        return reverse("watchlist:remove")

    def get_watchlist(self):
        request = self.request  # noqa
        return get_manager(request).as_dict()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        watchlist = {}
        for model_label, watchlist_items in self.get_watchlist().items():
            try:
                model = apps.get_model(model_label)
            except LookupError:
                continue

            # Add the URL to the change page of each item:
            for watchlist_item in watchlist_items:
                watchlist_item["object_url"] = self.get_object_url(model, watchlist_item["object_id"])
                watchlist_item["model_label"] = model_label

            watchlist[model._meta.verbose_name] = watchlist_items
        context["watchlist"] = OrderedDict(sorted(watchlist.items()))
        context["remove_url"] = self.get_remove_url()
        return context


class AdminWatchlistView(WatchlistViewMixin, TemplateView):
    template_name = "admin/watchlist.html"
    admin_site = admin.sites.site  # TODO: explain that people should set this value to their admin site
    title = gettext_lazy("My watchlist")

    @property
    def media(self):
        return forms.Media(
            js=["mizdb_watchlist/js/watchlist.js"],
            css={"all": ["mizdb_watchlist/css/watchlist.css"]},
        )

    def get_url_namespace(self):
        return self.admin_site.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["media"] = self.media
        context["title"] = self.title
        context.update(self.admin_site.each_context(self.request))
        return context


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
