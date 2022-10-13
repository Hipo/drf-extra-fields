import base64
import binascii
import imghdr
import io
import uuid

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import (
    DateField,
    DateTimeField,
    DictField,
    EmailField,
    FileField,
    FloatField,
    ImageField,
    IntegerField,
    DecimalField,
)
from rest_framework.serializers import ModelSerializer
from rest_framework.utils import html
from drf_extra_fields import compat

try:
    from django.contrib.postgres import fields as postgres_fields
    from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange
except ImportError:
    postgres_fields = None
    DateRange = None
    DateTimeTZRange = None
    NumericRange = None


DEFAULT_CONTENT_TYPE = "application/octet-stream"


class Base64FieldMixin:
    EMPTY_VALUES = (None, "", [], (), {})

    @property
    def ALLOWED_TYPES(self):
        raise NotImplementedError

    @property
    def INVALID_FILE_MESSAGE(self):
        raise NotImplementedError

    @property
    def INVALID_TYPE_MESSAGE(self):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        self.trust_provided_content_type = kwargs.pop("trust_provided_content_type", False)
        self.represent_in_base64 = kwargs.pop("represent_in_base64", False)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, base64_data):
        # Check if this is a base64 string
        if base64_data in self.EMPTY_VALUES:
            return None

        if isinstance(base64_data, str):
            file_mime_type = None

            # Strip base64 header, get mime_type from base64 header.
            if ";base64," in base64_data:
                header, base64_data = base64_data.split(";base64,")
                if self.trust_provided_content_type:
                    file_mime_type = header.replace("data:", "")

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
            data = SimpleUploadedFile(
                name=complete_file_name,
                content=decoded_file,
                content_type=file_mime_type
            )

            return super().to_internal_value(data)

        raise ValidationError(_(f"Invalid type. This is not an base64 string: {type(base64_data)}"))

    def get_file_extension(self, filename, decoded_file):
        raise NotImplementedError

    def get_file_name(self, decoded_file):
        return str(uuid.uuid4())

    def to_representation(self, file):
        if self.represent_in_base64:
            # If the underlying ImageField is blank, a ValueError would be
            # raised on `open`. When representing as base64, simply return an
            # empty base64 str rather than let the exception propagate unhandled
            # up into serializers.
            if not file:
                return ""

            try:
                with open(file.path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except Exception:
                raise OSError("Error encoding file")
        else:
            return super().to_representation(file)


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
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow is not installed.")
        extension = imghdr.what(filename, decoded_file)

        # Try with PIL as fallback if format not detected due
        # to bug in imghdr https://bugs.python.org/issue16512
        if extension is None:
            try:
                image = Image.open(io.BytesIO(decoded_file))
            except OSError:
                raise ValidationError(self.INVALID_FILE_MESSAGE)

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

    default_error_messages = dict(DictField.default_error_messages)
    default_error_messages.update({
        'too_much_content': _('Extra content not allowed "{extra}".'),
        'bound_ordering': _('The start of the range must not exceed the end of the range.'),
    })

    def __init__(self, **kwargs):
        if postgres_fields is None:
            assert False, "'psgl2' is required to use {name}. Please install the  'psycopg2' library from 'pip'".format(
                name=self.__class__.__name__
            )

        self.child_attrs = kwargs.pop("child_attrs", {})
        self.child = self.child_class(**self.default_child_attrs, **self.child_attrs)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        Range instances <- Dicts of primitive datatypes.
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)

        # allow_empty is added to DictField in DRF Version 3.9.3
        if hasattr(self, "allow_empty") and not self.allow_empty and len(data) == 0:
            self.fail('empty')

        extra_content = list(set(data) - {"lower", "upper", "bounds", "empty"})
        if extra_content:
            self.fail('too_much_content', extra=', '.join(map(str, extra_content)))

        validated_dict = {}
        for key in ('lower', 'upper'):
            try:
                value = data[key]
            except KeyError:
                continue

            validated_dict[str(key)] = self.child.run_validation(value)

        lower, upper = validated_dict.get('lower'), validated_dict.get('upper')
        if lower is not None and upper is not None and lower > upper:
            self.fail('bound_ordering')

        for key in ('bounds', 'empty'):
            try:
                value = data[key]
            except KeyError:
                continue

            validated_dict[str(key)] = value

        return self.range_type(**validated_dict)

    def to_representation(self, value):
        """
        Range instances -> dicts of primitive datatypes.
        """
        if isinstance(value, dict):
            if not value:
                return value

            lower = value.get("lower")
            upper = value.get("upper")
            bounds = value.get("bounds")
        else:
            if value.isempty:
                return {'empty': True}
            lower = value.lower
            upper = value.upper
            bounds = value._bounds

        return {'lower': self.child.to_representation(lower) if lower is not None else None,
                'upper': self.child.to_representation(upper) if upper is not None else None,
                'bounds': bounds}

    def get_initial(self):
        initial = super().get_initial()
        return self.to_representation(initial)


class IntegerRangeField(RangeField):
    child_class = IntegerField
    default_child_attrs = {}
    range_type = NumericRange


class FloatRangeField(RangeField):
    child_class = FloatField
    default_child_attrs = {}
    range_type = NumericRange


class DecimalRangeField(RangeField):
    child_class = DecimalField
    default_child_attrs = {"max_digits": None, "decimal_places": None}
    range_type = NumericRange


class DateTimeRangeField(RangeField):
    child_class = DateTimeField
    default_child_attrs = {}
    range_type = DateTimeTZRange


class DateRangeField(RangeField):
    child_class = DateField
    default_child_attrs = {}
    range_type = DateRange


if postgres_fields:
    # monkey patch modelserializer to map Native django Range fields to
    # drf_extra_fiels's Range fields.
    ModelSerializer.serializer_field_mapping[postgres_fields.DateTimeRangeField] = DateTimeRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.DateRangeField] = DateRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.IntegerRangeField] = IntegerRangeField
    ModelSerializer.serializer_field_mapping[postgres_fields.DecimalRangeField] = DecimalRangeField
    if compat.FloatRangeField:
        ModelSerializer.serializer_field_mapping[compat.FloatRangeField] = FloatRangeField


class LowercaseEmailField(EmailField):
    """
    An enhancement over django-rest-framework's EmailField to allow
    case-insensitive serialization and deserialization of e-mail addresses.
    """
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return data.lower()

    def to_representation(self, value):
        value = super().to_representation(value)
        return value.lower()
