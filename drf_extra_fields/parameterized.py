from rest_framework import serializers

from . import composite


class SerializerParameterValidator(object):
    """
    Omit the field the specifies the serializer unless configured otherwise.
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


class SerializerParameterField(serializers.Field):
    """
    Map serialized parameter to the specific serializer and back.
    """

    default_error_messages = {
        'parameter': (
            'No specific serializer available for parameter {value!r}'),
    }

    def __init__(
            self,
            specific_serializers={}, specific_serializers_by_type={},
            skip=True, **kwargs):
        """
        Map parameters to serializers/fields per `specific_serializers`.
        """
        super(SerializerParameterField, self).__init__(**kwargs)

        assert specific_serializers, (
            'Must give `specific_serializers` kwarg '
            'mapping parameters to serializers/fields')
        self.specific_serializers = specific_serializers
        self.parameters = {
            type(specific): parameter
            for parameter, specific
            in self.specific_serializers.items()}
        self.specific_serializers_by_type = {
            specific.Meta.model: specific
            for specific in self.specific_serializers.values()
            if hasattr(specific, 'Meta') and
            hasattr(specific.Meta, 'model')}

        self.skip = skip
        self.validators.append(SerializerParameterValidator())

    def get_generic_serializer(self):
        """
        Get the generic serializer for this parameter fields.

        Override based on where the parameter comes from and where it applies.
        """
        # Common case: parameter is a field in the generic serializer
        return self.parent

    def set_specific(self, specific):
        """
        Make the specific serializer available to the generic serializer.
        """
        parent = self.get_generic_serializer()
        parent.child = specific
        parent.parameter_field = self
        return parent

    def to_internal_value(self, data):
        """
        The specific serializer corresponding to the parameter.
        """
        if data not in self.specific_serializers:
            self.fail('parameter', value=data)

        specific = self.specific_serializers[data]
        self.set_specific(specific)
        return specific

    def get_attribute(self, instance):
        """
        Get the specific serializer corresponding to the value.
        """
        if isinstance(instance, composite.SerializerChildValueWrapper):
            return instance.child

        if type(instance) not in self.specific_serializers_by_type:
            return super(
                SerializerParameterField, self).get_attribute(instance)
        specific = self.specific_serializers_by_type[type(instance)]
        self.set_specific(specific)
        return specific

    def to_representation(self, value):
        """
        The parameter corresponding to the specific serializer.
        """
        return self.parameters[type(value)]


class SerializerParameterDictField(
        composite.SerializerDictField, SerializerParameterField):
    """
    Map dictionary keys to the specific serializers and back.
    """

    def __init__(self, *args, **kwargs):
        """
        Ensure that `DictField.child` is a `ParameterizedGenericSerializer`.
        """
        kwargs.setdefault('skip', False)

        child = kwargs.get('child')
        if child is None:
            kwargs['child'] = ParameterizedGenericSerializer()
        else:
            assert isinstance(child, ParameterizedGenericSerializer), (
                'The `child` must be a subclass of '
                '`ParameterizedGenericSerializer`')
        super(SerializerParameterDictField, self).__init__(*args, **kwargs)

    def get_generic_serializer(self):
        """
        For a DictField, the ParameterizedGenericSerializer is the child.
        """
        return self.child

    def make_child(self, key, **kwargs):
        """
        Dictionary specific child lookup.
        """
        SerializerParameterField.to_internal_value(self, key)
        return super(SerializerParameterDictField, self).make_child(
            key, **kwargs)


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

        # Reconstitute and validate the specific serializer
        child = self.make_child(data=value)
        child.is_valid(raise_exception=True)

        # Make the specific serializer accessible downstream
        value = self.wrap_value(child)

        return value

    def to_representation(self, value):
        """
        Include generic items that aren't in the specific schema.
        """
        data = super(
            ParameterizedGenericSerializer, self).to_representation(value)

        if isinstance(value, composite.SerializerChildValueWrapper):
            child = value.child
        else:
            self.child = self.parameter_field.get_attribute(value)
            child = self.make_child(instance=value)

            # Override the child's representation with our representation
        # Merge back in child items that aren't overridden by our schema
        source_attrs = {field.source for field in self.fields.values()}
        data.update(
            (key, value) for key, value in child.data.items()
            if key not in source_attrs)

        return data

    def save(self, **kwargs):
        """
        Delegate to the specific serializer.
        """
        self.instance = self.child.save(**kwargs)
        return self.instance

    def create(self, validated_data):
        """
        Delegate to the specific serializer.
        """
        return self.child.create(validated_data)

    def update(self, instance, validated_data):
        """
        Delegate to the specific serializer.
        """
        return self.child.update(instance, validated_data)
