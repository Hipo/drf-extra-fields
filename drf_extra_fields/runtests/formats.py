from rest_framework import renderers
from rest_framework import parsers

from . import serializers


class ExampleParameterizedRenderer(renderers.JSONRenderer):
    """
    ExampleParameterized JSON format renderer
    """
    media_type = 'application/vnd.drf_extra_fields+json'
    format = 'drf-extra-fields-parameterized'

    serializer_class = serializers.ExampleTypeFieldSerializer


class ExampleParameterizedParser(parsers.JSONParser):
    """
    ExampleParameterized JSON format parser
    """
    media_type = ExampleParameterizedRenderer.media_type
