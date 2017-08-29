import re

from django.core import exceptions
from django.db import models
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

    detail_view_name_re = re.compile(r'(.+)-detail$')

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

        queryset = self.get_queryset(match)
        if self.lookup_url_kwarg not in match.kwargs:
            return queryset

        lookup_value = match.kwargs[self.lookup_url_kwarg]
        lookup_kwargs = {self.lookup_field: lookup_value}
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
        if isinstance(value, models.Model):
            model = type(value)
        else:
            model = value.model

        try:
            self.view_name = field_mapping.get_detail_view_name(model)
            if not isinstance(value, models.Model):
                # Listing view for queryset
                assert 'request' in self.context, (
                    "`%s` requires the request in the serializer"
                    " context. Add `context={'request': request}` when"
                    " instantiating the serializer." % self.__class__.__name__
                )

                request = self.context['request']
                format = self.context.get('format', None)
                return self.reverse(
                    self.detail_view_name_re.match(
                        self.view_name).group(1) + '-list',
                    request=request, format=format)

            return super(
                HyperlinkedGenericRelationsField, self).to_representation(
                    value)
        finally:
            self.view_name = None


class HyperlinkedGenericRelationsSerializer(object):
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
        # Get the primary ID field for the serializer
        id_field_name = self.get_field_names(self._declared_fields, info)[0]
        id_field = self._declared_fields.get(id_field_name)
        if id_field is None:
            # Reconstruct the ID field
            # Reproduce the ModelSerializer.get_fields() inner loop logic
            extra_kwargs = self.get_extra_kwargs()
            extra_field_kwargs = extra_kwargs.get(id_field_name, {})
            source = extra_field_kwargs.get('source') or id_field_name
            field_class, field_kwargs = super(
                HyperlinkedGenericRelationsSerializer, self).build_field(
                    source, info, model_class, nested_depth)
            field_kwargs = self.include_extra_kwargs(
                field_kwargs, extra_field_kwargs)
            id_field = field_class(**field_kwargs)

        # If not specified, infer the default URL lookup field for
        # generic relations from the serializer's primary ID/URL field
        lookup_kwargs = {}
        if hasattr(id_field, 'lookup_field'):
            # Another, hyperlink field, default to their lookup field
            lookup_kwargs.update(
                lookup_field=id_field.lookup_field,
                lookup_url_kwarg=id_field.lookup_url_kwarg)
        else:
            # Primary key ID field, use it's source as the lookup field
            source = getattr(id_field, 'source', None)
            if source is not None:
                lookup_kwargs.update(lookup_field=source)

        for model_field in self.generic_relations:
            if field_name != model_field.name:
                continue
            kwargs = field_mapping.get_field_kwargs(
                field_name, model_class._meta.get_field(
                    model_field.fk_field))
            for kwarg in ('min_value', 'max_value', 'model_field'):
                kwargs.pop(kwarg, None)
            lookup_field = kwargs.get('lookup_field')
            if lookup_field is None:
                kwargs.update(lookup_kwargs)
            return self.serializer_generic_related_field, kwargs

        return super(HyperlinkedGenericRelationsSerializer, self).build_field(
            field_name, info, model_class, nested_depth)


class GenericRelationsModelSerializer(
        HyperlinkedGenericRelationsSerializer, serializers.ModelSerializer):
    """
    Serialize `GenericForeignKey` model fields/relationships as hyperlinks.

    The primary ID field will still use primary keys by default.
    """


class HyperlinkedGenericRelationsModelSerializer(
        HyperlinkedGenericRelationsSerializer,
        serializers.HyperlinkedModelSerializer):
    """
    Serialize `GenericForeignKey` model fields/relationships as hyperlinks.

    The primary ID field will also use hyperlinks by default.
    """
