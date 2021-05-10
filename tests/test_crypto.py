import datetime

from django.test import TestCase

from drf_extra_fields.crypto_field import (
    CryptoBigIntegerField,
    CryptoCharField,
    CryptoDateField,
    CryptoDateTimeField,
    CryptoEmailField,
    CryptoIntegerField,
    CryptoPositiveIntegerField,
    CryptoPositiveSmallIntegerField,
    CryptoSmallIntegerField,
    CryptoTextField,
)


class PersonTest(TestCase):
    def test_get_prep_value(self):
        text_field = "RandomTextField123!"
        char_field = "RandomCharField123!"
        email_field = "random@email.com"
        int_field = -123
        date_field = datetime.date(2001, 1, 1)
        date_time_field = datetime.datetime(2001, 1, 1, 13, 00)
        big_int_field = -9223372036854775808
        positive_int_field = 123
        positive_small_int_field = 1
        small_int_field = -1

        c_text = CryptoTextField()
        c_char = CryptoCharField()
        c_email = CryptoEmailField()
        c_int = CryptoIntegerField()
        c_date = CryptoDateField()
        c_date_time = CryptoDateTimeField()
        c_big_int = CryptoBigIntegerField()
        c_positive_integer = CryptoPositiveIntegerField()
        c_positive_small_integer = CryptoPositiveSmallIntegerField()
        c_small_integer = CryptoSmallIntegerField()
        self.assertEqual(
            text_field,
            c_text.get_prep_value(value=text_field),
        )
        self.assertEqual(
            char_field,
            c_char.get_prep_value(value=char_field),
        )
        self.assertEqual(
            email_field,
            c_email.get_prep_value(value=email_field),
        )
        self.assertEqual(
            int_field,
            c_int.get_prep_value(value=int_field),
        )
        self.assertEqual(
            date_field,
            c_date.get_prep_value(value=date_field),
        )
        self.assertEqual(
            date_time_field,
            c_date_time.get_prep_value(value=date_time_field),
        )
        self.assertEqual(
            big_int_field,
            c_big_int.get_prep_value(value=big_int_field),
        )
        self.assertEqual(
            positive_int_field,
            c_positive_integer.get_prep_value(value=positive_int_field),
        )
        self.assertEqual(
            positive_small_int_field,
            c_positive_small_integer.get_prep_value(value=positive_small_int_field),
        )
        self.assertEqual(
            small_int_field,
            c_small_integer.get_prep_value(value=small_int_field),
        )

    def test_get_db_prep_save(self):
        c_text = CryptoTextField()
        self.assertIs(
            bytes,
            type(c_text.get_db_prep_save(value="RandomTextField123!", connection=None)),
        )

    def test_to_python(self):
        c_text = CryptoTextField()
        self.assertEqual(str(""), c_text.to_python(""))
        self.assertEqual(str("a"), c_text.to_python("a"))

    def test_password_salt(self):
        c_text = CryptoTextField()
        c2_text = CryptoTextField(password="password_to_be_used_as_key")
        self.assertEqual("Password123!!!", c_text.password)
        self.assertEqual("Salt123!!!", c_text.salt)
        self.assertEqual("password_to_be_used_as_key", c2_text.password)
