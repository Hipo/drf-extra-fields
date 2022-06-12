# Copied from django-rest-framework/tests/utils.py
from django.core.exceptions import ObjectDoesNotExist


class MockObject:
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __str__(self):
        kwargs_str = ', '.join([
            f'{key}={value}'
            for key, value in sorted(self._kwargs.items())
        ])
        return '<MockObject %s>' % kwargs_str

    @property
    def foo_property(self):
        return MockQueryset(
            [
                MockObject(pk=3, name="foo"),
                MockObject(pk=1, name="bar"),
                MockObject(pk=2, name="baz"),
            ]
        )

    def foo_function(self):
        return self.foo_property

    @property
    def bar_property(self):
        return MockObject(pk=3, name="foo")


class MockQueryset:
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

    def __iter__(self):
        return MockIterator(self.items)


class MockIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __next__(self):
        if self.index >= len(self.items):
            raise StopIteration

        self.index += 1
        return self.items[self.index - 1]
