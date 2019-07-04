DRF-EXTRA-FIELDS
================

Extra Fields for Django Rest Framework

[![Build Status](https://travis-ci.org/Hipo/drf-extra-fields.svg?branch=master)](https://travis-ci.org/Hipo/drf-extra-fields)
[![codecov](https://codecov.io/gh/Hipo/drf-extra-fields/branch/master/graph/badge.svg)](https://codecov.io/gh/Hipo/drf-extra-fields)

Usage
================
 
Install the package
 
```bash
pip install django-extra-fields
```

**Note:** 
- Install version 0.1 for Django Rest Framework 2.*
- Install version 0.3 or greater for Django Rest Framework 3.*


Releases
--------

**1.2.3 (Latest version)**

- Added `presentation_serializer_kwargs` attribute to `PresentablePrimaryKeyRelatedField`.

**1.2.2**

- Fixed [a bug](https://github.com/Hipo/drf-extra-fields/pull/75) in Base64ImageField.
- Added codecov support.

**1.2.1**

- Moved filename generation of Base64FieldMixin into a method.


**1.2.0**

- Properly handle blank image fields when `represent_in_base64` is enabled.


**1.1.0**

- Python 3.7 support is added.


**1.0.0**

- `PointField` is changed. The field now returns float coordinates instead of strings. It's a breaking change. If you want to return string coordinates add `str_points=True` as an argument. See [PointField](#pointfield) documentation for more details.


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
 - Other options like for Base64ImageField
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
        }
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

## HybridImageField
A django-rest-framework field for handling image-uploads through raw post data, with a fallback to multipart form data.

It first tries Base64ImageField. if it fails then tries ImageField.

```python
from rest_framework import serializers
from drf_extra_fields.fields import HybridImageField


class HybridImageSerializer(serializers.Serializer):
    image = HybridImageField()
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
docker build -t drf_extra_fields .
docker run -v $(pwd):/app -it drf_extra_fields /bin/bash
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
