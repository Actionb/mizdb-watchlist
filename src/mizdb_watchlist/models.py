from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField(verbose_name=_("Object ID"))
    object_repr = models.CharField(max_length=200, verbose_name=_("Object representation"))
    time_added = models.DateTimeField(auto_now_add=True, verbose_name=_("Added at"))
    notes = models.TextField(blank=True, verbose_name=_("Additional Notes"))

    def __str__(self):
        return f"{self.content_type.name}: {self.object_repr}"  # pragma: no cover

    class Meta:
        ordering = ["user", "content_type", "time_added"]
        verbose_name = _("Watchlist Item")
        verbose_name_plural = _("Watchlist Items")
