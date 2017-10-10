from drf_extra_fields import serializer_formats as viewsets

from . import models
from . import serializers


class ExamplePersonViewset(viewsets.UUIDModelViewSet):
    """
    A simple model viewset for testing.
    """

    serializer_class = serializers.ExamplePersonSerializer
    queryset = models.Person.objects.all()


class OverriddenPersonViewSet(ExamplePersonViewset):
    """
    An example of a view that overrides another.
    """

    serializer_class = serializers.OverriddenPersonSerializer


class ExampleTypeFieldViewset(viewsets.UUIDModelViewSet):
    """
    A generic viewset with a type field.
    """

    serializer_class = serializers.ExampleTypeFieldSerializer


class ExampleViewSetWOModel(viewsets.UUIDModelViewSet):
    """
    A simple viewset without a model.
    """

    serializer_class = serializers.ExampleSerializerWOModel
