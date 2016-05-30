from __future__ import unicode_literals

import base64
import binascii
import imghdr
import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.fields import (
    DateField,
    DateTimeField,
    DictField,
    FloatField,
    ImageField,
    IntegerField,
)
from rest_framework.serializers import ModelSerializer, RelatedField
from rest_framework.utils import html

from .compat import (
    DateRange,
    DateTimeTZRange,
    NumericRange,
    postgres_fields,
)


DEFAULT_CONTENT_TYPE = "application/octet-stream"
ALLOWED_IMAGE_TYPES = (
    "jpeg",
    "jpg",
    "png",
    "gif"
)

EMPTY_VALUES = (None, '', [], (), {})


class Base64ImageField(ImageField):
    """
    A django-rest-framework field for handling image-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.
    """

    def __init__(self, *args, **kwargs):
        self.represent_in_base64 = kwargs.pop('represent_in_base64', False)
        super(Base64ImageField, self).__init__(*args, **kwargs)

    def to_internal_value(self, base64_data):
        # Check if this is a base64 string
        if base64_data in EMPTY_VALUES:
            return None

        if isinstance(base64_data, six.string_types):
            # Strip base64 header.
            if ';base64,' in base64_data:
                header, base64_data = base64_data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(base64_data)
            except (TypeError, binascii.Error):
                raise ValidationError(_("Please upload a valid image."))
            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)
            if file_extension not in ALLOWED_IMAGE_TYPES:
                raise ValidationError(_("The type of the image couldn't been determined."))
            complete_file_name = file_name + "." + file_extension
            data = ContentFile(decoded_file, name=complete_file_name)
            return super(Base64ImageField, self).to_internal_value(data)
        raise ValidationError(_('This is not an base64 string'))

    def get_file_extension(self, filename, decoded_file):
        extension = imghdr.what(filename, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension
        return extension

    def to_representation(self, image):
        if self.represent_in_base64:
            try:
                with open(image.path, 'rb') as f:
                    return base64.b64encode(f.read()).decode()
            except Exception:
                raise IOError("Error encoding image file")
        else:
            return super(ImageField, self).to_representation(image)


class RangeField(DictField):

    range_type = None

    default_error_messages = {
        'not_a_dict': _('Expected a dictionary of items but got type "{input_type}".'),
        'too_much_content': _('Extra content not allowed "{extra}".'),
    }

    def to_internal_value(self, data):
        """
        Range instances <- Dicts of primitive datatypes.
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)
        validated_dict = {}
        for key in ('lower', 'upper'):
            try:
                value = data.pop(key)
            except KeyError:
                continue
            validated_dict[six.text_type(key)] = self.child.run_validation(value)
        for key in ('bounds', 'empty'):
            try:
                value = data.pop(key)
            except KeyError:
                continue
            validated_dict[six.text_type(key)] = value
        if data:
            self.fail('too_much_content', extra=', '.join(map(str, data.keys())))
        return self.range_type(**validated_dict)

    def to_representation(self, value):
        """
        Range instances -> dicts of primitive datatypes.
        """
        if value.isempty:
            return {'empty': True}
        lower = self.child.to_representation(value.lower) if value.lower is not None else None
        upper = self.child.to_representation(value.upper) if value.upper is not None else None
        return {'lower': lower,
                'upper': upper,
                'bounds': value._bounds}


class IntegerRangeField(RangeField):
    child = IntegerField()
    range_type = NumericRange


class FloatRangeField(RangeField):
    child = FloatField()
    range_type = NumericRange


class DateTimeRangeField(RangeField):
    child = DateTimeField()
    range_type = DateTimeTZRange


class DateRangeField(RangeField):
    child = DateField()
    range_type = DateRange

if postgres_fields is not None:
    # monkey patch modelserializer to map Native django Range fields to
    # drf_extra_fiels's Range fields.
    ModelSerializer.serializer_field_mapping[postgres_fields.DateTimeRangeField] = DateTimeRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.DateRangeField] = DateRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.IntegerRangeField] = IntegerRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.FloatRangeField] = FloatRangeField


class SerializableRelatedField(RelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, **kwargs):
        self.serializer_class = kwargs.pop('serializer_class', None)
        assert self.serializer_class is not None, (
            '{cls} must provide a `serializer_class` argument'.format(cls=self.__class__.__name__)
        )
        self.serializer_params = kwargs.pop('serializer_params', dict())
        if 'queryset' not in kwargs and issubclass(self.serializer_class, ModelSerializer):
            kwargs['queryset'] = self.serializer_class.Meta.model.objects.all()
        kwargs['style'] = {'base_template': 'input.html', 'input_type': 'numeric'}
        self.serializer = self.serializer_class(**self.serializer_params)
        self.serializer.parent = self
        super(SerializableRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        return self.serializer.to_representation(value)
