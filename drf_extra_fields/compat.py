# contrib.postgres only supported from 1.8 onwards.
try:
    from django.contrib.postgres import fields as postgres_fields
    from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange
except ImportError:
    postgres_fields = DateRange = DateTimeTZRange = NumericRange = None

# django.utils.six has been removed in Django 3.0
try:
    from django.utils.six import string_types, text_type
except ImportError:
    string_types = str
    text_type = str
