from drf_extra_fields import serializer_formats as viewsets

from . import models
from . import serializers


class ExamplePersonViewset(viewsets.UUIDModelViewSet):
    """
    A simple model viewset for testing.
    """

    serializer_class = serializers.ExamplePersonSerializer
    queryset = models.Person.objects

    lookup_field = serializers.ExamplePersonSerializer.Meta.extra_kwargs[
        'related_to']['lookup_field']
    lookup_value_regex = '[0-9a-f-]{36}'


class ExampleTypeFieldViewset(viewsets.UUIDModelViewSet):
    """
    A generic viewset with a type field.
    """

    serializer_class = serializers.ExampleTypeFieldSerializer
