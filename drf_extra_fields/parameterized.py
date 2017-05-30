import six

from django.conf import settings
from django import urls
from django.utils import functional

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework import renderers
from rest_framework import parsers


from . import composite


def lookup_serializer_parameters(field, pattern):
    """
    Lookup up the parameters and their specific serializers from views.
    """
    specific_serializers = {}
    specific_serializers_by_type = {}

    # Lookup any available viewset that can provide a serializer
    class_ = getattr(getattr(pattern, 'callback', None), 'cls', None)
    if hasattr(class_, 'get_serializer'):
        viewset = class_(request=None, format_kwarg=None)
        serializer = viewset.get_serializer(context=field.context)
        model = getattr(getattr(serializer, 'Meta', None), 'model', None)
        if hasattr(class_, 'get_queryset'):
            model = viewset.get_queryset().model
        parameter = getattr(
            getattr(serializer, 'Meta'), 'parameter',
            model._meta.verbose_name.replace(' ', '-'))
        specific_serializers[parameter] = serializer
        specific_serializers_by_type[model] = serializer

    if hasattr(pattern, 'url_patterns'):
        for recursed_pattern in pattern.url_patterns:
            recursed = lookup_serializer_parameters(field, recursed_pattern)
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


class SerializerParameterField(composite.SerializerCompositeField):
    """
    Map serialized parameter to the specific serializer and back.
    """

    default_error_messages = {
        'parameter': (
            'No specific serializer available for parameter {value!r}'),
    }

    def __init__(
            self,
            urlconf=settings.ROOT_URLCONF,
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
        super(SerializerParameterField, self).__init__(**kwargs)

        assert (
            urlconf or
            specific_serializers or specific_serializers_by_type
        ), (
            'Must give at lease one of `urlconf`, `specific_serializers` or'
            '`specific_serializers_by_type`')
        self.urlconf = urlconf
        self._specific_serializers = specific_serializers
        self._specific_serializers_by_type = specific_serializers_by_type

        self.skip = skip
        self.validators.append(SerializerParameterValidator())

    def bind_parameter_field(self, serializer):
        """
        Bind the serializer to the parameter field.
        """
        if not hasattr(serializer, 'clone_meta'):
            serializer.clone_meta = {}
        serializer.clone_meta['parameter_field'] = self
        self.parameter_serializer = serializer

    def bind(self, field_name, parent):
        """
        Tell the generic serializer to get the specific serializers from us.
        """
        super(SerializerParameterField, self).bind(field_name, parent)
        self.bind_parameter_field(parent)

    def merge_serializer_parameters(self):
        """
        Lookup and merge the parameters and specific serializers.
        """
        serializers = lookup_serializer_parameters(
            self, urls.get_resolver(self.urlconf))
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

    def clone_specific_internal(self, data):
        """
        Lookup specific serializer by the current key.
        """
        specific = SerializerParameterField.to_internal_value(
            self, self.current_parameter)
        return composite.clone_serializer(
            specific, self.parameter_serializer.parent,
            context=self.parameter_serializer.context, data=data)

    def clone_specific_representation(self, value):
        """
        Lookup specific serializer by the current key.
        """
        specific = SerializerParameterField.to_internal_value(
            self, self.current_parameter)
        return composite.clone_serializer(
            specific, self.parameter_serializer.parent,
            context=self.parameter_serializer.context, instance=value)

    def to_internal_value(self, data):
        """
        The specific serializer corresponding to the parameter.
        """
        if data not in self.specific_serializers:
            self.fail('parameter', value=data)

        self.current_parameter = data
        return self.specific_serializers[data]

    def get_attribute(self, instance):
        """
        Get the specific serializer corresponding to the value.
        """
        if isinstance(instance, composite.CloneReturnDict):
            return instance.clone

        model = type(instance)
        if model not in self.specific_serializers_by_type:
            view = self.context.get('view')
            if hasattr(view, 'get_queryset'):
                model = view.get_queryset().model
            else:
                self.current_parameter = super(
                    SerializerParameterField, self).get_attribute(instance)
                return self.specific_serializers[self.current_parameter]

        specific = self.specific_serializers_by_type[model]
        self.current_parameter = self.parameters[type(specific)]
        return specific

    def to_representation(self, value):
        """
        The parameter corresponding to the specific serializer.
        """
        self.current_parameter = self.parameters[type(value)]
        return self.current_parameter


class SerializerParameterDictField(
        composite.SerializerDictField, SerializerParameterField):
    """
    Map dictionary keys to the specific serializers and back.
    """
    # TODO specific serializer validation errors in parameter dict field

    def __init__(self, *args, **kwargs):
        """
        Ensure that `DictField.child` is a `ParameterizedGenericSerializer`.
        """
        kwargs.setdefault('skip', False)

        child = kwargs.get('child')
        assert isinstance(child, ParameterizedGenericSerializer), (
            'The `child` must be a subclass of '
            '`ParameterizedGenericSerializer`')
        super(SerializerParameterDictField, self).__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        """
        Tell the generic serializer to get the specific serializers from us.
        """
        super(SerializerParameterDictField, self).bind(field_name, parent)
        self.bind_parameter_field(self.child)

    get_attribute = composite.SerializerDictField.get_attribute

    def clone_child(self, key, child, **kwargs):
        """
        Record the current parameter before cloning.
        """
        SerializerParameterField.to_internal_value(self, key)
        return super(SerializerParameterDictField, self).clone_child(
            key, child, **kwargs)


class ParameterizedGenericSerializer(
        serializers.Serializer, composite.SerializerCompositeField):
    """
    Process generic schema, then delegate the rest to the specific serializer.
    """

    def to_internal_value(self, data):
        """
        Merge generic values into the rest and pass onto the specific.
        """
        # Deserialize our schema
        value = super(
            ParameterizedGenericSerializer, self).to_internal_value(data)

        # Include all keys not already processed by our schema.
        value.update(
            (key, value) for key, value in data.items()
            if key not in self.fields)

        specific = self.clone_meta[
            'parameter_field'].clone_specific_internal(data=value)
        if not self.context.get('skip_parameterized', False):
            # Reconstitute and validate the specific serializer
            specific.is_valid(raise_exception=True)
            value = specific.validated_data

        return composite.CloneReturnDict(value, specific)

    def to_representation(self, value):
        """
        Include generic items that aren't in the specific schema.
        """
        if isinstance(value, composite.CloneReturnDict):
            specific = value.clone
        else:
            # Ensure all fields are bound so that the parameter field is found
            self.fields
            if getattr(
                    self.clone_meta['parameter_field'],
                    'current_parameter', None) is None:
                # Make sure the parameter field sets the specific serializer
                self.clone_meta['parameter_field'].get_attribute(value)
            specific = self.clone_meta[
                'parameter_field'].clone_specific_representation(
                    value=value)
        if not self.context.get('skip_parameterized', False):
            value = composite.CloneReturnDict(specific.data, specific)

        data = super(ParameterizedGenericSerializer, self).to_representation(
            value)

        # Merge back in specific items that aren't overridden by our schema
        source_attrs = {field.source for field in self.fields.values()}
        data.update(
            (key, value) for key, value in value.items()
            if key not in source_attrs)

        return composite.CloneReturnDict(data, specific)

    def save(self, **kwargs):
        """
        Delegate to the specific serializer.
        """
        self.instance = self.validated_data.clone.save(**kwargs)
        return self.instance

    def create(self, validated_data):
        """
        Delegate to the specific serializer.
        """
        return validated_data.clone.create(validated_data)

    def update(self, instance, validated_data):
        """
        Delegate to the specific serializer.
        """
        return validated_data.clone.update(instance, validated_data)


class ParameterizedRenderer(renderers.JSONRenderer):
    """
    Parameterized format renderer
    """

    # Subclasses must override
    serializer_class = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Transliate the DRF internal format into the parameterized format.
        """

        # Use the serializer to parse only the generic fields, passing the
        # rest onto the serializer for the actual endpoint
        if renderer_context is None:
            context = {}
        else:
            context = renderer_context.copy()
        context['skip_parameterized'] = True

        serializer_kwargs = dict(instance=data, context=context)
        if getattr(context.get('view'), 'action', 'get') == 'list':
            serializer_kwargs['many'] = True

        serializer = self.serializer_class(**serializer_kwargs)
        data = serializer.data

        return super(ParameterizedRenderer, self).render(
            data, accepted_media_type=accepted_media_type,
            renderer_context=renderer_context)


class ParameterizedParser(parsers.JSONParser):
    """
    Parameterized format parser
    """

    # Subclasses must override
    serializer_class = None

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Translate the parameterized format into the DRF internal format.
        """
        data = super(ParameterizedParser, self).parse(
            stream, media_type=media_type, parser_context=parser_context)

        # Use the serializer to parse only the generic parameterized fields,
        # passing the rest onto the serializer for the actual endpoint
        try:
            serializer = self.serializer_class(data=data, context=dict(
                parser_context, skip_parameterized=True))
            serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError as exc:
            raise
        except Exception as exc:
            raise parsers.ParseError(
                'Parse error - %s' % six.text_type(exc))

        return serializer.validated_data
