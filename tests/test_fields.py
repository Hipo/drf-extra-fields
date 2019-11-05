import datetime
import base64
import imghdr
import os

import django
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from mock import patch
import pytz
from rest_framework import serializers

from drf_extra_fields import compat
from drf_extra_fields.geo_fields import PointField
from drf_extra_fields.fields import (
    Base64ImageField,
    Base64FileField,
    DateRangeField,
    DateTimeRangeField,
    FloatRangeField,
    HybridImageField,
    IntegerRangeField,
)


import pytest

UNDETECTABLE_BY_IMGHDR_SAMPLE = """data:image/jpeg;base64,
/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD
/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAAQABADASIAAhEBAxEB
/8QAFgABAQEAAAAAAAAAAAAAAAAABwQF/8QAJBAAAQQBBAICAwAAAAAAAAAAAQIDBAYFBwgSExEiABQJMTL/xAAVAQEBAAAAAAAAAAAAAAAAAAAABv
/EACMRAAECBQMFAAAAAAAAAAAAAAECEQMEBQYhABIxFRZhgeH/2gAMAwEAAhEDEQA/ABSm0mobc8HmExLUlRzzEWPkJWW
+ulrsaUVAseUgslSlH9LKuPryIKuWPZdskzXmm3fX5m2nF4GlVxx/HOpx4ks51+MiU/Iaad7UcUo4tILoS4kqcWkezS0hO
/HvuRp0rO6hWnWO1UisZVuFi4GFeyEpmGepa5S5SWVPuciFKRFLgSrwetnyPIB+Vb4N9mKhQMzo5po9XLdDs9d6ZVix2VEhiL9kuNPxw2gEKcDQ
/rs8AuA8VAe0vdl7VOYn+27flGAUgmITjbhSmCg3BYlyeWDkMolvw4KOp1KM6iCNvngZHwetf//Z """


class UploadedBase64Image(object):
    def __init__(self, file=None, created=None):
        self.file = file
        self.created = created or datetime.datetime.now()


class UploadedBase64File(UploadedBase64Image):
    pass


class DownloadableBase64Image(object):
    class ImageFieldFile(object):
        def __init__(self, path):
            self.path = path

    def __init__(self, image_path):
        self.image = self.ImageFieldFile(path=image_path)


class DownloadableBase64File(object):
    class FieldFile(object):
        def __init__(self, path):
            self.path = path

    def __init__(self, file_path):
        self.file = self.FieldFile(path=file_path)


class UploadedBase64ImageSerializer(serializers.Serializer):
    file = Base64ImageField(required=False)
    created = serializers.DateTimeField()

    def update(self, instance, validated_data):
        instance.file = validated_data['file']
        return instance

    def create(self, validated_data):
        return UploadedBase64Image(**validated_data)


class DownloadableBase64ImageSerializer(serializers.Serializer):
    image = Base64ImageField(represent_in_base64=True)


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

    def test_create_with_base64_prefix(self):
        """
        Test for creating Base64 image in the server side
        """
        now = datetime.datetime.now()
        file = 'data:image/gif;base64,R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
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
        serializer = UploadedBase64ImageSerializer(data={'created': now,
                                                         'file': 'abc'})
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

    def test_fallback_to_pil_if_not_detected_by_imghdr(self):
        """
        Passing a sample image which goes undetected by imghdr should
        still be detected by PIL.
        """
        now = datetime.datetime.now()
        file = UNDETECTABLE_BY_IMGHDR_SAMPLE

        # check image is undetectable by imghdr
        self.assertIsNone(imghdr.what('test.jpeg', base64.b64decode(file)))

        uploaded_image = UploadedBase64Image(file=file, created=now)
        serializer = UploadedBase64ImageSerializer(instance=uploaded_image, data={'created': now, 'file': file})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], uploaded_image.created)
        self.assertIsNotNone(serializer.validated_data['file'])

    def test_download(self):
        encoded_source = 'R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs='

        with open('im.jpg', 'wb') as im_file:
            im_file.write(base64.b64decode(encoded_source))
        image = DownloadableBase64Image(os.path.abspath('im.jpg'))
        serializer = DownloadableBase64ImageSerializer(image)

        try:
            self.assertEqual(serializer.data['image'], encoded_source)
        finally:
            os.remove('im.jpg')

    def test_hybrid_image_field(self):
        field = HybridImageField()
        with patch('drf_extra_fields.fields.Base64FieldMixin') as mixin_patch:
            field.to_internal_value({})
            self.assertTrue(mixin_patch.to_internal_value.called)

        with patch('drf_extra_fields.fields.Base64FieldMixin') as mixin_patch:
            mixin_patch.to_internal_value.side_effect = ValidationError('foobar')
            with patch('drf_extra_fields.fields.ImageField') as image_patch:
                field.to_internal_value({})
                self.assertTrue(mixin_patch.to_internal_value.called)
                self.assertTrue(image_patch.to_internal_value.called)


