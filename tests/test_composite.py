from rest_framework import serializers
from rest_framework import test

from drf_extra_fields import composite


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


class ExampleListSerializer(serializers.Serializer):
    """
    A simple serializer for testing the list composite field.
    """

    children = composite.SerializerListField(child=ExampleChildSerializer())

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return {"children": [
            child_data.clone.create(child_data)
            for child_data in validated_data["children"]]}


class ExampleDictSerializer(serializers.Serializer):
    """
    A simple serializer for testing the dict composite field.
    """

    children = composite.SerializerDictField(child=ExampleChildSerializer())

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return {"children": {
            key: child_data.clone.create(child_data)
            for key, child_data in validated_data["children"].items()}}


class TestCompositeSerializerFields(test.APISimpleTestCase):
    """
    Test that composite field serializers can be used as normal.
    """

    list_data = {"children": [{"name": "Foo Name"}]}
    dict_data = {"children": {"foo": list_data["children"][0]}}

    def test_list_field(self):
        """
        Test that a list field child serializer can be fully used.
        """
        parent = ExampleListSerializer(data=self.list_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, self.list_data, 'Wrong serializer save results')

    def test_dict_field(self):
        """
        Test that a dict field child serializer can be fully used.
        """
        parent = ExampleDictSerializer(data=self.dict_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, self.dict_data, 'Wrong serializer save results')
