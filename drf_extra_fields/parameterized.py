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

        if type(instance) not in self.specific_serializers_by_type:
            return super(
                SerializerParameterField, self).get_attribute(instance)

        specific = self.specific_serializers_by_type[type(instance)]
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

    def bind(self, field_name, parent):
        """
        Tell the generic serializer to get the specific serializers from us.
        """
        super(SerializerParameterDictField, self).bind(field_name, parent)
        self.bind_parameter_field(self.child)

    def get_attribute(self, instance):
        """
        A DictField already knows the current parameter so use that.
        """
        if getattr(self, 'current_parameter', None):
            return self.specific_serializers[self.current_parameter]
        return super(SerializerParameterDictField, self).get_attribute(
            instance)

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

        # Reconstitute and validate the specific serializer
        specific = self.clone_meta['parameter_field'].clone_specific_internal(
            data=value)
        specific.is_valid(raise_exception=True)
        value = composite.CloneReturnDict(specific.validated_data, specific)

        return value

    def to_representation(self, value):
        """
        Include generic items that aren't in the specific schema.
        """
        if isinstance(value, composite.CloneReturnDict):
            specific = value.clone
        else:
            # Make sure all fields are bound
            self.fields
            # Make sure the parameter field sets the specific serializer
            self.clone_meta['parameter_field'].get_attribute(value)
            specific = self.clone_meta[
                'parameter_field'].clone_specific_representation(
                    value=value)

        data = super(ParameterizedGenericSerializer, self).to_representation(
            composite.CloneReturnDict(specific.data, specific))

        # Merge back in specific items that aren't overridden by our schema
        source_attrs = {field.source for field in self.fields.values()}
        data.update(
            (key, value) for key, value in specific.data.items()
            if key not in source_attrs)

        return data

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
