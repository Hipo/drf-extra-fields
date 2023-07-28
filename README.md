DRF-EXTRA-FIELDS
================

Extra Fields for Django Rest Framework

[![Build Status](https://github.com/Hipo/drf-extra-fields/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/Hipo/drf-extra-fields/actions)
[![codecov](https://codecov.io/gh/Hipo/drf-extra-fields/branch/master/graph/badge.svg)](https://codecov.io/gh/Hipo/drf-extra-fields)
[![PyPI Version](https://img.shields.io/pypi/v/drf-extra-fields.svg)](https://pypi.org/project/drf-extra-fields)
[![Python Versions](https://img.shields.io/pypi/pyversions/drf-extra-fields.svg)](https://pypi.org/project/drf-extra-fields)

Latest Changes
==============
- **v3.6.0**
  - File objects without an actual file-system path can now be used in `Base64ImageField`, `Base64FileField` and `HybridImageField`
- **v3.5.0**
  - Development environment fixes & improvements.
  - Since `Python 3.6` support is ended, the codebase is refactored/modernized for `Python 3.7`.
  - `WebP` is added to default `ALLOWED_TYPES` of the `Base64ImageField`.
  - Deprecated `imghdr` library is replaced with `filetype`.
  - Unintended `Pillow` dependency is removed.
- **v3.4.0**
  - :warning: **BACKWARD INCOMPATIBLE** :warning:
    - Support for `Django 3.0` and `Django 3.1` is ended.
  - `Django 4.0` is now supported.
- **v3.3.0**
  - :warning: **BACKWARD INCOMPATIBLE** :warning:
    - Support for `Python 3.6` is ended.
- **v3.2.1**
  - A typo in the `python_requires` argument of `setup.py` that prevents installation for `Python 3.6` is fixed.
- **v3.2.0**
  - :warning: **BACKWARD INCOMPATIBLE** :warning:
    - Support for `Python 3.5` is ended.
  - `Python 3.9` and `Python 3.10` are now supported.
  - `Django 3.2` is now supported.
- **v3.1.1**
  - `psycopg2` dependency is made optional.
- **v3.1.0**
  - **Possible Breaking Change**:
    -  In this version we have changed file class used in `Base64FileField` from `ContentFile` to `SimpleUploadedFile` (you may see the change [here](https://github.com/Hipo/drf-extra-fields/pull/149/files#diff-5f77bcb61083cd9c026f6dfb3b77bf8fa824c45e620cdb7826ad713bde7b65f8L72-R85)).
  - `child_attrs` property is added to [RangeFields](https://github.com/Hipo/drf-extra-fields#rangefield).

Usage
================

Install the package

```bash
pip install drf-extra-fields
```

**Note:**
- **This package renamed as "drf-extra-fields", earlier it was named as django-extra-fields.**
- Install version 0.1 for Django Rest Framework 2.*
- Install version 0.3 or greater for Django Rest Framework 3.*

Fields:
----------------


## Base64ImageField

An image representation for Base64ImageField

Inherited from `ImageField`


**Signature:** `Base64ImageField()`

 - It takes a base64 image as a string.
 - A base64 image:  `data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7`
 - Base64ImageField accepts the entire string or just the part after base64, `R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7`
 - It takes the optional parameter `represent_in_base64` (`False` by default), if set to `True` it will allow for base64-encoded downloads of an `ImageField`.
 - You can inherit the `Base64ImageField` class and set allowed extensions (`ALLOWED_TYPES` list), or customize the validation messages (`INVALID_FILE_MESSAGE`, `INVALID_TYPE_MESSAGE`)


**Example:**

```python
# serializer

from drf_extra_fields.fields import Base64ImageField

class UploadedBase64ImageSerializer(serializers.Serializer):
    file = Base64ImageField(required=False)
    created = serializers.DateTimeField()

# use the serializer
file = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
serializer = UploadedBase64ImageSerializer(data={'created': now, 'file': file})
```


## Base64FileField

A file representation for Base64FileField

Inherited from `FileField`


**Signature:** `Base64FileField()`

 - It takes a base64 file as a string.
 - Other options like for `Base64ImageField`
 - You have to provide your own full implementation of this class. You have to implement file validation in `get_file_extension` method and set `ALLOWED_TYPES` list.


**Example:**

```python
class PDFBase64File(Base64FileField):
    ALLOWED_TYPES = ['pdf']

    def get_file_extension(self, filename, decoded_file):
        try:
            PyPDF2.PdfFileReader(io.BytesIO(decoded_file))
        except PyPDF2.utils.PdfReadError as e:
            logger.warning(e)
        else:
            return 'pdf'
```


## PointField

Point field for GeoDjango


**Signature:** `PointField()`

 - It takes a dictionary contains latitude and longitude keys like below

    {
     "latitude": 49.8782482189424,
     "longitude": 24.452545489
    }
 - It takes the optional parameter `str_points` (False by default), if set to True it serializes the longitude/latitude
 values as strings
 - It takes the optional parameter `srid` (None by default), if set the Point created object will have its srid attribute set to the same value.

**Example:**

```python
# serializer

from drf_extra_fields.geo_fields import PointField

class PointFieldSerializer(serializers.Serializer):
    point = PointField(required=False)
    created = serializers.DateTimeField()

# use the serializer
point = {
    "latitude": 49.8782482189424,
    "longitude": 24.452545489
    }
serializer = PointFieldSerializer(data={'created': now, 'point': point})
```


# RangeField

The Range Fields map to Django's PostgreSQL specific [Range Fields](https://docs.djangoproject.com/en/stable/ref/contrib/postgres/fields/#range-fields).

Each accepts an optional parameter `child_attrs`, which allows passing parameters to the child field.

For example, calling `IntegerRangeField(child_attrs={"allow_null": True})` allows deserializing data with a null value for `lower` and/or `upper`:

```python
from rest_framework import serializers
from drf_extra_fields.fields import IntegerRangeField


class RangeSerializer(serializers.Serializer):
    ranges = IntegerRangeField(child_attrs={"allow_null": True})


serializer = RangeSerializer(data={'ranges': {'lower': 0, 'upper': None}})

```

## IntegerRangeField

```python
from rest_framework import serializers
from drf_extra_fields.fields import IntegerRangeField


class RangeSerializer(serializers.Serializer):
    ranges = IntegerRangeField()


serializer = RangeSerializer(data={'ranges': {'lower': 0, 'upper': 1}})

```

## FloatRangeField

```python
from rest_framework import serializers
from drf_extra_fields.fields import FloatRangeField


class RangeSerializer(serializers.Serializer):
    ranges = FloatRangeField()


serializer = RangeSerializer(data={'ranges': {'lower': 0., 'upper': 1.}})

```

## DecimalRangeField

```python
from rest_framework import serializers
from drf_extra_fields.fields import DecimalRangeField


class RangeSerializer(serializers.Serializer):
    ranges = DecimalRangeField()


serializer = RangeSerializer(data={'ranges': {'lower': 0., 'upper': 1.}}, )

```

## DateRangeField

```python
import datetime

from rest_framework import serializers
from drf_extra_fields.fields import DateRangeField


class RangeSerializer(serializers.Serializer):
    ranges = DateRangeField()


serializer = RangeSerializer(data={'ranges': {'lower': datetime.date(2015, 1, 1), 'upper': datetime.date(2015, 2, 1)}})

```

## DateTimeRangeField

```python
import datetime

from rest_framework import serializers
from drf_extra_fields.fields import DateTimeRangeField


class RangeSerializer(serializers.Serializer):
    ranges = DateTimeRangeField()


serializer = RangeSerializer(data={'ranges': {'lower': datetime.datetime(2015, 1, 1, 0), 'upper': datetime.datetime(2015, 2, 1, 0)}})

```

## PresentablePrimaryKeyRelatedField

Represents related object with a serializer.

`presentation_serializer` could also be a string that represents a dotted path of a serializer, this is useful when you want to represent a related field with the same serializer.

```python
from drf_extra_fields.relations import PresentablePrimaryKeyRelatedField

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            "username",
        )

class PostSerializer(serializers.ModelSerializer):
    user = PresentablePrimaryKeyRelatedField(
        queryset=User.objects.all(),
        presentation_serializer=UserSerializer,
        presentation_serializer_kwargs={
            'example': [
                'of',
                'passing',
                'kwargs',
                'to',
                'serializer',
            ]
        },
        read_source=None
    )
    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "user",
        )
```

**Serializer data:**
```
{
    "user": 1,
    "title": "test"
}
```

**Serialized data with PrimaryKeyRelatedField:**
```
{
    "id":1,
    "user": 1,
    "title": "test"
}
```

**Serialized data with PresentablePrimaryKeyRelatedField:**
```
{
    "id":1,
    "user": {
        "id": 1,
        "username": "test"
    },
    "title": "test"
}
```


## PresentableSlugRelatedField

Represents related object retrieved using slug with a serializer.

```python
from drf_extra_fields.relations import PresentableSlugRelatedField

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "slug",
            "name"
        )

class ProductSerializer(serializers.ModelSerializer):
    category = PresentableSlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        presentation_serializer=CategorySerializer,
        presentation_serializer_kwargs={
            'example': [
                'of',
                'passing',
                'kwargs',
                'to',
                'serializer',
            ]
        },
        read_source=None
    )
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "category",
        )
```

**Serializer data:**
```
{
    "category": "vegetables",
    "name": "Tomato"
}
```

**Serialized data with SlugRelatedField:**
```
{
    "id": 1,
    "name": "Tomato",
    "category": "vegetables"
}
```

**Serialized data with PresentableSlugRelatedField:**
```
{
    "id": 1,
    "name": "Tomato",
    "category": {
        "id": 1,
        "slug": "vegetables",
        "name": "Vegetables"
    }
}
```

### read_source parameter
This parameter allows you to use different `source` for read operations and doesn't change field name for write operations. This is only used while representing the data. 

## HybridImageField
A django-rest-framework field for handling image-uploads through raw post data, with a fallback to multipart form data.

It first tries Base64ImageField. if it fails then tries ImageField.

```python
from rest_framework import serializers
from drf_extra_fields.fields import HybridImageField


class HybridImageSerializer(serializers.Serializer):
    image = HybridImageField()
```

drf-yasg fix for BASE64 Fields:
----------------
The [drf-yasg](https://github.com/axnsan12/drf-yasg) project seems to generate wrong documentation on Base64ImageField or Base64FileField. It marks those fields as readonly. Here is the workaround code for correct the generated document. (More detail on issue [#66](https://github.com/Hipo/drf-extra-fields/issues/66))

```python
class PDFBase64FileField(Base64FileField):
    ALLOWED_TYPES = ['pdf']

    class Meta:
        swagger_schema_fields = {
            'type': 'string',
            'title': 'File Content',
            'description': 'Content of the file base64 encoded',
            'read_only': False  # <-- FIX
        }

    def get_file_extension(self, filename, decoded_file):
        try:
            PyPDF2.PdfFileReader(io.BytesIO(decoded_file))
        except PyPDF2.utils.PdfReadError as e:
            logger.warning(e)
        else:
            return 'pdf'
```


## LowercaseEmailField
An enhancement over django-rest-framework's EmailField to allow case-insensitive serialization and deserialization of e-mail addresses.

```python
from rest_framework import serializers
from drf_extra_fields.fields import LowercaseEmailField


class EmailSerializer(serializers.Serializer):
    email = LowercaseEmailField()

```

CONTRIBUTION
=================

**TESTS**
- Make sure that you add the test for contributed field to test/test_fields.py
and run with command before sending a pull request:

```bash
$ pip install tox  # if not already installed
$ tox
```

Or, if you prefer using Docker (recommended):

```bash
tools/run_development.sh
tox
```

**README**
- Make sure that you add the documentation for the field added to README.md


LICENSE
====================

Copyright DRF EXTRA FIELDS HIPO

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
