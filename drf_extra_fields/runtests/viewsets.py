from rest_framework import viewsets

from . import models
from . import serializers


class ExamplePersonViewset(viewsets.ModelViewSet):
    """
    A simple model viewset for testing.
    """

    serializer_class = serializers.ExamplePersonSerializer
    queryset = models.Person.objects


class ExampleTypeFieldViewset(viewsets.ModelViewSet):
    """
    A generic viewset with a type field.
    """

    serializer_class = serializers.ExampleTypeFieldSerializer
