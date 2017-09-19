import re

try:
    import inflection
except ImportError:  # pragma: no cover
    inflectors = []
else:
    inflectors = [inflection.pluralize, inflection.parameterize]

from django.conf import settings
from django import urls
from django.db import models
from django.utils import functional

from rest_framework import serializers
from django.utils import six
from rest_framework.utils import serializer_helpers
from rest_framework.utils import html

from . import composite

url_parameter_re = re.compile(r'\^([^/?]+)/\$')


def get_resource_items(
        instance, pattern=None,
        url_re=url_parameter_re, inflectors=inflectors):
    """
    Lookup the resource type, model and serializer, from various sources.
    """
    if isinstance(instance, models.Model):
        model = instance
        serializer = parameter = None
    elif hasattr(instance, 'get_serializer'):
        serializer = instance.get_serializer()
        model = getattr(getattr(serializer, 'Meta', None), 'model', None)
        if hasattr(instance, 'get_queryset'):
            try:
                queryset = instance.get_queryset()
            except AssertionError:
                pass
            else:
                model = queryset.model

        parameter = getattr(
            getattr(serializer, 'Meta', None), 'parameter', None)

    if parameter is None:
        if pattern is not None:
            url_match = url_re.match(pattern.regex.pattern)
            if url_match is not None:
                parameter = url_match.group(1)
        if pattern is None and model is not None:
            parameter = model._meta.verbose_name
    if parameter is not None:
        for inflector in inflectors:
            parameter = inflector(parameter)

    return parameter, model, serializer


def lookup_serializer_parameters(
        field, pattern, url_re=url_parameter_re, inflectors=inflectors):
    """
    Lookup up the parameters and their specific serializers from views.
    """
    specific_serializers = {}
    specific_serializers_by_type = {}

    # Lookup any available viewset that can provide a serializer
    class_ = getattr(getattr(pattern, 'callback', None), 'cls', None)
    if hasattr(class_, 'get_serializer'):
        viewset = class_(request=None, format_kwarg=None)
        parameter, model, serializer = get_resource_items(
            viewset, pattern, url_re, inflectors)
        if serializer is not None:
            if parameter is not None:
                specific_serializers.setdefault(parameter, serializer)
            if model is not None:
                specific_serializers_by_type.setdefault(model, serializer)

    if hasattr(pattern, 'url_patterns'):
        for recursed_pattern in pattern.url_patterns:
            recursed = lookup_serializer_parameters(
                field, recursed_pattern, inflectors=inflectors)
            recursed['specific_serializers'].update(
                specific_serializers)
            specific_serializers = recursed[
                'specific_serializers']
            recursed['specific_serializers_by_type'].update(
                specific_serializers_by_type)
            specific_serializers_by_type = recursed[
                'specific_serializers_by_type']
    return dict(
        specific_serializers=specific_serializers,
        specific_serializers_by_type=specific_serializers_by_type)


class SerializerParameterValidator(object):
    """
    Omit the parameter field by default.
    """

    def set_context(self, serializer_field):
        """
        Capture the field.
        """
        self.field = serializer_field

    def __call__(self, value):
        """
        Omit the field unless configured otherwise.
        """
        if self.field.skip:
            raise serializers.SkipField(
                "Don't include generic type field in internal value")
        return value


