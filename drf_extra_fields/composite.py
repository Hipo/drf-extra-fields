"""
Composite fields that support calling `save()` on the child.
"""

import collections

from django.utils import six

from rest_framework.utils import html
from rest_framework.utils import serializer_helpers
from rest_framework import serializers


def clone_serializer(serializer, parent=None, **kwargs):
    """
    Reconstitute a new serializer from an existing one.
    """
    kwargs = dict(serializer._kwargs, **kwargs)
    if 'child' in kwargs:
        kwargs['child'] = clone_serializer(serializer.child)

    clone = type(serializer)(*serializer._args, **kwargs)

    # Copy over the DRF bits the clone will need
    if parent is not None:
        clone.bind(parent.field_name or type(parent).__name__, parent)

    # Set up any non-DRF, clone-specific references
    clone.original = serializer
    if hasattr(serializer, 'clone_meta'):
        clone.clone_meta = serializer.clone_meta

    return clone


class SerializerCompositeField(serializers.Field):
    """
    A composite field that supports full use of the child serializer:

    e.g. `save()`.
    """

    def clone_child(self, child, **kwargs):
        """
        Reconstitute a new child from the existing one.
        """
        kwargs.setdefault('context', self.context)
        return clone_serializer(child, self, **kwargs)


class SerializerListField(serializers.ListField, SerializerCompositeField):
    """
    A list field that supports full use of the child serializer:

    e.g. `save()`.
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

        value = serializer_helpers.ReturnList([], serializer=self)
        for child_data in data:
            clone = self.clone_child(self.child, data=child_data)
            clone.is_valid(raise_exception=True)
            child_value = clone.validated_data
            if not (child_value is None or isinstance(
                    child_value, serializer_helpers.ReturnDict)):
                child_value = serializer_helpers.ReturnDict(
                    child_value, serializer=clone)
            value.append(child_value)
        return value

    def to_representation(self, value):
        """
        Use the reconstituted child to serialize the value.
        """
        data = serializer_helpers.ReturnList([], serializer=self)
        for child_value in value:
            if child_value is None:
                data.append(None)
            else:
                if isinstance(child_value, serializer_helpers.ReturnDict):
                    child_data = child_value.serializer.data
                else:
                    clone = self.clone_child(self.child, instance=child_value)
                    child_data = serializer_helpers.ReturnDict(
                        clone.data, serializer=clone)
                data.append(child_data)
        return data


class SerializerDictField(serializers.DictField, SerializerCompositeField):
    """
    A dict field that supports full use of the child serializer:

    e.g. `save()`.
    """

    def clone_child(self, key, child, **kwargs):
        """
        Dictionary specific child lookup.
        """
        return super(SerializerDictField, self).clone_child(child, **kwargs)

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
            clone = self.clone_child(key, self.child, data=child_data)
            clone.is_valid(raise_exception=True)
            child_value = clone.validated_data
            if not (child_value is None or isinstance(
                    child_value, serializer_helpers.ReturnDict)):
                child_value = serializer_helpers.ReturnDict(
                    child_value, serializer=clone)
            value[six.text_type(key)] = child_value
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
                if isinstance(child_value, serializer_helpers.ReturnDict):
                    child_data = child_value.serializer.data
                else:
                    clone = self.clone_child(
                        key, self.child, instance=child_value)
                    child_data = serializer_helpers.ReturnDict(
                        clone.data, serializer=clone)
                data[key] = child_data
        return data
