"""
Composite fields that support calling `save()` on the child.
"""

import collections

from django.utils import six

from rest_framework.utils import html
from rest_framework import serializers


class SerializerChildValueWrapper(collections.Mapping):
    """
    Wrap a value mapping with the child accessible.
    """
    child = None


class SerializerCompositeField(serializers.Field):
    """
    A composite field that support calling `save()` on the child.
    """

    def make_child(self, **kwargs):
        """
        Reconstitute a new child from the existing one.
        """
        child = type(self.child)(context=self.context, **kwargs)
        child.bind(self.field_name or type(self).__name__, self)
        if hasattr(self.child, 'child'):
            child.child = self.child.child
        self.child = child
        return child

    def wrap_value(self, child, value=None):
        """
        Wrap the value mapping and set the child.
        """
        if value is None:
            value = child.validated_data
        assert isinstance(value, collections.Mapping), (
            'Child validation must return a dict-like object')

        class ChildValueWrapper(
                type(value), SerializerChildValueWrapper):
            """
            Wrap a value mapping with the child accessible.
            """
            pass

        kwargs = {}
        if hasattr(value, 'serializer'):
            kwargs['serializer'] = value.serializer
        wrapped = ChildValueWrapper(value, **kwargs)
        wrapped.child = child
        return wrapped


class SerializerListField(serializers.ListField, SerializerCompositeField):
    """
    A list field that support calling `save()` on the child.
    """

    def to_internal_value(self, data):
        """
        Reconstitute the child serializer and run validation.
        """
        if html.is_html_input(data):
            data = html.parse_html_list(data)
        if (
                isinstance(data, type('')) or
                isinstance(data, collections.Mapping) or
                not hasattr(data, '__iter__')):
            self.fail('not_a_list', input_type=type(data).__name__)
        if not self.allow_empty and len(data) == 0:
            self.fail('empty')

        value = []
        for child_data in data:
            child = self.make_child(data=child_data)
            child.is_valid(raise_exception=True)
            value.append(self.wrap_value(child))
        return value

    def to_representation(self, value):
        """
        Use the reconstituted child to serialize the value.
        """
        data = []
        for child_value in value:
            if child_value is None:
                data.append(None)
            else:
                if isinstance(value, SerializerChildValueWrapper):
                    child_data = child_value.child.data
                else:
                    child = self.make_child(instance=child_value)
                    child_data = self.wrap_value(child, child.data)
                data.append(child_data)
        return data


class SerializerDictField(serializers.DictField, SerializerCompositeField):
    """
    A dict field that support calling `save()` on the child.
    """

    def make_child(self, key, **kwargs):
        """
        Dictionary specific child lookup.
        """
        return super(SerializerDictField, self).make_child(**kwargs)

    def to_internal_value(self, data):
        """
        Reconstitute the child serializer and run validation.
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)

        value = {}
        for key, child_data in data.items():
            child = self.make_child(key, data=child_data)
            child.is_valid(raise_exception=True)
            value[six.text_type(key)] = self.wrap_value(child)
        return value

    def to_representation(self, value):
        """
        Use the reconstituted child to serialize the value.
        """
        data = {}
        for key, child_value in value.items():
            key = six.text_type(key)
            if child_value is None:
                data[key] = None
            else:
                if isinstance(value, SerializerChildValueWrapper):
                    child_data = child_value.child.data
                else:
                    child = self.make_child(key, instance=child_value)
                    child_data = self.wrap_value(child, child.data)
                data[key] = child_data
        return data
