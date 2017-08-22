from django.core import exceptions
from django.utils import functional
from django.contrib.contenttypes import fields as ct_fields
from django.utils.six.moves.urllib import parse as urlparse

from rest_framework.utils import field_mapping
from rest_framework import reverse
from rest_framework import serializers
from rest_framework import relations
from rest_framework import compat


class HyperlinkedGenericRelationsField(relations.HyperlinkedRelatedField):
    """
    Determine the content type from the URL or model field.
    """

    def __init__(self, **kwargs):
        """
        Don't require anything type-specific on instantiation.
        """
        self.view_name = None

        # Duplicate needed bits from relations.HyperlinkedRelatedField
        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop(
            'lookup_url_kwarg', self.lookup_field)
        self.format = kwargs.pop('format', None)
        self.reverse = reverse.reverse

        super(serializers.HyperlinkedRelatedField, self).__init__(**kwargs)

    def get_queryset(self, match=None):
        """
        Infer the query set from the type.
        """
        if match is not None:
            return match.func.cls().get_queryset()

    def to_internal_value(self, data):
        """
        Resolve the URL without verifying the view name.
        """
        try:
            http_prefix = data.startswith(('http:', 'https:'))
        except AttributeError:
            self.fail('incorrect_type', data_type=type(data).__name__)

        if http_prefix:
            # If needed convert absolute URLs to relative path
            data = urlparse.urlparse(data).path
            prefix = compat.get_script_prefix()
            if data.startswith(prefix):
                data = '/' + data[len(prefix):]

        try:
            match = compat.resolve(data)
        except compat.Resolver404:
            self.fail('no_match')

        lookup_value = match.kwargs[self.lookup_url_kwarg]
        lookup_kwargs = {self.lookup_field: lookup_value}
        queryset = self.get_queryset(match)
        try:
            return queryset.get(**lookup_kwargs)
        except (exceptions.ObjectDoesNotExist, TypeError, ValueError):
            if not self.context.get('allow_nonexistent_generic', False):
                self.fail('does_not_exist')
            return queryset.model(**lookup_kwargs)

    def to_representation(self, value):
        """
        Lookup the view to use for URL based on the type.
        """
        self.view_name = field_mapping.get_detail_view_name(type(value))
        try:
            return super(
                HyperlinkedGenericRelationsField, self).to_representation(
                    value)
        finally:
            self.view_name = None


class HyperlinkedGenericRelationsSerializer(serializers.ModelSerializer):
    """
    Serialize `GenericForeignKey` model fields/relationships as hyperlinks.

    We use hyperlinks as a "default" because it's the only relationship type
    included with DRF that already includes a reference to the content type by
    doing a reverse lookup on the hyperlink and using the viewset's queryset.
    """

    serializer_generic_related_field = HyperlinkedGenericRelationsField

    @functional.cached_property
    def generic_relations(self):
        """
        Names of all the `GenericForeignKey` fields/relationships.
        """
        return [
            field for field in
            self.Meta.model._meta.concrete_model._meta.virtual_fields
            if isinstance(field, ct_fields.GenericForeignKey)]

    def get_default_field_names(self, declared_fields, model_info):
        """
        Include `GenericForeignKey` fields as relationships.
        """
        field_names = super(
            HyperlinkedGenericRelationsSerializer, self
        ).get_default_field_names(declared_fields, model_info)

        for field in self.generic_relations:
            # Remove the type and foreign key fields that make it up
            field_names.remove(field.ct_field)
            field_names.remove(field.fk_field)
            # Add the generic relation field itself
            field_names.append(field.name)

        return field_names

    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Build `GenericForeignKey` fields.
        """
        for model_field in self.generic_relations:
            if field_name != model_field.name:
                continue
            kwargs = field_mapping.get_field_kwargs(
                field_name, model_class._meta.get_field(
                    model_field.fk_field))
            for kwarg in ('min_value', 'max_value', 'model_field'):
                kwargs.pop(kwarg, None)
            return self.serializer_generic_related_field, kwargs
        return super(HyperlinkedGenericRelationsSerializer, self).build_field(
            field_name, info, model_class, nested_depth)
