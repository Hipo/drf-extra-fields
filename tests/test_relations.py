import uuid

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.test import APISimpleTestCase
from .utils import (
    MockObject, MockQueryset
)

from drf_extra_fields import relations


class TestPresentablePrimaryKeyRelatedField(APISimpleTestCase):

    class PresentationSerializer(serializers.Serializer):
        def to_representation(self, instance):
            return {
                "pk": instance.pk,
                "name": instance.name
            }

    def setUp(self):

        self.queryset = MockQueryset([
            MockObject(pk=1, name='foo'),
            MockObject(pk=2, name='bar'),
            MockObject(pk=3, name='baz')
        ])
        self.instance = self.queryset.items[2]
        self.field = relations.PresentablePrimaryKeyRelatedField(
            queryset=self.queryset,
            presentation_serializer=self.PresentationSerializer
        )

    def test_representation(self):
        representation = self.field.to_representation(self.instance)
        expected_representation = self.PresentationSerializer(
            self.instance).data
        assert representation == expected_representation


class TestPrimaryKeySourceRelatedField(APISimpleTestCase):

    def setUp(self):
        """
        Create a mock object with both pk and UUID.
        """
        self.queryset = MockQueryset([
            MockObject(
                pk=1, uuid=uuid.uuid4(), name='foo')
        ])
        self.instance = self.queryset.items[0]
        self.field = relations.PrimaryKeySourceRelatedField(
            queryset=self.queryset,
            pk_field=serializers.UUIDField(source='uuid'))
        self.field_wo_source = relations.PrimaryKeySourceRelatedField(
            queryset=self.queryset)
        # Field needs to be bound
        self.serializer = serializers.Serializer()
        self.serializer.fields['id'] = self.field

    def test_representation(self):
        """
        The primary key field uses the UUID as the representation.
        """
        representation = self.field.to_representation(self.instance)
        self.assertEqual(
            representation, str(self.instance.uuid),
            'Wrong UUID as PK representation')
        self.assertEqual(
            self.field_wo_source.to_representation(self.instance),
            self.instance.pk,
            'Wrong PK as PK representation')

    def test_internal_value(self):
        """
        The primary key field uses the UUID as the internal value.
        """
        internal_value = self.field.to_internal_value(self.instance.uuid)
        self.assertEqual(
            internal_value, self.instance,
            'Wrong UUID internal value')
        self.assertEqual(
            self.field_wo_source.to_internal_value(self.instance.pk),
            self.instance,
            'Wrong PK internal value')

    def test_validation(self):
        """
        The primary key field validates the UUID.
        """
        with self.assertRaises(exceptions.ValidationError) as cm:
            self.field.to_internal_value(uuid.uuid4())
        self.assertIn(
            "does not exist",
            cm.exception.detail[0].lower(),
            'Wrong non-existent UUID validation error')

        def get(*args, **kwargs): raise TypeError()
        self.queryset.get = get
        with self.assertRaises(exceptions.ValidationError) as cm:
            self.field.to_internal_value(uuid.uuid4())
        self.assertIn(
            "incorrect type",
            cm.exception.detail[0].lower(),
            'Wrong UUID type validation error')

    def test_pk_only_optimization(self):
        """
        The primary key source field uses the pk optimization correctly.
        """
        self.assertFalse(
            self.field.use_pk_only_optimization(),
            'Used PK optimization when source was given')
        self.assertTrue(
            self.field_wo_source.use_pk_only_optimization(),
            'Did not use PK optimization when no source was given')
