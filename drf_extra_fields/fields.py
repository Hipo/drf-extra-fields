import base64
import binascii
import imghdr
import uuid
import sys
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.fields import ImageField


DEFAULT_CONTENT_TYPE = "application/octet-stream"
ALLOWED_IMAGE_TYPES = (
    "jpeg",
    "jpg",
    "png",
    "gif"
)

EMPTY_VALUES = (None, '', [], (), {})

# Python 3 Compatibility
# Issue: basestring in Python3 raises a NameError exception!
import types
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

class Base64ImageField(ImageField):
    """
    A django-rest-framework field for handling image-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.
    """
    def to_internal_value(self, base64_data):
        # Check if this is a base64 string
        if base64_data in EMPTY_VALUES:
            return None

        if isinstance(base64_data, six.string_types):
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

    def to_representation(self, value):
        # Return url including domain name.
        return value.name

    def get_file_extension(self, filename, decoded_file):
        extension = imghdr.what(filename, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension
        return extension
