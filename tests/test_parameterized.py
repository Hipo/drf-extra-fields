import copy

from django.contrib.auth import models as auth_models

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework import test

from drf_extra_fields import parameterized
from drf_extra_fields.runtests import serializers as test_serializers
from drf_extra_fields.runtests import viewsets as test_viewsets

from . import test_composite


class ExampleDictFieldSerializer(serializers.Serializer):
    """
    A simple serializer for testing a dict field parameter.
    """

    types = parameterized.SerializerParameterDictField(
        child=parameterized.ParameterizedGenericSerializer(),
        specific_serializers=test_serializers.ExampleTypeFieldSerializer(
        ).fields['type'].specific_serializers)

    def create(self, validated_data):
        """
        Delegate to the specific serializer.
        """
        return {"types": {
            type_: child_data.data.clone.create(child_data)
            for type_, child_data in validated_data["types"].items()}}


class TestParameterizedSerializerFields(test.APITestCase):
    """
    Test that a parameterized field uses the correct serializer.
    """

    type_field_data = {
        "type": "user", "username": "foo_username", "password": "secret"}
    dict_field_data = {"types": {type_field_data["type"]: {
        key: value for key, value in type_field_data.items()
        if key != "type"}}}

    def test_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a field.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            data=self.type_field_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, auth_models.User.objects.get(),
            'Wrong type field serializer save results')
        self.assertEqual(
            parent.data, self.type_field_data,
            'Wrong type field serializer representation')

    def test_parameterized_serializer_create(self):
        """
        Test parameterized serializer delegating to specific on create.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            data=self.type_field_data)
        parent.is_valid(raise_exception=True)
        create_result = parent.create(validated_data=parent.validated_data)
        self.assertEqual(
            create_result, auth_models.User.objects.get(),
            'Wrong type field serializer create results')

    def test_parameterized_serializer_update(self):
        """
        Test parameterized serializer delegating to specific on update.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            data=self.type_field_data)
        parent.is_valid(raise_exception=True)
        update_result = parent.update(
            instance=auth_models.User.objects.create(),
            validated_data=parent.validated_data)
        self.assertEqual(
            update_result, auth_models.User.objects.get(),
            'Wrong type field serializer update results')

    def test_parameterized_serializer_wo_model(self):
        """
        Test delegating to a specific serializer without a model.
        """
        foo_data = dict(
            test_composite.TestCompositeSerializerFields.child_data,
            type="foo-type")
        parent = test_serializers.ExampleTypeFieldSerializer(data=foo_data)
        parent.is_valid(raise_exception=True)
        self.assertEqual(
            parent.data, foo_data,
            'Wrong type field serializer representation')

    def test_parameterized_serializer_instance(self):
        """
        Test parameterized serializer instance to representation.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            instance=self.type_field_data,
            context=dict(view=test_viewsets.ExampleUserViewset()))
        self.assertEqual(
            parent.data, self.type_field_data,
            'Wrong type field serializer representation')

    def test_invalid_parameter(self):
        """
        Test invalid parameter validation.
        """
        invalid_parameter_data = dict(self.type_field_data, type="bar-type")
        parent = test_serializers.ExampleTypeFieldSerializer(
            data=invalid_parameter_data)
        with self.assertRaises(exceptions.ValidationError) as cm:
            parent.is_valid(raise_exception=True)
        self.assertIn(
            'no specific serializer available',
            cm.exception.detail["type"][0].lower(),
            'Wrong invalid parameter validation error')

    def test_dict_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a dict key.
        """
        parent = ExampleDictFieldSerializer(data=self.dict_field_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        dict_field_value = copy.deepcopy(self.dict_field_data)
        dict_field_value["types"]["user"] = auth_models.User.objects.get()
        self.assertEqual(
            save_result, dict_field_value,
            'Wrong dict field serializer save results')
        self.assertEqual(
            parent.data, self.dict_field_data,
            'Wrong dict field serializer representation')
