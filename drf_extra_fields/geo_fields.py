import json
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

EMPTY_VALUES = (None, '', [], (), {})
from django.contrib.gis.geos import Polygon 


class PointField(serializers.Field):
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
        'invalid': _('Enter a valid location.'),
    }

    def __init__(self, *args, **kwargs):
        self.str_points = kwargs.pop('str_points', False)
        self.srid = kwargs.pop('srid', None)
        super(PointField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        """
        Parse json data and return a point object
        """
        if value in EMPTY_VALUES and not self.required:
            return None

        if isinstance(value, str):
            try:
                value = value.replace("'", '"')
                value = json.loads(value)
            except ValueError:
                self.fail('invalid')

        if value and isinstance(value, dict):
            try:
                latitude = value.get("latitude")
                longitude = value.get("longitude")
                return GEOSGeometry('POINT(%(longitude)s %(latitude)s)' % {
                    "longitude": longitude,
                    "latitude": latitude},
                                    srid=self.srid
                )
            except (GEOSException, ValueError):
                self.fail('invalid')
        self.fail('invalid')

    def to_representation(self, value):
        """
        Transform POINT object to json.
        """
        if value is None:
            return value

        if isinstance(value, GEOSGeometry):
            value = {
                "latitude": value.y,
                "longitude": value.x
            }

        if self.str_points:
            value['longitude'] = smart_str(value.pop('longitude'))
            value['latitude'] = smart_str(value.pop('latitude'))

        return value



class PolygonField(serializers.Field):
    """
    A field for handling GeoDjango PolyGone fields as a array format.
    Expected input format:
        {
            [
                [
                    51.778564453125,
                    35.59925232772949
                ],
                [
                    50.1470947265625,
                    34.80929324176267
                ],
                [
                    52.6080322265625,
                    34.492975402501536
                ],
                [
                    51.778564453125,
                    35.59925232772949
                ]
            ]
        }

    """
    type_name = 'PolygonField'
    type_label = 'polygon'

    default_error_messages = {
        'invalid': _('Enter a valid polygon.'),
    }

    def __init__(self, *args, **kwargs):
        super(PolygonField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        """
        Parse array data and return a polygon object
        """
        if value in EMPTY_VALUES and not self.required:
            return None

        try:
            new_value = []        
            for item in value:
                item = list(map(float, item))
                new_value.append(item)
        except ValueError:
            self.fail('invalid')
        
        try:
            return Polygon(new_value)
        except (GEOSException, ValueError, TypeError):
            self.fail('invalid')
        self.fail('invalid')


    def to_representation(self, value):
        """
        Transform Polygon object to array of arrays.
        """
        if value is None:
            return value

        if isinstance(value, GEOSGeometry):
            value = value.boundary.array


        return value

