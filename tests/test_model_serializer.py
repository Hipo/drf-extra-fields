from django.db import models
from django.test import TestCase


from django.contrib.postgres.fields import DateRangeField, DateTimeRangeField, IntegerRangeField
from drf_extra_fields import compat
from rest_framework import serializers


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


class RegularFieldsModel(models.Model):
    date_range_field = DateRangeField()
    datetime_range_field = DateTimeRangeField()
    integer_range_field = IntegerRangeField()

    class Meta:
        app_label = 'tests'


if compat.FloatRangeField:
    class TestFloatRangeFieldMapping(TestCase):

        def test_decimal_range_field(self):
            class FloatRangeFieldModel(models.Model):
                float_range_field = compat.FloatRangeField()

                class Meta:
                    app_label = 'tests'

            class TestSerializer(serializers.ModelSerializer):
                class Meta:
                    model = FloatRangeFieldModel
                    fields = ("float_range_field",)

            expected = dedent("""
            TestSerializer():
                float_range_field = FloatRangeField()
            """)
            self.assertEqual(repr(TestSerializer()), expected)


if compat.DecimalRangeField:
    class TestDecimalRangeFieldMapping(TestCase):
        def test_decimal_range_field(self):
            class DecimalRangeFieldModel(models.Model):
                decimal_range_field = compat.DecimalRangeField()

                class Meta:
                    app_label = 'tests'

            class TestSerializer(serializers.ModelSerializer):
                class Meta:
                    model = DecimalRangeFieldModel
                    fields = ("decimal_range_field",)

            expected = dedent("""
            TestSerializer():
                decimal_range_field = DecimalRangeField()
            """)
            self.assertEqual(repr(TestSerializer()), expected)


class TestRegularFieldMappings(TestCase):
    def test_regular_fields(self):
        """
        Model fields should map to their equivalent serializer fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ("date_range_field", "datetime_range_field", "integer_range_field")

        expected = dedent("""
            TestSerializer():
                date_range_field = DateRangeField()
                datetime_range_field = DateTimeRangeField()
                integer_range_field = IntegerRangeField()
        """)

        self.assertEqual(repr(TestSerializer()), expected)
