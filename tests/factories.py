import factory

from tests.testapp.models import Company, Person


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    id = factory.Sequence(lambda n: n + 10)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    id = factory.Sequence(lambda n: n + 100)
    name = factory.Faker("company")