class SerializerParameterFieldBase(serializers.Field, composite.Cloner):
    """
    Map serialized parameter to the specific serializer and back.
    """

    default_error_messages = {
        'unknown': (
            'No specific serializer available for parameter {value!r}'),
        'serializer': (
            'No parameter found for the specific serializer, {value!r}'),
        'mismatch': (
            'The parameter, {data!r}, '
            'does not match the looked up parameter, {parameter!r}'),
    }

    def __init__(
            self,
            urlconf=settings.ROOT_URLCONF, inflectors=inflectors,
            specific_serializers={}, specific_serializers_by_type={},
            skip=True, **kwargs):
        """Map parameters to serializers/fields per `specific_serializers`.

        `specific_serializers` maps parameter keys (e.g. string "types") to
        serializer instance values while `specific_serializers_by_type` maps
        instance types/classes (e.g. Django models) to specific serializer
        instances.

        If `urlconf` is given or is left as it's default,
        `settings.ROOT_URLCONF`, it will be used to map singular string types
        derived from the model's `verbose_name` of any viewset's
        `get_queryset()` found in the default URL patterns to those viewset's
        serializers via `get_serializer()`.

        If both are given, items in `specific_serializers*` override items
        derived from `urlconf`.
        """
        super(SerializerParameterFieldBase, self).__init__(**kwargs)

        assert (
            urlconf or
            specific_serializers or specific_serializers_by_type
        ), (
            'Must give at lease one of `urlconf`, `specific_serializers` or'
            '`specific_serializers_by_type`')
        self.urlconf = urlconf
        self.inflectors = inflectors
        self._specific_serializers = specific_serializers
        self._specific_serializers_by_type = specific_serializers_by_type

        self.skip = skip
        self.validators.append(SerializerParameterValidator())

        self.parameter_serializers = []

    def bind_parameter_field(self, serializer):
        """
        Bind the serializer to the parameter field.
        """
        if not hasattr(serializer, 'clone_meta'):
            serializer.clone_meta = {}
        serializer.clone_meta['parameter_field'] = self
        if isinstance(serializer, ParameterizedGenericSerializer):
            self.parameter_serializers.append(serializer)

    def bind(self, field_name, parent):
        """
        Tell the generic serializer to get the specific serializers from us.
        """
        super(SerializerParameterFieldBase, self).bind(field_name, parent)
        self.bind_parameter_field(parent)

    def merge_serializer_parameters(self):
        """
        Lookup and merge the parameters and specific serializers.
        """
        serializers = lookup_serializer_parameters(
            self, urls.get_resolver(self.urlconf), inflectors=self.inflectors)
        serializers['specific_serializers'].update(
            self._specific_serializers)
        serializers['specific_serializers_by_type'].update(
            self._specific_serializers_by_type)
        serializers['parameters'] = {
            type(serializer): parameter for parameter, serializer in
            serializers['specific_serializers'].items()}
        return serializers

    @functional.cached_property
    def specific_serializers(self):
        """
        Populate specific serializer lookup on first reference.
        """
        serializers = self.merge_serializer_parameters()
        vars(self).update(**serializers)
        return serializers['specific_serializers']

    @functional.cached_property
    def specific_serializers_by_type(self):
        """
        Populate specific serializer lookup on first reference.
        """
        serializers = self.merge_serializer_parameters()
        vars(self).update(**serializers)
        return serializers['specific_serializers_by_type']

    @functional.cached_property
    def parameters(self):
        """
        Populate specific serializer lookup on first reference.
        """
        serializers = self.merge_serializer_parameters()
        vars(self).update(**serializers)
        return serializers['parameters']

    def to_internal_value(self, data):
        """
        The specific serializer corresponding to the parameter.
        """
        if data not in self.specific_serializers:
            self.fail('unknown', value=data)

        # if the generic serializer ends up using a serializer other than
        # `self.child`, such as when the primary serializer looks up the
        # serializer from the view, verify that the type matches.
        child = self.parameter_serializers[0].get_view_serializer()
        if child is not None:
            parameter = self.parameters.get(type(child))
            if parameter is None:
                self.fail('serializer', value=child)
            if data != parameter:
                self.fail('mismatch', data=data, parameter=parameter)
        else:
            child = self.specific_serializers[data]

        for parameter_serializer in self.parameter_serializers:
            parameter_serializer.child = child
        return child

    def to_representation(self, instance):
        """
        The parameter corresponding to the specific serializer.
        """
        if isinstance(instance, serializer_helpers.ReturnDict):
            # Serializing self.validated_data
            child = instance.serializer
        else:
            # Infer the specific serializer from the instance type
            model = type(instance)
            # TODO validation error?
            assert model in self.specific_serializers_by_type, (
                'Could not lookup parameter from {0!r}'.format(instance))
            child = self.specific_serializers_by_type[model]
        data = self.parameters[type(child)]

        # if the generic serializer ends up using a serializer other than
        # `self.child`, such as when the primary serializer looks up the
        # serializer from the view, verify that the type matches.
        view_child = self.parameter_serializers[0].get_view_serializer()
        if view_child is not None:
            child = view_child

        for parameter_serializer in self.parameter_serializers:
            parameter_serializer.child = child
        return data


class SerializerParameterField(
        composite.ParentField, SerializerParameterFieldBase):
    """
    Map field data to the specific serializer and back.
    """


