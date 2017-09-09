from django.conf.urls import url, include

from rest_framework import routers

from . import viewsets

router = routers.DefaultRouter()
router.register('people', viewsets.ExamplePersonViewset)
router.register(
    'types', viewsets.ExampleTypeFieldViewset, base_name='types')
router.register(
    'wo-model', viewsets.ExampleViewSetWOModel, base_name='wo-model')

urlpatterns = [url(r'^', include(router.urls))]
