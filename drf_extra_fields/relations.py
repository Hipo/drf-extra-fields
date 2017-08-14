from django.core import exceptions

from rest_framework import serializers
from rest_framework import relations


class PresentablePrimaryKeyRelatedField(relations.PrimaryKeyRelatedField):
    """
    Override PrimaryKeyRelatedField to represent serializer data.

    Instead of a pk field of the object.
    """

    def use_pk_only_optimization(self):
        """
        Instead of sending pk only object, return full object.

        The object already retrieved from db by drf.

        This doesn't cause an extra query. It even might save from making an
        extra query on serializer.to_representation method.
        Related source codes:
        - https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/relations.py#L41
        - https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/relations.py#L132
        """  # noqa
        return False

    def __init__(self, **kwargs):
        self.presentation_serializer = kwargs.pop(
            'presentation_serializer', None)
        assert self.presentation_serializer is not None, (
            'PresentablePrimaryKeyRelatedField must provide '
            'a `presentation_serializer` argument'
        )
        super(PresentablePrimaryKeyRelatedField, self).__init__(**kwargs)

    def to_representation(self, data):
        return self.presentation_serializer(data, context=self.context).data


class PrimaryKeySourceRelatedField(relations.PrimaryKeyRelatedField):
    """
    A field for arbitrary primary key model fields.
    """

    def use_pk_only_optimization(self):
        if (getattr(self.pk_field, 'source', None) or 'pk') == 'pk':
            return True
        return False

    def bind(self, field_name, parent):
        """
        Also bind the `pk_field`.
        """
        super(PrimaryKeySourceRelatedField, self).bind(field_name, parent)

        if self.pk_field is not None:
            self.pk_field.bind('pk', self)

    def to_internal_value(self, data):
        if self.pk_field is not None:
            kwargs = {
                self.pk_field.source or 'pk':
                self.pk_field.to_internal_value(data)}
        else:
            kwargs = {'pk': data}
        try:
            return self.get_queryset().get(**kwargs)
        except exceptions.ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=kwargs)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        if getattr(self, 'pk_field', None) is not None:
            return self.pk_field.to_representation(
                self.pk_field.get_attribute(value))
        return value.pk


uuid_field = serializers.UUIDField(source='uuid')


class UUIDRelatedField(PrimaryKeySourceRelatedField):
    """
    A primary key and relationship field that uses UUIDs.
    """

    def __init__(self, **kwargs):
        """
        Use the UUID field by default.
        """
        kwargs.setdefault('pk_field', uuid_field)
        super(UUIDRelatedField, self).__init__(**kwargs)


class UUIDModelSerializer(serializers.ModelSerializer):
    """
    A serializer that uses UUIDs throughout, meant to be subclassed.
    """

    serializer_related_field = UUIDRelatedField

    class Meta:
        exclude = ('uuid', )
        # Ensure related serializers also use the UUID field
        extra_kwargs = dict(id=dict(pk_field=uuid_field))

    id = serializers.UUIDField(source='uuid', required=False)
