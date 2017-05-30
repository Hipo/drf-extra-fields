from django.conf.urls import url, include

from rest_framework import routers

from . import viewsets

router = routers.DefaultRouter()
router.register('users', viewsets.ExampleUserViewset)
router.register(
    'no-queryset', viewsets.ExampleNoQuerysetViewset, base_name='no-queryset')

urlpatterns = [url(r'^', include(router.urls))]
