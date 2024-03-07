from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    object_repr = models.CharField(max_length=200)
    time_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(gettext_lazy("Additional Notes"), blank=True)

    def __str__(self):
        return f"{self.content_type.name}: {self.object_repr}"  # TODO: just use object_repr?

    class Meta:
        ordering = ["user", "content_type", "time_added"]
        verbose_name = gettext_lazy("Watchlist")
        verbose_name_plural = gettext_lazy("Watchlists")
