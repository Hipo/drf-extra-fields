import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from drf_extra_fields.fields import (
    BaseQRCodeField,
    UrlQRCodeField,
    WiFiQRCodeField,
    vCardQRCodeField,
    )

from rest_framework.serializers import Serializer
from rest_framework.exceptions import ValidationError as DRFValidationError
from PIL import Image

# --- Test for BaseQRCodeField ---
@pytest.fixture
def qr_field():
    """Fixture para instanciar la clase BaseQRCodeField."""
    return BaseQRCodeField()


def test_qrcode_field_valid(qr_field):
    """Caso exitoso: debe generar un archivo PNG válido cuando se le pasa un string."""
    text = "Hola Gerardo"
    file = qr_field.to_internal_value(text)

    # Verificamos que el resultado sea un archivo subido válido
    assert isinstance(file, SimpleUploadedFile)
    assert file.content_type == "image/png"
    assert file.name.startswith("qrcode_")
    assert file.name.endswith(".png")
    assert file.size > 0  # El archivo no está vacío


def test_qrcode_field_invalid_type(qr_field):
    with pytest.raises(ValidationError) as exc_info:
        qr_field.to_internal_value(12345)

    assert str(exc_info.value) == "['Expected text to generate QR code']"


def test_qrcode_field_empty_string(qr_field):
    with pytest.raises(ValidationError) as exc_info:
        qr_field.to_internal_value("")

    assert str(exc_info.value) == "['Cannot generate QR code from empty text']"


# --- Tests for UrlQRCodeField ---

class UrlQRCodeFieldTestSerializer(Serializer):
    qr = UrlQRCodeField()

@pytest.fixture
def url_serializer():
    return UrlQRCodeFieldTestSerializer

def test_valid_url_generates_qr(url_serializer):
    data = {"qr": "https://www.example.com"}
    serializer = url_serializer(data=data)
    assert serializer.is_valid(), serializer.errors

    qr_file = serializer.validated_data["qr"]
    assert qr_file.name.endswith(".png")

    image = Image.open(qr_file)
    assert image.format == "PNG"

def test_invalid_url_scheme(url_serializer):
    data = {"qr": "ftp://example.com"}
    serializer = url_serializer(data=data)
    assert not serializer.is_valid()
    assert "qr" in serializer.errors
    assert "The URL must begin with" in str(serializer.errors["qr"][0])

def test_empty_url(url_serializer):
    data = {"qr": ""}
    serializer = url_serializer(data=data)
    assert not serializer.is_valid()
    assert "qr" in serializer.errors
    assert "cannot be generated from an empty URL" in str(serializer.errors["qr"][0])

def test_non_string_input(url_serializer):
    data = {"qr": 12345}
    serializer = url_serializer(data=data)
    assert not serializer.is_valid()
    assert "qr" in serializer.errors
    assert "A text string (URL) was expected" in str(serializer.errors["qr"][0])

# --- test for WIFIQRCodeField ---

@pytest.fixture
def wifi_field():
    return WiFiQRCodeField()


def test_wifi_qrcode_valid_wpa(wifi_field):
    creds = {
        "ssid": "MyWiFi",
        "password": "supersecret",
        "security": "WPA",
        "hidden": False,
    }

    file = wifi_field.to_internal_value(creds)

    assert isinstance(file, SimpleUploadedFile)
    assert file.content_type == "image/png"
    assert file.name.startswith("qrcode_")
    assert file.name.endswith(".png")
    assert file.size > 0


def test_wifi_qrcode_valid_nopass(wifi_field):
    creds = {
        "ssid": "PublicHotspot",
        "security": "nopass",
    }

    file = wifi_field.to_internal_value(creds)

    assert isinstance(file, SimpleUploadedFile)
    assert file.content_type == "image/png"
    assert file.name.endswith(".png")


def test_wifi_qrcode_invalid_type_not_dict(wifi_field):
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value("not-a-dict")
    assert exc_info.value.messages[0] == "Expected a dictionary with WiFi credentials"


def test_wifi_qrcode_empty_data(wifi_field):
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value("")
    assert exc_info.value.messages[0] == "Cannot generate WiFi QR from empty data"


