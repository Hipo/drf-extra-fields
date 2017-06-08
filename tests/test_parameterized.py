import copy
import json
import pprint

from django.contrib.auth import models as auth_models

from rest_framework import serializers
from rest_framework import test

from drf_extra_fields import parameterized
from drf_extra_fields.runtests import serializers as test_serializers
from drf_extra_fields.runtests import viewsets as test_viewsets
from drf_extra_fields.runtests import formats

from . import test_composite


class ExampleDictFieldSerializer(serializers.Serializer):
    """
    A simple serializer for testing a dict field parameter.
    """

    types = parameterized.SerializerParameterDictField(
        child=parameterized.ParameterizedGenericSerializer(),
        specific_serializers=test_serializers.ExampleTypeFieldSerializer(
        ).fields['type']._specific_serializers)

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

    user_field_data = {"username": "foo_username", "password": "secret"}
    type_field_data = dict(user_field_data, type="user")
    dict_field_data = {"types": {type_field_data["type"]: user_field_data}}

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
        create_response = self.client.post(
            '/types/', invalid_parameter_data, format='json')
        self.assertEqual(
            create_response.status_code, 400,
            'Invalid request did return validation error:\n{0}'.format(
                pprint.pformat(create_response.data)))
        self.assertIn(
            'type', create_response.data,
            'Missing invalid parameter validation error')
        self.assertIn(
            'no specific serializer available',
            create_response.data["type"][0].lower(),
            'Wrong invalid parameter validation error')

    def test_parameterized_field_parameters(self):
        """
        Test referencing reverse parameter lookup.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            instance=self.type_field_data,
            context=dict(view=test_viewsets.ExampleUserViewset()))
        self.assertIn(
            test_serializers.ExampleUserSerializer,
            parent.fields['type'].parameters,
            'Missing specific serializer in reverse parameter lookup')
        self.assertEqual(
            parent.fields['type'].parameters[
                test_serializers.ExampleUserSerializer],
            self.type_field_data['type'],
            'Wrong specific serializer reverse parameter lookup')

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

    def test_parameterized_format(self):
        """
        Test using parameterized serialiers in renderers/parsers.
        """
        create_response = self.client.post(
            '/users/?format=drf-extra-fields-parameterized',
            json.dumps(self.type_field_data),
            content_type=formats.ExampleParameterizedRenderer.media_type)
        self.assertEqual(
            create_response.status_code, 201,
            'Create request did not succeed:\n{0}'.format(
                pprint.pformat(create_response.data)))
        create_json = json.loads(create_response.content.decode())
        self.assertEqual(
            create_json["username"], self.type_field_data["username"],
            'Wrong parameterized format create response results')

    def test_parameterized_format_wo_context(self):
        """
        Test using parameterized renderers/parsers without context.

        Unfortunately, this is specific to the DRF test framework.
        """
        create_response = self.client.post(
            '/users/',
            self.type_field_data,
            format='drf-extra-fields-parameterized')
        self.assertEqual(
            create_response.status_code, 201,
            'Create request did not succeed:\n{0}'.format(
                pprint.pformat(create_response.data)))
        create_json = json.loads(create_response.content.decode())
        self.assertEqual(
            create_json["username"], self.type_field_data["username"],
            'Wrong parameterized format create response results')

    def test_parameterized_format_list(self):
        """
        Test using parameterized renderers/parsers on list views.
        """
        auth_models.User.objects.create(**self.user_field_data)
        list_response = self.client.get(
            '/users/?format=drf-extra-fields-parameterized')
        self.assertEqual(
            list_response.status_code, 200,
            'List request did not succeed:\n{0}'.format(
                pprint.pformat(list_response.data)))
        list_json = json.loads(list_response.content.decode())
        self.assertEqual(
            list_json[0], self.type_field_data,
            'Wrong parameterized format list response results')

    def test_parameterized_parser_validation(self):
        """
        Test the parameterized parser validation.
        """
        invalid_response = self.client.post(
            '/users/?format=drf-extra-fields-parameterized',
            json.dumps(self.user_field_data),
            content_type=formats.ExampleParameterizedRenderer.media_type)
        self.assertEqual(
            invalid_response.status_code, 400,
            'Invalid request did return validation error:\n{0}'.format(
                pprint.pformat(invalid_response.data)))
        self.assertIn(
            'type', invalid_response.data,
            'Invalid request did not return error details.')
        self.assertIn(
            'this field is required',
            invalid_response.data['type'][0].lower(),
            'Wrong invalid request error details.')

    def test_parameterized_parser_exception(self):
        """
        Test the parameterized parser exception handling.
        """
        exception_field_data = dict(
            self.user_field_data,
            test_unhandled_exception='Foo parser exception')
        exception_response = self.client.post(
            '/users/?format=drf-extra-fields-parameterized',
            json.dumps(exception_field_data),
            content_type=formats.ExampleParameterizedRenderer.media_type)
        self.assertEqual(
            exception_response.status_code, 400,
            'Exception request did return validation error:\n{0}'.format(
                pprint.pformat(exception_response.data)))
        self.assertIn(
            'detail', exception_response.data,
            'Exception request did not return error details.')
        self.assertIn(
            exception_field_data['test_unhandled_exception'].lower(),
            exception_response.data['detail'].lower(),
            'Wrong exception request error details.')
