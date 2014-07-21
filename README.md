drf-extra-fields
================

Extra Fields for Django Rest Framework

Usage
================
 
 install the package
 
 `pip install django-extra-fields`



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

    #serializer
    from drf_extra_fields.fields import Base64ImageField

    class UploadedBase64ImageSerializer(serializers.Serializer):
        file = serializers.Base64ImageField(required=False)
        created = serializers.DateTimeField()

    #use the serializer
    file = 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
    serializer = UploadedBase64ImageSerializer(data={'created': now, 'file': file})
    

## PointField

Point field for GeoDjango


**Signature:** `PointField()`

 - It takes a dictionary contains latitude and longitude keys like below


    {
        "latitude": 49.8782482189424,
        "longitude": 24.452545489
    }

    
**Example:**

    #serializer
    from drf_extra_fields.geo_fields import PointField

    class PointFieldSerializer(serializers.Serializer):
        file = PointField(required=False)
        created = serializers.DateTimeField()

    #use the serializer
    point = {
        "latitude": 49.8782482189424,
        "longitude": 24.452545489
        }    
    serializer = PointFieldSerializer(data={'created': now, 'point': point})
