import json
from django.contrib.gis.geos import GEOSGeometry
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

EMPTY_VALUES = (None, '', [], (), {})

class PointField(serializers.WritableField):
    """
    A field for handling GeoDjango Point fields as a json format.
    Expected input format:
        {
        "latitude": 49.8782482189424,
         "longitude": 24.452545489
        }

    """
    type_name = 'PointField'
    type_label = 'point'

    default_error_messages = {
        'invalid': _('Location field has wrong format. Use {"latitude": 45.67294621, "longitude": 26.43156}'),
        }

    def from_native(self, value):
        """c
        Parse json data and return a point object
        """
        if value in EMPTY_VALUES:
            return None

        value_type = type(value)
        if value_type is str or value_type is unicode:
            try:
                value = value.replace("'", '"')
                value = json.loads(value)
            except ValueError:
                msg = self.error_messages['invalid']
                raise serializers.ValidationError(msg)

        if value:
            latitude = value.get("latitude")
            longitude = value.get("longitude")
            if latitude and longitude:
                point_object = GEOSGeometry('POINT(%(longitude)s %(latitude)s)' % {
                    "longitude": longitude,
                    "latitude": latitude,
                    })
                return point_object
            msg = self.error_messages['invalid']
            raise serializers.ValidationError(msg)

    def to_native(self, value):
        """
        Transform POINT object to json.
        """
        if value is None:
            return value

        if isinstance(value, GEOSGeometry):
            value = {
                    "latitude": str(value.y),
                    "longitude": str(value.x)
                    }
        return value
