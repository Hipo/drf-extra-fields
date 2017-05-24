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
    clone = type(serializer)(**kwargs)

    # Copy over the DRF bits the clone will need
    if parent is not None:
        clone.bind(parent.field_name or type(parent).__name__, parent)
    if hasattr(serializer, 'child'):
        clone.child = serializer.child

    # Set up any non-DRF, clone-specific references
    clone.original = serializer
    if hasattr(serializer, 'clone_meta'):
        clone.clone_meta = serializer.clone_meta

    return clone


class CloneReturnDict(serializer_helpers.ReturnDict):
    """
    Wrap a data mapping with the cloned serializer accessible.
    """

    def __init__(self, data, clone, **kwargs):
        """
        Capture clone and original mapping references.
        """
        self.clone = clone
        self.data = data
        kwargs.setdefault('serializer', getattr(data, 'serializer', None))
        super(CloneReturnDict, self).__init__(data, **kwargs)

    def copy(self):
        """
        Pass along captured references.
        """
        return CloneReturnDict(
            self.data, clone=self.clone, serializer=self.serializer)


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

        value = []
        for child_data in data:
            clone = self.clone_child(self.child, data=child_data)
            clone.is_valid(raise_exception=True)
            value.append(CloneReturnDict(clone.validated_data, clone))
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
                if isinstance(value, CloneReturnDict):
                    child_data = child_value.child.data
                else:
                    clone = self.clone_child(self.child, instance=child_value)
                    child_data = CloneReturnDict(clone.data, clone)
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
            value[six.text_type(key)] = CloneReturnDict(
                clone.validated_data, clone)
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
                if isinstance(value, CloneReturnDict):
                    child_data = child_value.child.data
                else:
                    clone = self.clone_child(
                        key, self.child, instance=child_value)
                    child_data = CloneReturnDict(clone.data, clone)
                data[key] = child_data
        return data
