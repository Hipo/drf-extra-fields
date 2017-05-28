import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-extra-fields',
    version='0.9',
    packages=['drf_extra_fields',
              'drf_extra_fields.runtests'],
    include_package_data=True,
    license='License',  # example license
    description='Additional fields for Django Rest Framework.',
    long_description=README,
    author='hipo',
    author_email='pypi@hipolabs.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=['django<1.11', 'djangorestframework>=3.0'],
    test_suite='setuptest.setuptest.SetupTestSuite',
    tests_require=['django-setuptest'],
)
