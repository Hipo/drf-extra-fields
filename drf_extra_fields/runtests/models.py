"""
Django ORM models for the JSON API examples.
"""

import uuid

from django.db import models
from django.contrib.contenttypes import fields as ct_fields
from django.contrib.contenttypes import models as ct_models


class Person(models.Model):
    """
    Example related model with UUID.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, blank=False, editable=False, unique=True)
    name = models.CharField(max_length=255)

    related_to_type = models.ForeignKey(
        ct_models.ContentType, on_delete=models.CASCADE,
        related_name='related_to_type', null=True, blank=True)
    related_to_id = models.PositiveIntegerField(null=True, blank=True)
    related_to = ct_fields.GenericForeignKey(
        'related_to_type', 'related_to_id')


class Article(models.Model):
    """
    Example model with UUID.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, blank=False, editable=False, unique=True)
    author = models.ForeignKey(
        Person, blank=False, related_name='articles')
