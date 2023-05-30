try:
    from django.contrib.postgres.fields import FloatRangeField
except ImportError:
    FloatRangeField = None

try:
    from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange
except ImportError:
    DateRange = None
    DateTimeTZRange = None
    NumericRange = None
