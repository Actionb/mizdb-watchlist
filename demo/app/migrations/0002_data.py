import factory
from django.db import migrations


def forwards_func(apps, schema_editor):
    Person = apps.get_model("app", "Person")

    class PersonFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Person

        first_name = factory.Faker("first_name")
        last_name = factory.Faker("last_name")

    persons = []
    for _ in range(100):
        persons.append(PersonFactory.build())
    Person.objects.bulk_create(persons)


def reverse_func(apps, schema_editor):
    Person = apps.get_model("app", "Person")
    Person.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [migrations.RunPython(forwards_func, reverse_func)]
