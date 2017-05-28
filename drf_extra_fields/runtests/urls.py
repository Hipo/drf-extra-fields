from django.conf.urls import url, include

from rest_framework import routers

from . import viewsets

router = routers.DefaultRouter()
router.register('users', viewsets.ExampleUserViewset)

urlpatterns = [url(r'^', include(router.urls))]
