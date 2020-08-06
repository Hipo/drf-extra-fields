import django
from django.contrib.postgres.fields import (
    DateRangeField,
    DateTimeRangeField,
    IntegerRangeField,
    DecimalRangeField
)
from django.db import models
from django.test import TestCase
from rest_framework import serializers
import pytest

from drf_extra_fields import compat


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


class PostgreFieldsModel(models.Model):
    date_range_field = DateRangeField()
    datetime_range_field = DateTimeRangeField()
    integer_range_field = IntegerRangeField()
    decimal_range_field = DecimalRangeField()

    class Meta:
        app_label = 'tests'


@pytest.mark.skipif(django.VERSION >= (3, 1) or compat.FloatRangeField is None,
                    reason='FloatRangeField deprecated on django 3.1 ')
class TestFloatRangeFieldMapping(TestCase):

    def test_float_range_field(self):
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


class TestPosgreFieldMappings(TestCase):
    def test_regular_fields(self):
        """
        Model fields should map to their equivalent serializer fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = PostgreFieldsModel
                fields = ("date_range_field", "datetime_range_field",
                          "integer_range_field", "decimal_range_field")

        expected = dedent("""
            TestSerializer():
                date_range_field = DateRangeField()
                datetime_range_field = DateTimeRangeField()
                integer_range_field = IntegerRangeField()
                decimal_range_field = DecimalRangeField()
        """)

        self.assertEqual(repr(TestSerializer()), expected)
