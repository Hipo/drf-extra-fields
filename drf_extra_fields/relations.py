from collections import OrderedDict

from django.utils.module_loading import import_string
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField


class PresentableRelatedFieldMixin(object):
    def __init__(self, **kwargs):
        self.presentation_serializer = kwargs.pop("presentation_serializer", None)
        self.presentation_serializer_kwargs = kwargs.pop(
            "presentation_serializer_kwargs", dict()
        )
        assert self.presentation_serializer is not None, (
            self.__class__.__name__
            + " must provide a `presentation_serializer` argument"
        )
        super(PresentableRelatedFieldMixin, self).__init__(**kwargs)

    def use_pk_only_optimization(self):
        """
        Instead of sending pk only object, return full object. The object already retrieved from db by drf.
        This doesn't cause an extra query.
        It even might save from making an extra query on serializer.to_representation method.
        Related source codes:
        - https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/relations.py#L41
        - https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/relations.py#L132
        """
        return False

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([(item.pk, self.display_value(item)) for item in queryset])

    def to_representation(self, data):
        if isinstance(self.presentation_serializer, str):
            self.presentation_serializer = import_string(self.presentation_serializer)

        return self.presentation_serializer(
            data, context=self.context, **self.presentation_serializer_kwargs
        ).data


class PresentablePrimaryKeyRelatedField(
    PresentableRelatedFieldMixin, PrimaryKeyRelatedField
):
    """
    Override PrimaryKeyRelatedField to represent serializer data instead of a pk field of the object.
    """

    pass


class PresentableSlugRelatedField(PresentableRelatedFieldMixin, SlugRelatedField):
    """
    Override SlugRelatedField to represent serializer data instead of a slug field of the object.
    """

    pass
