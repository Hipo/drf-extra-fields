import time

from rest_framework import serializers
from drf_extra_fields.crypto_fields import (
    CryptoBinaryField,
    CryptoCharField,
    _generate_password_key,
    _encrypt,
)
import datetime
from django.test import TestCase
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
from django.utils.translation import gettext_lazy as _

DEFAULT_PASSWORD = b"Non_nobis1solum?nati!sumus"
DEFAULT_SALT = settings.SECRET_KEY


class SaveCrypto(object):
    def __init__(self, message=None, created=None):
        self.message = message
        self.created = created or datetime.datetime.now()


class CryptoSerializer(serializers.Serializer):
    message = CryptoBinaryField(required=False)
    created = serializers.DateTimeField()

    def update(self, instance, validated_data):
        instance.message = validated_data["message"]
        return instance

    def create(self, validated_data):
        return SaveCrypto(**validated_data)


class CryptoCharSerializer(serializers.Serializer):
    message = CryptoCharField(required=False)
    created = serializers.DateTimeField()


class SaltCryptoSerializerSerializer(CryptoSerializer):
    message = CryptoBinaryField(salt="Salt")
    created = serializers.DateTimeField()


class PasswordCryptoSerializerSerializer(CryptoSerializer):
    message = CryptoBinaryField(password="Password")
    created = serializers.DateTimeField()


class TtlCryptoSerializerSerializer(CryptoSerializer):
    message = CryptoBinaryField(ttl=1)
    created = serializers.DateTimeField()


class PointSerializerTest(TestCase):
    def test_create(self):
        """
        Test for creating CryptoBinaryField
        """
        now = datetime.datetime.now()
        message = "test message"
        serializer = CryptoSerializer(data={"created": now, "message": message})
        model_data = SaveCrypto(message=message, created=now)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["created"], model_data.created)
        self.assertFalse(serializer.validated_data is model_data)
        self.assertIs(type(serializer.validated_data["message"]), bytes)

    def test_create_char(self):
        """
        Test for creating CryptoCharField
        """
        now = datetime.datetime.now()
        message = "test message"
        serializer = CryptoCharSerializer(data={"created": now, "message": message})
        model_data = SaveCrypto(message=message, created=now)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["created"], model_data.created)
        self.assertFalse(serializer.validated_data is model_data)
        self.assertIs(type(serializer.validated_data["message"]), str)

    def test_serialization(self):
        """
        Regular JSON serialization should output float values
        """
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key(DEFAULT_SALT, DEFAULT_PASSWORD)
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = CryptoSerializer(model_data)
        self.assertEqual(serializer.data["message"], message)

    def test_serialization_salt(self):
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key("Salt", DEFAULT_PASSWORD)
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = SaltCryptoSerializerSerializer(model_data)
        time.sleep(3)
        self.assertEqual(serializer.data["message"], message)

    def test_serialization_password(self):
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key(DEFAULT_SALT, "Password")
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = PasswordCryptoSerializerSerializer(model_data)
        time.sleep(3)
        self.assertEqual(serializer.data["message"], message)

    def test_serialization_ttl(self):
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key(DEFAULT_SALT, DEFAULT_PASSWORD)
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = TtlCryptoSerializerSerializer(model_data)
        time.sleep(3)
        with self.assertRaises(InvalidToken):
            return serializer.data["message"]