def test_wifi_qrcode_missing_ssid(wifi_field):
    creds = {"security": "WPA", "password": "x"}
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value(creds)
    assert exc_info.value.messages[0] == "Field 'ssid' must be a string"


def test_wifi_qrcode_empty_ssid(wifi_field):
    creds = {"ssid": "", "security": "WPA", "password": "x"}
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value(creds)
    assert exc_info.value.messages[0] == "Field 'ssid' cannot be empty"


def test_wifi_qrcode_missing_security(wifi_field):
    creds = {"ssid": "MyWiFi", "password": "x"}
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value(creds)
    assert exc_info.value.messages[0] == "Field 'security' must be a non-empty string"


def test_wifi_qrcode_invalid_security_value(wifi_field):
    creds = {"ssid": "MyWiFi", "password": "x", "security": "WPA2"}
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value(creds)
    assert exc_info.value.messages[0] == "Field 'security' must be one of: WPA, WEP, nopass"


def test_wifi_qrcode_password_required_for_wpa(wifi_field):
    creds = {"ssid": "MyWiFi", "security": "WPA"}
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value(creds)
    assert exc_info.value.messages[0] == "Field 'password' must be a string"


def test_wifi_qrcode_hidden_must_be_boolean(wifi_field):
    creds = {"ssid": "MyWiFi", "password": "x", "security": "WEP", "hidden": "yes"}
    with pytest.raises(ValidationError) as exc_info:
        wifi_field.to_internal_value(creds)
    assert exc_info.value.messages[0] == "Field 'hidden' must be a boolean if provided"


def test_wifi_qrcode_escaping_characters(wifi_field):
    creds = {
        "ssid": "Office;Wi,fi:Net\\work\"",
        "password": "p;,:\\\"",
        "security": "WEP",
        "hidden": True,
    }

    file = wifi_field.to_internal_value(creds)
    assert isinstance(file, SimpleUploadedFile)

# --- Test for vCardQRCodeFields ---

@pytest.fixture
def vcard_field():
    return vCardQRCodeField()


def test_vcard_qrcode_valid(vcard_field):
    data = {
        "name": "John Doe",
        "phone": "+1-555-1234",
        "email": "john@example.com",
    }

    file = vcard_field.to_internal_value(data)

    assert isinstance(file, SimpleUploadedFile)
    assert file.content_type == "image/png"
    assert file.name.startswith("qrcode_")
    assert file.name.endswith(".png")
    assert file.size > 0


def test_vcard_qrcode_invalid_type_not_dict(vcard_field):
    with pytest.raises(ValidationError) as exc_info:
        vcard_field.to_internal_value("not-a-dict")
    assert exc_info.value.messages[0] == "Expected a dictionary with vCard credentials"


def test_vcard_qrcode_empty_data(vcard_field):
    with pytest.raises(ValidationError) as exc_info:
        vcard_field.to_internal_value("")
    assert exc_info.value.messages[0] == "Cannot generate vCard QR from empty data"


def test_vcard_qrcode_missing_name(vcard_field):
    data = {"phone": "+1-555-1234", "email": "john@example.com"}
    with pytest.raises(ValidationError) as exc_info:
        vcard_field.to_internal_value(data)
    assert exc_info.value.messages[0] == "Required fields are missing: name"


def test_vcard_qrcode_missing_phone(vcard_field):
    data = {"name": "John Doe", "email": "john@example.com"}
    with pytest.raises(ValidationError) as exc_info:
        vcard_field.to_internal_value(data)
    assert exc_info.value.messages[0] == "Required fields are missing: phone"


def test_vcard_qrcode_missing_email(vcard_field):
    data = {"name": "John Doe", "phone": "+1-555-1234"}
    with pytest.raises(ValidationError) as exc_info:
        vcard_field.to_internal_value(data)
    assert exc_info.value.messages[0] == "Required fields are missing: email"


def test_vcard_qrcode_multiple_missing_fields(vcard_field):
    data = {"name": "John Doe"}
    with pytest.raises(ValidationError) as exc_info:
        vcard_field.to_internal_value(data)
    # El orden de los campos faltantes sigue la lógica de construcción de la lista
    assert exc_info.value.messages[0] in (
        "Required fields are missing: phone, email",
        "Required fields are missing: email, phone",
    )