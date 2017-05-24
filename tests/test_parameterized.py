from rest_framework import serializers
from rest_framework import test

from drf_extra_fields import parameterized
from . import test_composite


class ExampleTypeFieldSerializer(
        parameterized.ParameterizedGenericSerializer):
    """
    A simple serializer for testing a type field parameter.
    """

    type = parameterized.SerializerParameterField(
        specific_serializers={
            "foo-type": test_composite.ExampleChildSerializer()})


class ExampleDictFieldSerializer(serializers.Serializer):
    """
    A simple serializer for testing a dict field parameter.
    """

    types = parameterized.SerializerParameterDictField(
        child=parameterized.ParameterizedGenericSerializer(),
        specific_serializers=ExampleTypeFieldSerializer().fields[
            'type'].specific_serializers)

    def create(self, validated_data):
        """
        Delegate to the specific serializer.
        """
        return {"types": {
            type_: child_data.data.clone.create(child_data)
            for type_, child_data in validated_data["types"].items()}}


class TestParameterizedSerializerFields(test.APISimpleTestCase):
    """
    Test that a parameterized field uses the correct serializer.
    """

    type_field_data = {"type": "foo-type", "name": "Foo Name"}
    dict_field_data = {"types": {
        type_field_data["type"]: {"name": type_field_data["name"]}}}

    def test_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a field.
        """
        parent = ExampleTypeFieldSerializer(data=self.type_field_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        specific_data = self.type_field_data.copy()
        del specific_data["type"]
        self.assertEqual(
            save_result, specific_data,
            'Wrong type field serializer save results')

    def test_dict_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a dict key.
        """
        parent = ExampleDictFieldSerializer(data=self.dict_field_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, self.dict_field_data,
            'Wrong dict field serializer save results')