class PDFBase64FileField(Base64FileField):
    ALLOWED_TYPES = ('pdf',)

    def get_file_extension(self, filename, decoded_file):
        return 'pdf'


class UploadedBase64FileSerializer(serializers.Serializer):
    file = PDFBase64FileField(required=False)
    created = serializers.DateTimeField()

    def update(self, instance, validated_data):
        instance.file = validated_data['file']
        return instance

    def create(self, validated_data):
        return UploadedBase64File(**validated_data)


class DownloadableBase64FileSerializer(serializers.Serializer):
    file = PDFBase64FileField(represent_in_base64=True)


class Base64FileSerializerTests(TestCase):
    def test_create(self):
        """
        Test for creating Base64 file in the server side
        """
        now = datetime.datetime.now()
        file = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        serializer = UploadedBase64FileSerializer(data={'created': now, 'file': file})
        uploaded_file = UploadedBase64File(file=file, created=now)
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], uploaded_file.created)
        self.assertFalse(serializer.validated_data is uploaded_file)

    def test_create_with_base64_prefix(self):
        """
        Test for creating Base64 file in the server side
        """
        now = datetime.datetime.now()
        file = 'data:image/gif;base64,R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        serializer = UploadedBase64FileSerializer(data={'created': now, 'file': file})
        uploaded_file = UploadedBase64File(file=file, created=now)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], uploaded_file.created)
        self.assertFalse(serializer.validated_data is uploaded_file)

    def test_validation_error_with_non_file(self):
        """
        Passing non-base64 should raise a validation error.
        """
        now = datetime.datetime.now()
        errmsg = "Please upload a valid file."
        serializer = UploadedBase64FileSerializer(data={'created': now, 'file': 'abc'})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'file': [errmsg]})

    def test_remove_with_empty_string(self):
        """
        Passing empty string as data should cause file to be removed
        """
        now = datetime.datetime.now()
        file = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        uploaded_file = UploadedBase64File(file=file, created=now)
        serializer = UploadedBase64FileSerializer(instance=uploaded_file, data={'created': now, 'file': ''})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['created'], uploaded_file.created)
        self.assertIsNone(serializer.validated_data['file'])

    def test_download(self):
        encoded_source = 'R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs='

        with open('im.jpg', 'wb') as im_file:
            im_file.write(base64.b64decode(encoded_source))
        file = DownloadableBase64File(os.path.abspath('im.jpg'))
        serializer = DownloadableBase64FileSerializer(file)

        try:
            self.assertEqual(serializer.data['file'], encoded_source)
        finally:
            os.remove('im.jpg')


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


class StringPointSerializer(PointSerializer):
    point = PointField(required=False, str_points=True)


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

    def test_empty_latitude(self):
        now = datetime.datetime.now()
        point = {
            "latitude": 49.8782482189424,
            "longitude": ""
        }
        serializer = PointSerializer(data={'created': now, 'point': point})
        self.assertFalse(serializer.is_valid())

    def test_invalid_latitude(self):
        now = datetime.datetime.now()
        point = {
            "latitude": 49.8782482189424,
            "longitude": "fdff"
        }
        serializer = PointSerializer(data={'created': now, 'point': point})
        self.assertFalse(serializer.is_valid())

    def test_serialization(self):
        """
        Regular JSON serialization should output float values
        """
        from django.contrib.gis.geos import Point
        now = datetime.datetime.now()
        point = Point(24.452545489, 49.8782482189424)
        saved_point = SavePoint(point=point, created=now)
        serializer = PointSerializer(saved_point)
        self.assertEqual(serializer.data['point'], {'latitude': 49.8782482189424, 'longitude': 24.452545489})

    def test_str_points_serialization(self):
        """
        PointField with str_points=True should output string values
        """
        from django.contrib.gis.geos import Point
        now = datetime.datetime.now()
        # test input is shortened due to string conversion rounding
        # gps has at max 8 decimals, so it doesn't make a difference
        point = Point(24.452545489, 49.8782482189)
        saved_point = SavePoint(point=point, created=now)
        serializer = StringPointSerializer(saved_point)
        self.assertEqual(serializer.data['point'], {'latitude': '49.8782482189', 'longitude': '24.452545489'})


