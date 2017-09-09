"""
Composite fields that support calling `save()` on the child.
"""

import copy

from django.utils import functional

from rest_framework.utils import serializer_helpers
from rest_framework import serializers


def clone_serializer(serializer, parent=None, **kwargs):
    """
    Reconstitute a new serializer from an existing one.
    """
    kwargs = dict(serializer._kwargs, **kwargs)
    if 'child' in kwargs:
        kwargs['child'] = clone_serializer(kwargs['child'])
    elif getattr(serializer, 'child', None) is not None:
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


class ParentField(serializers.Field):
    """
    Common support for fields/serializers with a child field.
    """

    child = None

    def __init__(self, *args, **kwargs):
        """
        Capture and bind the child field/serializer.
        """
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        super(ParentField, self).__init__(*args, **kwargs)
        if self.child is not None:
            # Support runtime child lookup
            self.child.bind(field_name='', parent=self)


class Cloner(object):
    """
    Common support for cloning a child field.
    """

    def clone_child(self, child, **kwargs):
        """
        Reconstitute a new child from the existing one.
        """
        kwargs.setdefault('context', self.context)
        return clone_serializer(child, self, **kwargs)


class CloningField(ParentField, serializers.Field, Cloner):
    """
    Clone the child field and delegate to it.
    """

    def run_validation(self, data=serializers.empty):
        """
        Clone the child, delegate to it, and wrap with a clone reference.
        """
        clone = self.clone_child(self.child, data=data)
        clone.is_valid(raise_exception=True)
        value = clone.validated_data
        if not (value is None or isinstance(
                value, serializer_helpers.ReturnDict)):
            value = serializer_helpers.ReturnDict(value, serializer=clone)
        return value

    def to_representation(self, value):
        """
        Clone the child, delegate to it, and wrap with a clone reference.
        """
        if isinstance(value, serializer_helpers.ReturnDict):
            data = value.serializer.data
        else:
            clone = self.clone_child(self.child, instance=value)
            data = serializer_helpers.ReturnDict(clone.data, serializer=clone)
        return data


class SerializerCompositeField(object):
    """
    A composite field that supports full use of the child:

    e.g. `save()`.
    """

    child = None

    def __init__(self, *args, **kwargs):
        """
        Use an intermediate field to wrap the child at runtime.
        """
        kwargs['child'] = CloningField(
            child=kwargs.pop('child', copy.deepcopy(self.child)))
        super(SerializerCompositeField, self).__init__(*args, **kwargs)


class SerializerListField(SerializerCompositeField, serializers.ListField):
    """
    A list field that supports full use of the child:

    e.g. `save()`.
    """


class SerializerDictField(SerializerCompositeField, serializers.DictField):
    """
    A dict field that supports full use of the child serializer:

    e.g. `save()`.
    """


class CompositeSerializer(serializers.Serializer, ParentField, Cloner):
    """
    Process our schema, then delegate the rest to the child serializer.
    """

    primary = True

    def __init__(self, *args, **kwargs):
        """
        Accept an argument specifying whether this serializer is primary.

        As opposed to a related serializer, or otherwise one that shouldn't
        use the view's serializer.
        """
        primary = kwargs.pop('primary', None)
        # Preserve class default if not given
        if primary is not None:
            self.primary = primary
        super(CompositeSerializer, self).__init__(*args, **kwargs)

    def get_view_serializer(self, *args, **kwargs):
        """
        Get the serializer from the view if we're the primary serializer.
        """
        view = self.context.get('view')
        if self.primary and hasattr(view, 'get_serializer'):
            serializer_class = view.serializer_class
            kwargs['context'] = view.get_serializer_context()
            return serializer_class(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        """
        Return a clone of the child if present, or from the view.
        """
        if self.child is not None:
            return self.clone_child(self.child, *args, **kwargs)

        return self.get_view_serializer(*args, **kwargs)

    @functional.cached_property
    def field_source_attrs(self):
        """
        Collect the keys the generic schema looks for.
        """
        return {field.source for field in self.fields.values()}

    def to_internal_value(self, data):
        """
        Merge our values into the rest and pass onto the child.
        """
        # Deserialize our schema
        value = super(CompositeSerializer, self).to_internal_value(data)

        # Include all keys not already processed by our schema.
        value.update(
            (key, value) for key, value in data.items()
            if key not in self.fields)

        # Reconstitute and validate the child serializer
        child = self.get_serializer(data=value)
        if child is None:
            raise ValueError(
                'Must give either a child serializer or be used in the '
                'context of a view from which to get the serializer')
        child.is_valid(raise_exception=True)
        value = child.validated_data

        return serializer_helpers.ReturnDict(value, serializer=child)

    def to_representation(self, instance):
        """
        Include our fields that aren't in the child schema.
        """
        if isinstance(instance, serializer_helpers.ReturnDict):
            child = instance.serializer
        else:
            child = self.get_serializer(instance=instance)
            if child is None:
                raise ValueError(
                    'Must give either a child serializer or be used in the '
                    'context of a view from which to get the serializer')

        instance = serializer_helpers.ReturnDict(child.data, serializer=child)

        data = super(CompositeSerializer, self).to_representation(instance)

        # Merge back in child fields that aren't overridden by our schema
        data.update(
            (key, value) for key, value in instance.items()
            if key not in self.field_source_attrs)

        return serializer_helpers.ReturnDict(data, serializer=child)

    def save(self, **kwargs):
        """
        Delegate to the child serializer.
        """
        self.instance = self.validated_data.serializer.save(**kwargs)
        return self.instance

    def create(self, validated_data):
        """
        Delegate to the child serializer.
        """
        return validated_data.serializer.create(validated_data)

    def update(self, instance, validated_data):
        """
        Delegate to the child serializer.
        """
        return validated_data.serializer.update(instance, validated_data)
