# Copied from django-rest-framework/tests/utils.py
from django.core.exceptions import ObjectDoesNotExist


class MockObject(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        for key, val in kwargs.items():
            setattr(self, key, val)


class MockQueryset(object):
    def __init__(self, iterable):
        self.items = iterable

    def get(self, **lookup):
        for item in self.items:
            if all([
                getattr(item, key, None) == value
                for key, value in lookup.items()
            ]):
                return item
        raise ObjectDoesNotExist()
