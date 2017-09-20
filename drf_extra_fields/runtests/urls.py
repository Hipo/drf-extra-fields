from django.conf.urls import url, include

from rest_framework import routers

from . import viewsets

router = routers.DefaultRouter()
router.register('people', viewsets.ExamplePersonViewset)
router.register(
    'types', viewsets.ExampleTypeFieldViewset, base_name='types')
router.register(
    'wo-model', viewsets.ExampleViewSetWOModel, base_name='wo-model')

override_router = routers.DefaultRouter()
override_router.register('people', viewsets.OverriddenPersonViewSet)

urlpatterns = [
    url(r'^', include(override_router.urls)),
    url(r'^', include(router.urls)),
]
