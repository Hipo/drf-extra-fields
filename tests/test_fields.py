import datetime
from django.test import TestCase
from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField
from drf_extra_fields.fields import Base64ImageField


class UploadedBase64Image(object):
    def __init__(self, file=None, created=None):
        self.file = file
        self.created = created or datetime.datetime.now()


class UploadedBase64ImageSerializer(serializers.Serializer):
    file = Base64ImageField(required=False)
    created = serializers.DateTimeField()

    def update(self, instance, validated_data):
        instance.file = validated_data['file']
        return instance

    def create(self, validated_data):
        return UploadedBase64Image(**validated_data)


class Base64ImageSerializerTests(TestCase):

    def test_create(self):
        """
        Test for creating Base64 image in the server side
        """
        now = datetime.datetime.now()
        file = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        serializer = UploadedBase64ImageSerializer(data={'created': now, 'file': file})
        uploaded_image = UploadedBase64Image(file=file, created=now)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], uploaded_image.created)
        self.assertFalse(serializer.validated_data is uploaded_image)

    def test_validation_error_with_non_file(self):
        """
        Passing non-base64 should raise a validation error.
        """
        now = datetime.datetime.now()
        errmsg = "Please upload a valid image."
        serializer = UploadedBase64ImageSerializer(data={'created': now, 'file': 'abc'})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'file': [errmsg]})

    def test_remove_with_empty_string(self):
        """
        Passing empty string as data should cause image to be removed
        """
        now = datetime.datetime.now()
        file = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        uploaded_image = UploadedBase64Image(file=file, created=now)
        serializer = UploadedBase64ImageSerializer(instance=uploaded_image, data={'created': now, 'file': ''})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], uploaded_image.created)
        self.assertIsNone(serializer.validated_data['file'])


class SavePoint(object):
    def __init__(self, point=None, created=None):
        self.point = point
        self.created = created or datetime.datetime.now()


class PointSerializer(serializers.Serializer):
    point = PointField(required=False)
    created = serializers.DateTimeField()

    def update(self, instance, validated_data):
        instance.point = validated_data['point']
        return instance

    def create(self, validated_data):
        return SavePoint(**validated_data)


class PointSerializerTest(TestCase):

    def test_create(self):
        """
        Test for creating Point field in the server side
        """
        now = datetime.datetime.now()
        point = {
            "latitude": 49.8782482189424,
            "longitude": 24.452545489
        }
        serializer = PointSerializer(data={'created': now, 'point': point})
        saved_point = SavePoint(point=point, created=now)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], saved_point.created)
        self.assertFalse(serializer.validated_data is saved_point)

    def test_validation_error_with_non_file(self):
        """
        Passing non-dict contains latitude and longitude should raise a validation error.
        """
        now = datetime.datetime.now()
        serializer = PointSerializer(data={'created': now, 'point': '123'})
        self.assertFalse(serializer.is_valid())

    def test_remove_with_empty_string(self):
        """
        Passing empty string as data should cause point to be removed
        """
        now = datetime.datetime.now()
        point = {
            "latitude": 49.8782482189424,
            "longitude": 24.452545489
        }
        saved_point = SavePoint(point=point, created=now)
        serializer = PointSerializer(data={'created': now, 'point': ''})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], saved_point.created)
        self.assertIsNone(serializer.validated_data['point'])
