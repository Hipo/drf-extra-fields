from django.contrib.auth import models as auth_models

from rest_framework import serializers

from drf_extra_fields import parameterized


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


class ExampleUserSerializer(serializers.ModelSerializer):
    """
    A simple model serializer for testing.
    """

    class Meta:
        model = auth_models.User
        fields = ('username', 'password')


class ExampleTypeFieldSerializer(
        parameterized.ParameterizedGenericSerializer):
    """
    A simple serializer for testing a type field parameter.
    """

    type = parameterized.SerializerParameterField(
        specific_serializers={
            "foo-type": ExampleChildSerializer(),
            "user": ExampleUserSerializer()})


