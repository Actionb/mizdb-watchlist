from django.db import models


class Person(models.Model):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "Persons"
        ordering = ["last_name", "first_name"]


class Company(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name
