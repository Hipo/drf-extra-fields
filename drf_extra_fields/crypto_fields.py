import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import time

EMPTY_VALUES = (None, "", [], (), {})
DEFAULT_PASSWORD = b"Non_nobis1solum?nati!sumus"
DEFAULT_SALT = settings.SECRET_KEY


def _generate_password_key(salt=DEFAULT_SALT, password=DEFAULT_PASSWORD):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_to_bytes(salt),
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(_to_bytes(password)))
    return key


def _to_bytes(v):
    if isinstance(v, str):
        return v.encode("utf-8")

    if isinstance(v, bytes):
        return v

    raise TypeError(
        _(
            "SALT & PASSWORD must be specified as strings that convert nicely to "
            "bytes."
        )
    )


def _encrypt(token, value_in_str):
    b_message = value_in_str.encode("utf-8")
    encrypted_message = token.encrypt(b_message)
    return encrypted_message


def _decrypt(token, value, ttl=None):
    ttl = int(ttl) if ttl else None
    decrypted_message = token.decrypt(_to_bytes(value), ttl)
    return decrypted_message.decode("utf-8")


def _get_timestamp(token, value):
    timestamp = token.extract_timestamp(_to_bytes(value))
    return int(timestamp)


class CryptoBinaryField(serializers.Field):
    """
    A django-rest-framework field for handling encryption through serialisation, where input are string
    and internal python representation is Binary object.
    """

    type_name = "CryptoBinaryField"
    type_label = "crypto"

    default_error_messages = {
        "invalid": _("Input a valid data"),
    }

    def __init__(self, *args, **kwargs):
        self.salt = kwargs.pop("salt", DEFAULT_SALT)
        self.password = kwargs.pop("password", DEFAULT_PASSWORD)
        self.ttl = kwargs.pop("ttl", None)
        super(CryptoBinaryField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        """
        Parse input data to encrypted binary data
        """
        if value in EMPTY_VALUES and not self.required:
            return None

        if isinstance(value, str):
            key = _generate_password_key(self.salt, self.password)
            token = Fernet(key)
            encrypted_message = _encrypt(token, value)
            return encrypted_message

        self.fail("invalid")

    def to_representation(self, value):
        """
        Transform encrypted data to decrypted string.
        """
        if value is None:
            return value
        if isinstance(value, str):
            value = value.encode("utf-8")
        elif isinstance(value, (bytearray, memoryview)):
            value = bytes(value)
        if isinstance(value, bytes):
            key = _generate_password_key(self.salt, self.password)
            token = Fernet(key)
            try:
                decrypted_message = _decrypt(token, value, self.ttl)
                return decrypted_message
            except InvalidToken:

                if self.ttl is not None:
                    # timestamp, data = Fernet._get_unverified_token_data(token)
                    # timestamp = Fernet.extract_timestamp(token)
                    # timestamp = token.extract_timestamp(token)
                    timestamp = _get_timestamp(token, value)
                    current_time = int(time.time())
                    if timestamp + self.ttl < current_time:
                        raise InvalidToken(_("The Token ttl has expired"))

                raise InvalidToken(_("Valid Token could not be created"))

        self.fail("invalid")


class CryptoCharField(CryptoBinaryField):
    """
    A django-rest-framework field for handling encryption through serialisation, where input are string
    and internal python representation is String object.
    """

    type_name = "CryptoBinaryField"

    def to_internal_value(self, value):
        value = super(CryptoCharField, self).to_internal_value(value)
        if value is None:
            return value
        elif value:
            return value.decode("utf-8")
        self.fail("invalid")
