from django.utils import datastructures

import copy
import json
import pprint

import inflection

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework import test

from drf_extra_fields import parameterized
from drf_extra_fields.runtests import models
from drf_extra_fields.runtests import serializers as test_serializers
from drf_extra_fields.runtests import viewsets as test_viewsets
from drf_extra_fields.runtests import formats

from . import test_composite


class ExampleDictFieldSerializer(serializers.Serializer):
    """
    A simple serializer for testing a dict field parameter.
    """

    types = parameterized.SerializerParameterDictField(
        inflectors=[inflection.singularize, inflection.parameterize],
        child=parameterized.ParameterizedGenericSerializer(allow_null=True),
        specific_serializers=test_serializers.ExampleTypeFieldSerializer(
        ).fields['type']._specific_serializers)

    def create(self, validated_data):
        """
        Delegate to the specific serializer.
        """
        return {"types": {
            type_: child_data.serializer.create(child_data)
            for type_, child_data in validated_data["types"].items()}}


class ExampleSiblingFieldSerializer(serializers.Serializer):
    """
    A simple serializer for testing a dict field parameter.
    """

    type = parameterized.SerializerParameterField(
        specific_serializers=test_serializers.ExampleTypeFieldSerializer(
        ).fields['type']._specific_serializers, source='attributes')
    attributes = parameterized.ParameterizedGenericSerializer(
        parameter_field_name='type')

    def create(self, validated_data):
        """
        Delegate to the specific serializer.
        """
        validated_data["type"] = self.fields['type'].parameters[
            type(validated_data['attributes'].serializer)]
        validated_data["attributes"] = validated_data[
            "attributes"].serializer.create(validated_data["attributes"])
        return validated_data