# Backported from django_rest_framework/tests/test_fields.py
def get_items(mapping_or_list_of_two_tuples):
    # Tests accept either lists of two tuples, or dictionaries.
    if isinstance(mapping_or_list_of_two_tuples, dict):
        # {value: expected}
        return mapping_or_list_of_two_tuples.items()
    # [(value, expected), ...]
    return mapping_or_list_of_two_tuples


class FieldValues:
    """
    Base class for testing valid and invalid input values.
    """
    def test_valid_inputs(self):
        """
        Ensure that valid values return the expected validated data.
        """
        for input_value, expected_output in get_items(self.valid_inputs):
            assert self.field.run_validation(input_value) == expected_output

    def test_invalid_inputs(self):
        """
        Ensure that invalid values raise the expected validation error.
        """
        for input_value, expected_failure in get_items(self.invalid_inputs):
            with pytest.raises(serializers.ValidationError) as exc_info:
                self.field.run_validation(input_value)
            assert exc_info.value.detail == expected_failure

    def test_outputs(self):
        for output_value, expected_output in get_items(self.outputs):
            assert self.field.to_representation(output_value) == expected_output

# end of backport


@pytest.mark.skipif(django.VERSION < (1, 8) or compat.postgres_fields is None,
                    reason='RangeField is only available for django1.8+'
                    ' and with psycopg2.')
class TestIntegerRangeField(FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    if compat.NumericRange is not None:
        valid_inputs = [
            ({'lower': '1', 'upper': 2, 'bounds': '[)'},
             compat.NumericRange(**{'lower': 1, 'upper': 2, 'bounds': '[)'})),
            ({'lower': 1, 'upper': 2},
             compat.NumericRange(**{'lower': 1, 'upper': 2})),
            ({'lower': 1},
             compat.NumericRange(**{'lower': 1})),
            ({'upper': 1},
             compat.NumericRange(**{'upper': 1})),
            ({'empty': True},
             compat.NumericRange(**{'empty': True})),
            ({}, compat.NumericRange()),
        ]
        invalid_inputs = [
            ({'lower': 'a'}, ['A valid integer is required.']),
            ('not a dict', ['Expected a dictionary of items but got type "str".']),
            ({'foo': 'bar'}, ['Extra content not allowed "foo".']),
            ({'lower': 20, 'upper': 10},
             ['The start of the range must not exceed the end of the range.']),
        ]
        outputs = [
            (compat.NumericRange(**{'lower': '1', 'upper': '2'}),
             {'lower': 1, 'upper': 2, 'bounds': '[)'}),
            (compat.NumericRange(**{'empty': True}), {'empty': True}),
            (compat.NumericRange(), {'bounds': '[)', 'lower': None, 'upper': None}),
        ]
    field = IntegerRangeField()

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            IntegerRangeField(child=serializers.IntegerField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )


@pytest.mark.skipif(django.VERSION < (1, 8) or compat.postgres_fields is None,
                    reason='RangeField is only available for django1.8+'
                    ' and with psycopg2.')
class TestFloatRangeField(FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    if compat.NumericRange is not None:
        valid_inputs = [
            ({'lower': '1', 'upper': 2., 'bounds': '[)'},
             compat.NumericRange(**{'lower': 1., 'upper': 2., 'bounds': '[)'})),
            ({'lower': 1., 'upper': 2.},
             compat.NumericRange(**{'lower': 1, 'upper': 2})),
            ({'lower': 1},
             compat.NumericRange(**{'lower': 1})),
            ({'upper': 1},
             compat.NumericRange(**{'upper': 1})),
            ({'empty': True},
             compat.NumericRange(**{'empty': True})),
            ({}, compat.NumericRange()),
        ]
        invalid_inputs = [
            ({'lower': 'a'}, ['A valid number is required.']),
            ('not a dict', ['Expected a dictionary of items but got type "str".']),
            ({'lower': 20.0, 'upper': 10.0},
             ['The start of the range must not exceed the end of the range.']),
        ]
        outputs = [
            (compat.NumericRange(**{'lower': '1.1', 'upper': '2'}),
             {'lower': 1.1, 'upper': 2, 'bounds': '[)'}),
            (compat.NumericRange(**{'empty': True}), {'empty': True}),
            (compat.NumericRange(), {'bounds': '[)', 'lower': None, 'upper': None}),
        ]
    field = FloatRangeField()

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            FloatRangeField(child=serializers.IntegerField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )


@pytest.mark.skipif(django.VERSION < (1, 8) or compat.postgres_fields is None,
                    reason='RangeField is only available for django1.8+'
                    ' and with psycopg2.')
@override_settings(USE_TZ=True)
class TestDateTimeRangeField(TestCase, FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    if compat.DateTimeTZRange is not None:
        valid_inputs = [
            ({'lower': '2001-01-01T13:00:00Z',
              'upper': '2001-02-02T13:00:00Z',
              'bounds': '[)'},
             compat.DateTimeTZRange(
                 **{'lower': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=pytz.utc),
                    'upper': datetime.datetime(2001, 2, 2, 13, 00, tzinfo=pytz.utc),
                    'bounds': '[)'})),
            ({'upper': '2001-02-02T13:00:00Z',
              'bounds': '[)'},
             compat.DateTimeTZRange(
                 **{'upper': datetime.datetime(2001, 2, 2, 13, 00, tzinfo=pytz.utc),
                    'bounds': '[)'})),
            ({'lower': '2001-01-01T13:00:00Z',
              'bounds': '[)'},
             compat.DateTimeTZRange(
                 **{'lower': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=pytz.utc),
                    'bounds': '[)'})),
            ({'empty': True},
             compat.DateTimeTZRange(**{'empty': True})),
            ({}, compat.DateTimeTZRange()),
        ]
        invalid_inputs = [
            ({'lower': 'a'}, ['Datetime has wrong format. Use one of these'
                              ' formats instead: '
                              'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].']),
            ('not a dict', ['Expected a dictionary of items but got type "str".']),
            (
                {
                    'lower': datetime.datetime(2001, 2, 2, 13, 00, tzinfo=pytz.utc),
                    'upper': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=pytz.utc),
                },
                ['The start of the range must not exceed the end of the range.'],
            ),
        ]
        outputs = [
            (compat.DateTimeTZRange(
                **{'lower': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=pytz.utc),
                   'upper': datetime.datetime(2001, 2, 2, 13, 00, tzinfo=pytz.utc)}),
                {'lower': '2001-01-01T13:00:00Z',
                 'upper': '2001-02-02T13:00:00Z',
                 'bounds': '[)'}),
            (compat.DateTimeTZRange(**{'empty': True}),
             {'empty': True}),
            (compat.DateTimeTZRange(),
             {'bounds': '[)', 'lower': None, 'upper': None}),
        ]
    field = DateTimeRangeField()

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            DateTimeRangeField(child=serializers.IntegerField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )


