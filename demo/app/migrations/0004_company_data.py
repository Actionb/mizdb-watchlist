import factory
from django.db import migrations


def forwards_func(apps, schema_editor):
    Company = apps.get_model("app", "Company")

    class CompanyFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Company

        name = factory.Faker("company")

    objects = []
    for _ in range(100):
        objects.append(CompanyFactory.build())
    Company.objects.bulk_create(objects)


def reverse_func(apps, schema_editor):
    Company = apps.get_model("app", "Company")
    Company.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0003_company"),
    ]

    operations = [migrations.RunPython(forwards_func, reverse_func)]