class TestParameterizedSerializerFields(test.APITestCase):
    """
    Test that a parameterized field uses the correct serializer.
    """

    person_field_data = {"name": "Foo Name", "articles": []}
    type_field_data = dict(person_field_data, type="people")
    sibling_field_data = {"type": "people", "attributes": person_field_data}
    dict_field_data = {"types": {"person": person_field_data}}

    def test_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a field.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            data=self.type_field_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        self.assertEqual(
            save_result, models.Person.objects.get(),
            'Wrong type field serializer save results')
        type_field_data = dict(
            self.type_field_data, id=str(save_result.uuid))
        self.assertEqual(
            parent.data, type_field_data,
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
            create_result, models.Person.objects.get(),
            'Wrong type field serializer create results')

    def test_parameterized_serializer_update(self):
        """
        Test parameterized serializer delegating to specific on update.
        """
        parent = test_serializers.ExampleTypeFieldSerializer(
            data=self.type_field_data)
        parent.is_valid(raise_exception=True)
        update_result = parent.update(
            instance=models.Person.objects.create(),
            validated_data=parent.validated_data)
        self.assertEqual(
            update_result, models.Person.objects.get(),
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
        person = models.Person.objects.create(
            name=self.person_field_data['name'])
        parent = test_serializers.ExampleTypeFieldSerializer(
            instance=person,
            context=dict(view=test_viewsets.ExamplePersonViewset()))
        self.assertEqual(
            parent.data, dict(self.type_field_data, id=str(person.uuid)),
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
            context=dict(view=test_viewsets.ExamplePersonViewset()))
        self.assertIn(
            test_serializers.ExamplePersonSerializer,
            parent.fields['type'].parameters,
            'Missing specific serializer in reverse parameter lookup')
        self.assertEqual(
            parent.fields['type'].parameters[
                test_serializers.ExamplePersonSerializer],
            self.type_field_data['type'],
            'Wrong specific serializer reverse parameter lookup')

    def test_sibling_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a sibling field.
        """
        parent = ExampleSiblingFieldSerializer(data=self.sibling_field_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        sibling_field_value = copy.deepcopy(self.sibling_field_data)
        sibling_field_value["attributes"] = models.Person.objects.get()
        self.assertEqual(
            save_result, sibling_field_value,
            'Wrong sibling field serializer save results')
        sibling_field_data = copy.deepcopy(self.sibling_field_data)
        sibling_field_data["attributes"]["id"] = str(
                sibling_field_value["attributes"].uuid)
        self.assertEqual(
            parent.data, sibling_field_data,
            'Wrong sibling field serializer representation')

    def test_dict_parameterized_serializer(self):
        """
        Test delegating to a specific serializer from a dict key.
        """
        dict_data = self.dict_field_data.copy()
        dict_data["types"] = datastructures.MultiValueDict({
            '.' + key: [value]
            for key, value in self.dict_field_data["types"].items()})
        parent = ExampleDictFieldSerializer(data=dict_data)
        parent.is_valid(raise_exception=True)
        save_result = parent.save()
        dict_field_value = copy.deepcopy(self.dict_field_data)
        dict_field_value["types"]["person"] = models.Person.objects.get()
        self.assertEqual(
            save_result, dict_field_value,
            'Wrong dict field serializer save results')
        dict_field_data = self.dict_field_data.copy()
        dict_field_data["types"]["person"]["id"] = str(
            dict_field_value["types"]["person"].uuid)
        self.assertEqual(
            parent.data, dict_field_data,
            'Wrong dict field serializer representation')

    def test_dict_parameterized_serializer_none(self):
        """
        Test that a dict field handles none values.
        """
        none_data = self.dict_field_data.copy()
        none_data["types"] = dict(self.dict_field_data["types"])
        none_data["types"]["foo-type"] = None
        none = ExampleDictFieldSerializer(data=none_data)
        none.is_valid(raise_exception=True)
        self.assertEqual(
            none.data, none_data, 'Wrong serializer reproduction')

    def test_dict_parameterized_serializer_type(self):
        """
        Test that a dict field validates type.
        """
        type_data = self.dict_field_data.copy()
        type_data["types"] = [self.dict_field_data["types"]]
        wrong_type = ExampleDictFieldSerializer(data=type_data)
        with self.assertRaises(exceptions.ValidationError) as cm:
            wrong_type.is_valid(raise_exception=True)
        self.assertIn(
            'expected a dictionary of items',
            cm.exception.detail["types"][0].lower(),
            'Wrong dict type validation error')

    def test_serializer_exclude_parameterized(self):
        """
        An parameterized serializer can optionally exclude specific fields.
        """
        data_serializer = test_serializers.ExampleTypeFieldSerializer(
            data=self.type_field_data, exclude_parameterized=True)
        data_serializer.is_valid(raise_exception=True)
        self.assertNotIn(
            'name', data_serializer.data,
            'Parameterized field in internal value')
        person = models.Person.objects.create(
            name=self.person_field_data['name'])
        instance_serializer = test_serializers.ExampleTypeFieldSerializer(
            instance=person, exclude_parameterized=True)
        self.assertNotIn(
            'name', instance_serializer.data,
            'Parameterized field in representation')

    def test_parameterized_format(self):
        """
        Test using parameterized serialiers in renderers/parsers.
        """
        create_response = self.client.post(
            '/people/?format=drf-extra-fields-parameterized',
            json.dumps(self.type_field_data),
            content_type=formats.ExampleParameterizedRenderer.media_type)
        self.assertEqual(
            create_response.status_code, 201,
            'Create request did not succeed:\n{0}'.format(
                pprint.pformat(create_response.data)))
        create_json = json.loads(create_response.content.decode())
        self.assertEqual(
            create_json["name"], self.type_field_data["name"],
            'Wrong parameterized format create response results')

    def test_parameterized_format_wo_context(self):
        """
        Test using parameterized renderers/parsers without context.

        Unfortunately, this is specific to the DRF test framework.
        """
        create_response = self.client.post(
            '/people/',
            self.type_field_data,
            format='drf-extra-fields-parameterized')
        self.assertEqual(
            create_response.status_code, 201,
            'Create request did not succeed:\n{0}'.format(
                pprint.pformat(create_response.data)))
        create_json = json.loads(create_response.content.decode())
        self.assertEqual(
            create_json["name"], self.type_field_data["name"],
            'Wrong parameterized format create response results')

    def test_parameterized_format_list(self):
        """
        Test using parameterized renderers/parsers on list views.
        """
        person = models.Person.objects.create(
            name=self.person_field_data['name'])
        list_response = self.client.get(
            '/people/?format=drf-extra-fields-parameterized')
        self.assertEqual(
            list_response.status_code, 200,
            'List request did not succeed:\n{0}'.format(
                pprint.pformat(list_response.data)))
        list_json = json.loads(list_response.content.decode())
        type_field_data = dict(self.type_field_data, id=str(person.uuid))
        self.assertEqual(
            list_json[0], type_field_data,
            'Wrong parameterized format list response results')

    def test_parameterized_parser_validation(self):
        """
        Test the parameterized parser validation.
        """
        invalid_response = self.client.post(
            '/people/?format=drf-extra-fields-parameterized',
            json.dumps(self.person_field_data),
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

    def test_parameterized_format_exception(self):
        """
        Test the parameterized format handling of errors.
        """
        view = test_viewsets.ExamplePersonViewset()
        factory = test.APIRequestFactory()
        view.request = request.Request(factory.get('/'))
        view.format_kwarg = None
        view.request.accepted_renderer = (
            formats.ExampleParameterizedRenderer())
        view.request.accepted_renderer.error_serializer_class = (
            serializers.Serializer)
        exc = exceptions.APIException('example exception')
        response = view.handle_exception(exc)
        self.assertEqual(
            response.data, {}, 'Wrong exception response detail')
