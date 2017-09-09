from drf_extra_fields import serializer_formats as viewsets

from . import models
from . import serializers


class ExamplePersonViewset(viewsets.UUIDModelViewSet):
    """
    A simple model viewset for testing.
    """

    serializer_class = serializers.ExamplePersonSerializer
    queryset = models.Person.objects


class ExampleTypeFieldViewset(viewsets.UUIDModelViewSet):
    """
    A generic viewset with a type field.
    """

    serializer_class = serializers.ExampleTypeFieldSerializer
