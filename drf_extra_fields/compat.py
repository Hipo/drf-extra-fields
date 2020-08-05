try:
    from django.contrib.postgres.fields import FloatRangeField
except ImportError:
    FloatRangeField = None

try:
    from django.contrib.postgres.fields import DecimalRangeField
except ImportError:
    DecimalRangeField = None
