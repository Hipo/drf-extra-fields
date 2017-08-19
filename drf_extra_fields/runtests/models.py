"""
Django ORM models for the JSON API examples.
"""

import uuid

from django.db import models


class Person(models.Model):
    """
    Example related model with UUID.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, blank=False, editable=False, unique=True)
    name = models.CharField(max_length=255)


class Article(models.Model):
    """
    Example model with UUID.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, blank=False, editable=False, unique=True)
    author = models.ForeignKey(
        Person, blank=False, related_name='articles')
