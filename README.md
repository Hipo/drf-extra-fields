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


serializer = RangeSerizalizer(data={'ranges': {'lower': 0, 'upper': 1}})

```

## FloatRangeField

```python
from rest_framework import serializers
from drf_extra_fields.fields import FloatRangeField


class RangeSerizalizer(serializers.Serializer):
    ranges = FloatRangeField()


serializer = IntegerRangeSerizalizer(data={'ranges': {'lower': 0., 'upper': 1.}})

```

## DateRangeField

```python
import datetime

from rest_framework import serializers
from drf_extra_fields.fields import DateRangeField


class RangeSerizalizer(serializers.Serializer):
    ranges = DateRangeField()


serializer = RangeSerizalizer(data={'ranges': {'lower': datetime.date(2015, 1, 1), 'upper': datetime.date(2015, 2, 1)}})

```

## DateTimeRangeField

```python
import datetime

from rest_framework import serializers
from drf_extra_fields.fields import DateTimeRangeField


class RangeSerizalizer(serializers.Serializer):
    ranges = DateTimeRangeField()


serializer = RangeSerizalizer(data={'ranges': {'lower': datetime.datetime(2015, 1, 1, 0), 'upper': datetime.datetime(2015, 2, 1, 0)}})

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

## `relations.PrimaryKeySourceRelatedField` and `relations.UUIDModelSerializer`

The former provides support for relations that use something other than a DB
integer PK for relationships such that you can specify some other field to
use.  The latter is a serializer base class (IOW, meant to be subclassed in
your serializers) that uses the former field to provide model-based
serializers that use UUIDs instead of DB PK values throughout, for both the
primary resource and related resources.  These can be useful for creating APIs
that use UUIDs throughout while still using integer PKs in the DB on the
back-end.

```python
from drf_extra_fields.relations import UUIDModelSerializer

class UserSerializer(UUIDModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
```

## `generic.HyperlinkedGenericRelationsField`

This field supports serializing and deserializing [Django
`django.contrib.contenttypes` generic
relations](https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/#generic-relations)
as hyperlinks.  The `generic.GenericRelationsModelSerializer` serializer base
classes`generic.HyperlinkedGenericRelationsModelSerializer` also support using
this field for generic relations in model serializers:

```python
from drf_extra_fields.generic import HyperlinkedGenericRelationsModelSerializer

class UserSerializer(HyperlinkedGenericRelationsModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
```

## `composite.SerializerListField`, `composite.SerializerDictField`

The DRF composite list and dictionary fields both take a child serialzer
instance but only delegate to the child's `to_internal_value(data)` or
`to_representation(instance)` to deserialize/serialize.  These 2 fields extend
the base DRF composite fields by instantiating the child serializer with each
individual item and attaching it as a `data.serializer` attribute.  This
allows re-using a serializer's `save()`, `create()`, and/or `update()` methods
both as a standalone serializer and as a child of a composite field or just
for better factoring of create/update logic into the related serializer's
methods:

```
from rest_framework import serializers

from drf_extra_fields import composite


class ExampleListSerializer(serializers.Serializer):
    """
    A simple serializer for testing the list composite field.
    """

    children = composite.SerializerListField(
        child=parameterized.ExampleChildSerializer(allow_null=True),
        allow_empty=False)

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return {"children": [
            child_data.serializer.create(child_data)
            for child_data in validated_data["children"]]}
```


## parameterized....

The fields and serializers in the `parameterized` module support using a
different serializer based on a parameter in the JSON.  This can be useful
where a different schema should be used based on some content in the JSON,
such as a `type` field.  In this way, the same endpoint can be used to
retrieve or accept different JSON schemata based on the content.  These fields
also make use of the `composite` module, making it possible to re-use the
specific serializer's `save()`, `create()`, and/or `update()` methods once
looked up per the parameter.

The parameter field can also automatically derive string type parameters from
the model's `verbose_name` of any viewset's `get_queryset()` found in URL
patterns and map those to those viewset's serializers via `get_serializer()`.
This can be used, for example, to create a generic endpoint that accepts JSON
with a `type` key and uses that to lookup the appropriate serializer from
the specific endpoint and delegate to it:

```
from django.contrib.auth import models as auth_models

from rest_framework import serializers

from drf_extra_fields import parameterized


class ExampleChildSerializer(serializers.Serializer):
    """
    A simple serializer for testing composite fields as a child.
    """

    name = serializers.CharField()

    def create(self, validated_data):
        """
        Delegate to the children.
        """
        return validated_data


class ExampleUserSerializer(serializers.ModelSerializer):
    """
    A simple model serializer for testing.
    """

    class Meta:
        model = auth_models.User
        fields = ('username', 'password')


class ExampleTypeFieldSerializer(
        parameterized.ParameterizedGenericSerializer):
    """
    A simple serializer for testing a type field parameter.
    """

    type = parameterized.SerializerParameterField(
        specific_serializers={
            "foo-type": ExampleChildSerializer()})
```


## `serializer_formats`: Serializer-based formats/renderers/parsers

Support for defining JSON formats using DRF serializers.

Many JSON based formats, such as [JSON API](http://jsonapi.org), specify a lot
of structure in the JSON.  As such, defining the format in DRF terms is best
done using DRF serializers.  To support using multiple formats with the same
views/endpoints requires combining the serializer that defines the format with
the specific serializer for the endpoint.  The
`serializer_formats.FormatModelViewset` class will use the `serializer_class`
of the negotiated parser instead of the viewset's `serializer_class`for
create/update requests or of the negotiated renderer for retreive/list
requests if `serializer_class` exists on the parser/renderer.  Note that the
format's `serializer_class` is responsible for incorporating the specific
viewset's `serializer_class`, such as the `composite.CompositeSerializer`
does.  If the format is meant to also render error details, set
`error_serializer_class` on the renderer and it's `to_representation()` method
will be used to generate a representation of the exception.  Similarly, if the
renderer has a `pagination_serializer_class`, it will be used to generate a
represenation of the output of the paginated reponse.


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
