# import datetime
from django.db import models
# import pytz

from drf_extra_fields.crypto_field import (
    # CryptoFieldMixin,
    CryptoTextField,
    CryptoCharField,
    CryptoEmailField,
    CryptoIntegerField,
    CryptoDateField,
    CryptoDateTimeField,
    CryptoBigIntegerField,
    CryptoPositiveIntegerField,
    CryptoPositiveSmallIntegerField,
    CryptoSmallIntegerField,
)

class TextModel(models.Model):
    text_field = CryptoTextField()

class CharModel(models.Model):
    char_field = CryptoCharField()

# class DemoModel(models.Model):
#     password = "Password123!"
#     text_field = 'RandomText123!'
#     char_field = 'RandomChar123!'
#     email_field = 'random@email.com'
#     integer_field = 123
#     date_field = datetime.date(2001, 1, 1)
#     datetime_field = datetime.datetime(2001, 1, 1, 13, 00, tzinfo=pytz.utc)
#     big_integer_field = -9223372036854775808
#     positive_integer_field = 9223372036854775808
#     positive_small_integer_field = 1
#     small_integer_field = -1
#

