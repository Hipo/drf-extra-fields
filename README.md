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
- Install version 0.3 for Django Rest Framework 3.*


Fields:
----------------


## Base64ImageField

An image representation for Base64ImageField

Intherited by `ImageField`


**Signature:** `Base64ImageField()`

 - It takes a base64 image as a string.
 - a base64 image:  `data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7`
 - Base64ImageField accepts only the part after base64, `R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7`
 

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

CONTRIBUTION
=================

*TESTS*
- Make sure that you add the test for contributed field to test/test_fields.py
and run with command before sending a pull request:

```bash
$ pip install tox  # if not already installed
$ tox
```

*README*
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
