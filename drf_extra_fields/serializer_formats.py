"""
Support for defining JSON formats using DRF serializers.
"""

from rest_framework import exceptions
from rest_framework import generics
from rest_framework import viewsets

from . import viewsets as extra_viewsets


class FormatAPIView(object):
    """
    Use format-specific serializers based on DRF content negotiation.
    """

    def get_serializer_class(self):
        """
        Use the format's renderer `serializer_class` if available.
        """
        renderer_class = getattr(
            getattr(getattr(
                self, 'request', None), 'accepted_renderer', None),
            'serializer_class', None)
        if renderer_class is not None:
            return renderer_class

        return super(FormatAPIView, self).get_serializer_class()

    def handle_exception(self, exc):
        """
        Use the format's renderer `error_serializer_class` if available.
        """
        response = super(FormatAPIView, self).handle_exception(exc)
        serializer_class = getattr(
            self.request.accepted_renderer, 'error_serializer_class', None)
        if serializer_class is None:
            return response

        instance = exceptions.APIException(
            detail=response.data, code=response.status)
        serializer = serializer_class(
            instance=instance, context=self.get_serializer_context())
        response.data = serializer.data
        return response


class GenericAPIView(FormatAPIView, generics.GenericAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class CreateAPIView(FormatAPIView, generics.CreateAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class ListAPIView(FormatAPIView, generics.ListAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class RetrieveAPIView(FormatAPIView, generics.RetrieveAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class DestroyAPIView(FormatAPIView, generics.DestroyAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class UpdateAPIView(FormatAPIView, generics.UpdateAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class ListCreateAPIView(FormatAPIView, generics.ListCreateAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class RetrieveUpdateAPIView(FormatAPIView, generics.RetrieveUpdateAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class RetrieveDestroyAPIView(FormatAPIView, generics.RetrieveDestroyAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class RetrieveUpdateDestroyAPIView(
        FormatAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class GenericViewSet(FormatAPIView, viewsets.GenericViewSet):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class ReadOnlyModelViewSet(FormatAPIView, viewsets.ReadOnlyModelViewSet):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class ModelViewSet(FormatAPIView, viewsets.ModelViewSet):
    """
    Use format-specific serializers based on DRF content negotiation.
    """


class UUIDModelViewSet(FormatAPIView, extra_viewsets.UUIDModelViewSet):
    """
    Use format-specific serializers based on DRF content negotiation.
    """
