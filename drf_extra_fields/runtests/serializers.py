from rest_framework import serializers

from drf_extra_fields import relations
from drf_extra_fields import parameterized

from . import models


class ExampleChildSerializer(serializers.Serializer):
    """
    A simple serializer for testing composite fields as a child.
    """

    name = serializers.CharField()

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return validated_data

    def update(self, instance, validated_data):
        """
        Delegate to the children.
        """
        return validated_data


class ExamplePersonSerializer(relations.UUIDModelSerializer):
    """
    A simple model serializer for testing.
    """

    class Meta:
        model = models.Person
        fields = ('id', 'name', 'articles')
        extra_kwargs = dict(
            related_to=dict(lookup_field='uuid'))


class ExampleTypeFieldSerializer(
        parameterized.ParameterizedGenericSerializer):
    """
    A simple serializer for testing a type field parameter.
    """

    type = parameterized.SerializerParameterField(
        specific_serializers={
            "foo-type": ExampleChildSerializer()})

    def to_internal_value(self, data):
        """
        Add a hook for raising an unhandled exception.
        """
        if 'test_unhandled_exception' in data:
            raise Exception(data['test_unhandled_exception'])
        return super(ExampleTypeFieldSerializer, self).to_internal_value(data)
