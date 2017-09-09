from rest_framework import response

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


class ExampleViewSetWOModel(viewsets.UUIDModelViewSet):
    """
    A simple viewset without a model.
    """

    serializer_class = serializers.ExampleSerializerWOModel

    def retrieve(self, request, *args, **kwargs):
        """
        Just return the a new person.
        """
        serializer = self.get_serializer(
            instance=models.Person.objects.create())
        return response.Response(serializer.data)
