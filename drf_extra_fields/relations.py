from rest_framework.relations import PrimaryKeyRelatedField


class PresentablePrimaryKeyRelatedField(PrimaryKeyRelatedField):
    """
    Override PrimaryKeyRelatedField to represent serializer data instead of a pk field of the object.
    """

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

    def __init__(self, **kwargs):
        self.presentation_serializer = kwargs.pop('presentation_serializer', None)
        assert self.presentation_serializer is not None, (
            'PresentablePrimaryKeyRelatedField must provide a `presentation_serializer` argument'
        )
        super(PresentablePrimaryKeyRelatedField, self).__init__(**kwargs)

    def to_representation(self, data):
        return self.presentation_serializer(data, context=self.context).data
