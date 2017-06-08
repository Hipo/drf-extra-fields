from django.conf.urls import url, include

from rest_framework import routers

from . import viewsets

router = routers.DefaultRouter()
router.register('users', viewsets.ExampleUserViewset)
router.register(
    'types', viewsets.ExampleTypeFieldViewset, base_name='types')

urlpatterns = [url(r'^', include(router.urls))]