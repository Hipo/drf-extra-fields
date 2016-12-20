DRF-EXTRA-FIELDS
================

Extra Fields for Django Rest Framework

![https://travis-ci.org/Hipo/drf-extra-fields.svg?branch=master](https://travis-ci.org/Hipo/drf-extra-fields.svg?branch=master)

Usage
================
 
install the package
 
```bash
pip install django-extra-fields
```

**Note:** 
- Install version 0.1 for Django Rest Framework 2.*
- Install version 0.3 or greater for Django Rest Framework 3.*


Fields:
----------------


## Base64ImageField

An image representation for Base64ImageField

Intherited by `ImageField`


**Signature:** `Base64ImageField()`

 - It takes a base64 image as a string.
 - a base64 image:  `data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7`
 - Base64ImageField accepts the entire string or just the part after base64, `R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7`
 - It takes the optional parameter represent_in_base64(False by default), if set to True it wil allow for base64-encoded downloads of an ImageField.
 - You can inherit the Base64ImageField class and set allowed extensions (ALLOWED_TYPES list), or customize the validation messages (INVALID_FILE_MESSAGE, INVALID_TYPE_MESSAGE)


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

An file representation for Base64FileField

Intherited by `FileField`


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


class RangeSerizalizer(serializers.Serializer):
    ranges = IntegerRangeField()


serializer = RangeSerizalizer(data={'ranges': {'upper': 0, 'upper': 1}})

```

## FloatRangeField

```python
from rest_framework import serializers
from drf_extra_fields.fields import FloatRangeField


class RangeSerizalizer(serializers.Serializer):
    ranges = FloatRangeField()


serializer = IntegerRangeSerizalizer(data={'ranges': {'upper': 0., 'upper': 1.}})

```

## DateRangeField

```python
import datetime

from rest_framework import serializers
from drf_extra_fields.fields import DateRangeField


class RangeSerizalizer(serializers.Serializer):
    ranges = DateRangeField()


serializer = RangeSerizalizer(data={'ranges': {'upper': datetime.date(2015, 1, 1), 'upper': datetime.date(2015, 2, 1)}})

```

## DateTimeRangeField

```python
import datetime

from rest_framework import serializers
from drf_extra_fields.fields import DateTimeRangeField


class RangeSerizalizer(serializers.Serializer):
    ranges = DateTimeRangeField()


serializer = RangeSerizalizer(data={'ranges': {'upper': datetime.datetime(2015, 1, 1, 0), 'upper': datetime.datetime(2015, 2, 1, 0)}})

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
        queryset=User.objects,
        presentation_serializer=UserSerializer
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


CONTRIBUTION
=================

**TESTS**
- Make sure that you add the test for contributed field to test/test_fields.py
and run with command before sending a pull request:

```bash
$ pip install tox  # if not already installed
$ tox -e py27
```

Or, if you prefer using Docker (interactively):

```bash
docker pull lambdacomplete/drf-extra-fields
docker run -i -t lambdacomplete/drf-extra-fields /bin/bash
$ tox -e py27
```

To build the image yourself and run the tests automatically:
```bash
docker build -t ${MY_IMAGE} .
docker run ${MY_IMAGE}
```

*Note:* mounting the working directory via `-v` prevents tox from running (tox uses hard links which do not work with mounted directories). We are still working on this.

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
