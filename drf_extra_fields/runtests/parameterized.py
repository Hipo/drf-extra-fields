from drf_extra_fields import parameterized

from . import serializers


class ExampleParameterizedRenderer(parameterized.ParameterizedRenderer):
    """
    ExampleParameterized JSON format renderer
    """
    media_type = 'application/vnd.drf_extra_fields+json'
    format = 'drf-extra-fields-parameterized'

    serializer_class = serializers.ExampleUserSerializer


class ExampleParameterizedParser(parameterized.ParameterizedParser):
    """
    ExampleParameterized JSON format parser
    """
    media_type = ExampleParameterizedRenderer.media_type
    renderer_class = ExampleParameterizedRenderer

    serializer_class = ExampleParameterizedRenderer.serializer_class
