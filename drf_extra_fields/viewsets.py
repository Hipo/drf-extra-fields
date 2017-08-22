from rest_framework import viewsets


class UUIDModelViewSet(viewsets.ModelViewSet):
    """
    A model viewset that uses a `UUID` field in the URLS.
    """

    lookup_field = 'uuid'
    lookup_value_regex = '[0-9a-f-]{36}'
