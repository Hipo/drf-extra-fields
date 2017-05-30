from django.contrib.auth import models as auth_models

from rest_framework import viewsets

from . import serializers


class ExampleUserViewset(viewsets.ModelViewSet):
    """
    A simple model viewset for testing.
    """

    serializer_class = serializers.ExampleUserSerializer
    queryset = auth_models.User.objects


class ExampleNoQuerysetViewset(viewsets.ModelViewSet):
    """
    A viewset without a queryset for testing.
    """

    serializer_class = serializers.ExampleChildSerializer
