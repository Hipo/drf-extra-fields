from rest_framework import exceptions
from rest_framework import request
from rest_framework import serializers
from rest_framework import test
from rest_framework.utils import serializer_helpers

from drf_extra_fields import composite
from drf_extra_fields.runtests import models
from drf_extra_fields.runtests import serializers as parameterized
from drf_extra_fields.runtests import viewsets as test_viewsets


class ExampleListSerializer(serializers.Serializer):
    """
    A simple serializer for testing the list composite field.
    """

    children = composite.SerializerListField(
        child=parameterized.ExampleChildSerializer(allow_null=True),
        allow_empty=False)

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return {"children": [
            child_data.serializer.create(child_data)
            for child_data in validated_data["children"]]}


class ExampleDictSerializer(serializers.Serializer):
    """
    A simple serializer for testing the dict composite field.
    """

    children = composite.SerializerDictField(
        child=parameterized.ExampleChildSerializer(allow_null=True))

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return {"children": {
            key: child_data.serializer.create(child_data)
            for key, child_data in validated_data["children"].items()}}


class ExampleCompositeSerializer(composite.CompositeSerializer):
    """
    A simple composite serializer.
    """


class TestCompositeSerializerFields(test.APITestCase):
    """
    Test that composite field serializers can be used as normal.
    """

    child_data = {"name": "Foo Name"}
    list_data = {"children": [child_data]}
    dict_data = {"children": {"foo": child_data}}
    list_serializer_data = [child_data]

    def test_list_field(self):
        """
        Test that a list field child serializer can be fully used.
        """
        parent = ExampleListSerializer(data=self.list_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, self.list_data, 'Wrong serializer save results')
        self.assertEqual(
            parent.data, self.list_data, 'Wrong serializer reproduction')

    def test_list_field_instance(self):
        """
        Test that a list field child serializer can be used with an instance.
        """
        parent = ExampleListSerializer(instance=self.list_data)
        self.assertEqual(
            parent.data, self.list_data, 'Wrong serializer reproduction')

    def test_list_field_type(self):
        """
        Test that a list field validates type.
        """
        type = ExampleListSerializer(data=self.dict_data)
        with self.assertRaises(exceptions.ValidationError) as cm:
            type.is_valid(raise_exception=True)
        self.assertIn(
            'expected a list of items',
            cm.exception.detail["children"][0].lower(),
            'Wrong list type validation error')

    def test_list_field_empty(self):
        """
        Test that a list field validates empty values.
        """
        empty_data = self.list_data.copy()
        empty_data["children"] = []
        empty = ExampleListSerializer(data=empty_data)
        with self.assertRaises(exceptions.ValidationError) as cm:
            empty.is_valid(raise_exception=True)
        self.assertIn(
            'may not be empty',
            cm.exception.detail["children"][0].lower(),
            'Wrong list type validation error')

    def test_dict_field(self):
        """
        Test that a dict field child serializer can be fully used.
        """
        parent = ExampleDictSerializer(data=self.dict_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, self.dict_data, 'Wrong serializer save results')
        self.assertEqual(
            parent.data, self.dict_data, 'Wrong serializer representation')

    def test_dict_field_instance(self):
        """
        Test that a dict field child serializer can be used with an instance.
        """
        parent = ExampleDictSerializer(instance=self.dict_data)
        self.assertEqual(
            parent.data, self.dict_data, 'Wrong serializer reproduction')

    def test_list_serializer(self):
        """
        Test that a list serializer work.
        """
        parent = serializers.ListSerializer(
            data=self.list_serializer_data,
            child=parameterized.ExampleChildSerializer())
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, self.list_serializer_data,
            'Wrong serializer save results')

    def test_clone_serializer(self):
        """
        Test that cloning a serializer preserves what is needed.
        """
        parent = serializers.ListSerializer(
            data=self.list_serializer_data,
            child=parameterized.ExampleChildSerializer())
        parent.clone_meta = {"foo": "bar"}
        clone = composite.clone_serializer(parent)
        self.assertIs(
            clone.original, parent,
            'Serializer clone wrong original')
        self.assertIsInstance(
            clone.child, type(parent.child),
            'Serializer clone wrong child type')
        self.assertIs(
            clone.clone_meta, parent.clone_meta,
            'Serializer clone wrong clone metadata')

    def test_cone_return_dict(self):
        """
        Test that the return dict wrapper has the right references.
        """
        parent = ExampleListSerializer(data=self.list_data)
        parent.is_valid(raise_exception=True)
        wrapped = parent.validated_data["children"][0]
        self.assertIsInstance(
            wrapped, serializer_helpers.ReturnDict,
            'Child data missing clone wrapper')
        wrapped_copy = wrapped.copy()
        self.assertIsInstance(
            wrapped_copy, serializer_helpers.ReturnDict,
            'Child data clone wrapper copy wrong type')
        self.assertIs(
            wrapped_copy.serializer, wrapped.serializer,
            'Child serializer clone wrapper copy wrong serializer')

    def test_composite_serializer_child(self):
        """
        Test the composite serializer with a specific child.
        """
        data = {"name": "Foo name"}
        parent = ExampleCompositeSerializer(
            child=parameterized.ExampleChildSerializer(), data=data,
            primary=True)
        parent.is_valid(raise_exception=True)
        self.assertEqual(
            parent.save(), data,
            'Wrong composite serializer saved instance type')
        self.assertEqual(
            parent.create(parent.validated_data), data,
            'Wrong composite serializer saved instance type')
        self.assertEqual(
            parent.update(parent.instance, parent.validated_data), data,
            'Wrong composite serializer saved instance type')

    def test_composite_serializer_view(self):
        """
        Test the composite serializer getting the child from the view.
        """
        view = test_viewsets.ExamplePersonViewset()
        factory = test.APIRequestFactory()
        view.request = request.Request(factory.get('/'))
        view.format_kwarg = None
        data = {"name": "Foo name", "articles": []}
        parent = composite.CompositeSerializer(
            context=dict(view=view), data=data)
        parent.is_valid(raise_exception=True)
        self.assertEqual(
            parent.data, data, 'Wrong representation value')

    def test_composite_serializer_missing(self):
        """
        Test the composite serializer wthout a child.
        """
        data_parent = composite.CompositeSerializer(data={})
        with self.assertRaises(Exception) as to_internal_value:
            data_parent.is_valid(raise_exception=True)
        self.assertIn(
            'must give either', str(to_internal_value.exception).lower(),
            'Wrong composite serializer missing child error')

        instance_parent = composite.CompositeSerializer(instance={})
        with self.assertRaises(Exception) as to_representation:
            instance_parent.data
        self.assertIn(
            'must give either', str(to_representation.exception).lower(),
            'Wrong composite serializer missing child error')

    def test_composite_serializer_instance(self):
        """
        Test the composite serializer with an instance.
        """
        data = {"name": "Foo name"}
        parent = ExampleCompositeSerializer(
            child=parameterized.ExampleChildSerializer(),
            instance=models.Person.objects.create(**data))
        self.assertEqual(
            parent.data, data, 'Wrong representation value')
