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

## SerializablePKRelatedField

`SerializablePKRelatedField` may be used to represent the target of the relationship using serializer passed as argument.

For example, if we pass `TrackSerializer` the following serializer:

    class AlbumSerializer(serializers.ModelSerializer):
        tracks = serializers.SerializablePKRelatedField(many=True, serializer_class=TrackSerializer)

        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

Would serialize to a representation like this:

    {
        'album_name': 'The Roots',
        'artist': 'Undun',
        'tracks': [
            {
                'order': 1, 
                'title': 'Public Service Announcement', 
                'duration': 245,
            },
            {
                'order': 2, 
                'title': 'What More Can I Say', 
                'duration': 264,
            },
            ...
        ]
    }

By default this field take queryset from passed `serializer_class`.

**Arguments**:

* `queryset` - The queryset used for model instance lookups when validating the field input. Relationships must either set a queryset explicitly, or it based on ModelSerializer model or you set `read_only=True`.
* `many` - If applied to a to-many relationship, you should set this argument to `True`.
* `allow_null` - If set to `True`, the field will accept values of `None` or the empty string for nullable relationships. Defaults to `False`.
* `serializer_class` - serializer class to represent the target of the relationship, required field
* `serializer_params` - Parameters, passed to serializer
* `pk_field` - Set to a field to control serialization/deserialization of the primary key's value. For example, `pk_field=UUIDField(format='hex')` would serialize a UUID primary key into its compact hex representation.



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
