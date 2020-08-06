try:
    from django.contrib.postgres.fields import FloatRangeField
except ImportError:
    FloatRangeField = None
