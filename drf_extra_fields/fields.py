import imghdr
import io
import base64
import binascii
import uuid

from PIL import Image

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.fields import (
    DateField,
    DateTimeField,
    DictField,
    FileField,
    FloatField,
    ImageField,
    IntegerField,
)
from rest_framework.utils import html
from .compat import (
    DateRange,
    DateTimeTZRange,
    NumericRange,
    postgres_fields,
)


DEFAULT_CONTENT_TYPE = "application/octet-stream"


class Base64FieldMixin(object):
    @property
    def ALLOWED_TYPES(self):
        raise NotImplementedError

    @property
    def INVALID_FILE_MESSAGE(self):
        raise NotImplementedError

    @property
    def INVALID_TYPE_MESSAGE(self):
        raise NotImplementedError

    EMPTY_VALUES = (None, '', [], (), {})

    def __init__(self, *args, **kwargs):
        self.represent_in_base64 = kwargs.pop('represent_in_base64', False)
        super(Base64FieldMixin, self).__init__(*args, **kwargs)

    def to_internal_value(self, base64_data):
        # Check if this is a base64 string
        if base64_data in self.EMPTY_VALUES:
            return None

        if isinstance(base64_data, six.string_types):
            # Strip base64 header.
            if ';base64,' in base64_data:
                header, base64_data = base64_data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(base64_data)
            except (TypeError, binascii.Error, ValueError):
                raise ValidationError(self.INVALID_FILE_MESSAGE)
            # Generate file name:
            file_name = self.get_file_name(decoded_file)
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)
            if file_extension not in self.ALLOWED_TYPES:
                raise ValidationError(self.INVALID_TYPE_MESSAGE)
            complete_file_name = file_name + "." + file_extension
            data = ContentFile(decoded_file, name=complete_file_name)
            return super(Base64FieldMixin, self).to_internal_value(data)
        raise ValidationError(_('Invalid type. This is not an base64 string: {}'.format(
            type(base64_data))))

    def get_file_extension(self, filename, decoded_file):
        raise NotImplementedError

    def get_file_name(self, decoded_file):
        return str(uuid.uuid4())[:12]  # 12 characters are more than enough.

    def to_representation(self, file):
        if self.represent_in_base64:
            # If the underlying ImageField is blank, a ValueError would be
            # raised on `open`. When representing as base64, simply return an
            # empty base64 str rather than let the exception propagate unhandled
            # up into serializers.
            if not file:
                return ''

            try:
                with open(file.path, 'rb') as f:
                    return base64.b64encode(f.read()).decode()
            except Exception:
                raise IOError("Error encoding file")
        else:
            return super(Base64FieldMixin, self).to_representation(file)


class Base64ImageField(Base64FieldMixin, ImageField):
    """
    A django-rest-framework field for handling image-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.
    """
    ALLOWED_TYPES = (
        "jpeg",
        "jpg",
        "png",
        "gif"
    )
    INVALID_FILE_MESSAGE = _("Please upload a valid image.")
    INVALID_TYPE_MESSAGE = _("The type of the image couldn't be determined.")

    def get_file_extension(self, filename, decoded_file):
        extension = imghdr.what(filename, decoded_file)

        # Try with PIL as fallback if format not detected due
        # to bug in imghdr https://bugs.python.org/issue16512
        if extension is None:
            image = Image.open(io.BytesIO(decoded_file))
            extension = image.format.lower()

        extension = "jpg" if extension == "jpeg" else extension
        return extension


class HybridImageField(Base64ImageField):
    """
    A django-rest-framework field for handling image-uploads through
    raw post data, with a fallback to multipart form data.
    """

    def to_internal_value(self, data):
        """
        Try Base64Field first, and then try the ImageField
        ``to_internal_value``, MRO doesn't work here because
        Base64FieldMixin throws before ImageField can run.
        """
        try:
            return Base64FieldMixin.to_internal_value(self, data)
        except ValidationError:
            return ImageField.to_internal_value(self, data)


class Base64FileField(Base64FieldMixin, FileField):
    """
    A django-rest-framework field for handling file-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.
    """
    @property
    def ALLOWED_TYPES(self):
        raise NotImplementedError('List allowed file extensions')

    INVALID_FILE_MESSAGE = _("Please upload a valid file.")
    INVALID_TYPE_MESSAGE = _("The type of the file couldn't be determined.")

    def get_file_extension(self, filename, decoded_file):
        raise NotImplementedError('Implement file validation and return matching extension.')


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
    from rest_framework.serializers import ModelSerializer
    ModelSerializer.serializer_field_mapping[postgres_fields.DateTimeRangeField] = DateTimeRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.DateRangeField] = DateRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.IntegerRangeField] = IntegerRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.FloatRangeField] = FloatRangeField
