import django

try:
    from django.contrib.postgres import fields as postgres_fields

    if django.VERSION >= (4, 2):
        try:
            from psycopg.types.range import DateRange, NumericRange
            from psycopg.types.range import TimestamptzRange as DateTimeTZRange
        except ImportError:
            from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange
    else:
        from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange
except ImportError:
    postgres_fields = None
    DateRange = None
    DateTimeTZRange = None
    NumericRange = None