class SerializerParameterDictField(
        composite.SerializerDictField, SerializerParameterFieldBase):
    """
    Map dictionary keys to the specific serializers and back.
    """
    # TODO specific serializer validation errors in parameter dict field

    def __init__(self, *args, **kwargs):
        """
        Don't skip the field by default.
        """
        kwargs.setdefault('skip', False)
        super(SerializerParameterDictField, self).__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        """
        Tell the generic serializer to get the specific serializers from us.
        """
        super(SerializerParameterDictField, self).bind(field_name, parent)
        self.bind_parameter_field(self.child.child)

    def to_internal_value(self, data):
        """
        Use the dictionary keys as the parameter.x
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)

        value = serializer_helpers.ReturnDict(serializer=self)
        for key, val in data.items():
            # Set the specific serializer using the key as the parameter
            SerializerParameterFieldBase.to_internal_value(self, key)
            value[six.text_type(key)] = self.child.run_validation(val)
        return value

    def to_representation(self, value):
        """
        Use the dictionary keys as the parameter.x
        """
        data = serializer_helpers.ReturnDict(serializer=self)
        for key, val in value.items():
            # Set the specific serializer using the key as the parameter
            SerializerParameterFieldBase.to_internal_value(self, key)
            if val is None:
                data[six.text_type(key)] = None
            else:
                data[six.text_type(key)] = self.child.to_representation(val)
        return data


class ParameterizedGenericSerializer(composite.CompositeSerializer):
    """
    Process generic schema, then delegate the rest to the specific serializer.
    """

    # Class-based defaults for instantiation kwargs
    exclude_parameterized = False

    def __init__(
            self, instance=None, data=serializers.empty,
            parameter_field_name=None, exclude_parameterized=None, **kwargs):
        """Process generic schema, then delegate the rest to the specific.

        `SerializerParameterField` expects to be a field in the same
        JavaScript object as the parameterized fields:
        `{"type": "users", "id": 1, "username": "foo_username", ...}`
        while `SerializerParameterDictField` expects to get the parameter from
        a JavaScript object key/property-name:
        `{"users": {"id": 1, "username": "foo_username", ...}, ...}`.
        If `parameter_field_name` is given, it must be the name of a
        SerializerParameterField in the same parent serializer as this
        serializer.  This can be useful when the parameter is taken from a
        field next to the serializer, such as the JSON API format:
        `{"type": "users", "attributes": {"username": "foo_username", ...}}`.

        By default, the looked up parameterized serializer is used to process
        the data during `to_internal_value()` and `to_representation()`.
        Alternatively, only the paramaterized serializer fields which are
        consumed by the generic serializer's fields can be used if
        `exclude_parameterized=True`.  This can be useful where you need the
        parameterized serializer to lookup the parameter but don't actually
        want to include it's schema, such as when just looking up a `type`:
        `{"type": "users", "id": 1}`

        """
        super(ParameterizedGenericSerializer, self).__init__(
            instance=instance, data=data, **kwargs)
        self.parameter_field_name = parameter_field_name
        if exclude_parameterized is not None:
            # Allow class to provide a default
            self.exclude_parameterized = exclude_parameterized

    def bind(self, field_name, parent):
        """
        If a sibling parameter field is specified, bind as needed.
        """
        super(ParameterizedGenericSerializer, self).bind(field_name, parent)
        if self.parameter_field_name is not None:
            parameter_field = parent.fields[
                self.parameter_field_name]
            parameter_field.bind_parameter_field(self)

    def get_serializer(self, **kwargs):
        """
        Optionally exclude the specific child serialiers fields.
        """
        clone = super(ParameterizedGenericSerializer, self).get_serializer(
            **kwargs)
        if clone is None:
            return

        if self.exclude_parameterized:
            for field_name, field in list(clone.fields.items()):
                if field_name not in self.field_source_attrs:
                    del clone.fields[field_name]

        return clone

    def to_representation(self, instance):
        """
        Ensure the current parameter and serializer are set first.
        """
        # Ensure all fields are bound so the parameter field is available
        self.fields
        # Set the current parameter and specific serializer
        parameter_field = self.clone_meta['parameter_field']
        SerializerParameterFieldBase.to_representation(
            parameter_field, instance)

        return super(ParameterizedGenericSerializer, self).to_representation(
            instance)