@pytest.mark.skipif(django.VERSION < (1, 8) or compat.postgres_fields is None,
                    reason='RangeField is only available for django1.8+'
                    ' and with psycopg2.')
class TestDateRangeField(FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    if compat.DateRange is not None:
        valid_inputs = [
            ({'lower': '2001-01-01',
              'upper': '2001-02-02',
              'bounds': '[)'},
             compat.DateRange(
                 **{'lower': datetime.date(2001, 1, 1),
                    'upper': datetime.date(2001, 2, 2),
                    'bounds': '[)'})),
            ({'upper': '2001-02-02',
              'bounds': '[)'},
             compat.DateRange(
                 **{'upper': datetime.date(2001, 2, 2),
                    'bounds': '[)'})),
            ({'lower': '2001-01-01',
              'bounds': '[)'},
             compat.DateRange(
                 **{'lower': datetime.date(2001, 1, 1),
                    'bounds': '[)'})),
            ({'empty': True},
             compat.DateRange(**{'empty': True})),
            ({}, compat.DateRange()),
        ]
        invalid_inputs = [
            ({'lower': 'a'}, ['Date has wrong format. Use one of these'
                              ' formats instead: '
                              'YYYY-MM-DD.']),
            ('not a dict', ['Expected a dictionary of items but got type "str".']),
            (
                {'lower': datetime.date(2001, 2, 2),
                 'upper': datetime.date(2001, 1, 1)},
                ['The start of the range must not exceed the end of the range.']
            ),
        ]
        outputs = [
            (compat.DateRange(
                **{'lower': datetime.date(2001, 1, 1),
                   'upper': datetime.date(2001, 2, 2)}),
                {'lower': '2001-01-01',
                 'upper': '2001-02-02',
                 'bounds': '[)'}),
            (compat.DateRange(**{'empty': True}),
             {'empty': True}),
            (compat.DateRange(), {'bounds': '[)', 'lower': None, 'upper': None}),
        ]
    field = DateRangeField()

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            DateRangeField(child=serializers.IntegerField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )
