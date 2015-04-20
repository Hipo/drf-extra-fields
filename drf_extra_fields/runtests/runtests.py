import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
os.environ['DJANGO_SETTINGS_MODULE'] = 'drf_extra_fields.runtests.settings'

import django
from django.conf import settings
from django.test.utils import get_runner


def usage():
    return """
    Usage: python runtests.py [UnitTestClass].[method]

    You can pass the Class name of the `UnitTestClass` you want to test.

    Append a method name if you only want to test a specific method of
    that class.
    """


def main():
    try:
        django.setup()
    except AttributeError:
        pass
    TestRunner = get_runner(settings)

    test_runner = TestRunner()
    if len(sys.argv) == 2:
        test_case = '.' + sys.argv[1]
    elif len(sys.argv) == 1:
        test_case = ''
    else:
        print(usage())
        sys.exit(1)
    test_module_name = 'tests'
    if django.VERSION[0] == 1 and django.VERSION[1] < 6:
        test_module_name = 'drf_extra_fields.runtests'

    failures = test_runner.run_tests([test_module_name + test_case])

    sys.exit(failures)

if __name__ == '__main__':
    main()
