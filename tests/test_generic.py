import uuid

from rest_framework import exceptions
from rest_framework import request
from rest_framework import reverse
from rest_framework import serializers
from rest_framework import test

from drf_extra_fields import generic
from drf_extra_fields.runtests import models
from drf_extra_fields.runtests import serializers as test_serializers


class AllFieldsSerializer(
        test_serializers.ExamplePersonSerializer,
        generic.HyperlinkedGenericRelationsSerializer):
    """
    A simple model serializer that includes all fields.
    """

    class Meta(test_serializers.ExamplePersonSerializer.Meta):
        fields = serializers.ALL_FIELDS


class TestGenericHyperlinkRelations(test.APITestCase):
    """
    Test generic hyperlinked relations.
    """

    def setUp(self):
        """
        Create the necessary instances and a request.
        """
        self.person = models.Person.objects.create()
        self.person.related_to = self.person
        self.person.save()
        self.url = 'http://testserver/people/{0}/'.format(str(
            self.person.uuid))

        factory = test.APIRequestFactory()
        self.request = request.Request(factory.post(
            reverse.reverse(
                models.Person._meta.model_name + '-detail',
                kwargs=dict(uuid=self.person.uuid))))

    def test_to_representation(self):
        """
        Test generic hyperlinked relations representation.
        """
        serializer = AllFieldsSerializer(
            instance=self.person, context=dict(request=self.request))
        self.assertIn(
            'related_to', serializer.data, 'Missing generic relation')
        self.assertEqual(
            serializer.data['related_to'], self.url,
            'Wrong generic relation UUID value')

    def test_to_internal_value(self):
        """
        Test generic hyperlinked relations deserialization.
        """
        new_url = 'http://testserver/people/{0}/'.format(str(uuid.uuid4()))
        serializer = AllFieldsSerializer(
            data={
                "name": "Foo Name", "articles": [],
                "related_to": new_url},
            context=dict(
                request=self.request, allow_nonexistent_generic=True))
        serializer.is_valid(raise_exception=True)
        self.assertIn(
            'related_to', serializer.data, 'Missing generic relation')
        self.assertEqual(
            serializer.data['related_to'], None,
            'Wrong generic relation UUID value')

    def test_incorrect_type(self):
        """
        Test generic hyperlinked related field with wrong type.
        """
        serializer = AllFieldsSerializer(
            data={"name": "Foo Name", "articles": [], "related_to": 1},
            context=dict(request=self.request))
        with self.assertRaises(exceptions.ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn(
            'related_to', cm.exception.detail,
            'Missing generic relation type validation error')
        self.assertIn(
            'incorrect type',
            cm.exception.detail['related_to'][0].lower(),
            'Wrong generic relation type validation error')
        self.assertIn(
            'related_to', serializer.errors,
            'Missing generic relation type validation error')
        self.assertIn(
            'incorrect type',
            serializer.errors['related_to'][0].lower(),
            'Wrong generic relation type validation error')

    def test_does_not_exist(self):
        """
        Test generic hyperlinked related field does not exist error.
        """
        serializer = AllFieldsSerializer(
            data={
                "name": "Foo Name", "articles": [],
                "related_to":
                'http://testserver/people/{0}/'.format(str(uuid.uuid4()))},
            context=dict(request=self.request))
        with self.assertRaises(exceptions.ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn(
            'related_to', cm.exception.detail,
            'Missing generic relation does not exist validation error')
        self.assertIn(
            'does not exist',
            cm.exception.detail['related_to'][0].lower(),
            'Wrong generic relation does not exist validation error')
        self.assertIn(
            'related_to', serializer.errors,
            'Missing generic relation does not exist validation error')
        self.assertIn(
            'does not exist',
            serializer.errors['related_to'][0].lower(),
            'Wrong generic relation does not exist validation error')

    def test_no_match(self):
        """
        Test generic hyperlinked related field 404 error.
        """
        serializer = AllFieldsSerializer(
            data={
                "name": "Foo Name", "articles": [],
                "related_to":
                'http://testserver/foo/{0}/'.format(str(self.person.uuid))},
            context=dict(request=self.request))
        with self.assertRaises(exceptions.ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn(
            'related_to', cm.exception.detail,
            'Missing generic relation 404 validation error')
        self.assertIn(
            'no url match',
            cm.exception.detail['related_to'][0].lower(),
            'Wrong generic relation 404 validation error')
        self.assertIn(
            'related_to', serializer.errors,
            'Missing generic relation 404 validation error')
        self.assertIn(
            'no url match',
            serializer.errors['related_to'][0].lower(),
            'Wrong generic relation 404 validation error')
