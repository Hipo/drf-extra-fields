from django.contrib.auth import models as auth_models

from rest_framework import viewsets


class ExampleUserViewset(viewsets.ModelViewSet):
    """
    A simple model viewset for testing.
    """

    queryset = auth_models.User.objects
