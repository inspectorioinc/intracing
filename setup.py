import os
import re

from setuptools import find_packages, setup

PACKAGE_NAME = 'intracing'
REPOSITORY_URL = 'https://github.com/inspectorioinc/intracing'

OPENTRACING_INSTRUMENTATION_LINK = (
    'git+https://github.com/Jamim/opentracing-python-instrumentation.git'
    '@fix/psycopg2'
    '#egg=opentracing_instrumentation'
)


def read(*paths):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), *paths)
    with open(path) as input_file:
        return input_file.read()


def get_version():
    """Get a version string from the source code"""

    return re.search(
        r"^__version__ = '(?P<version>.*?)'.*$",
        read(PACKAGE_NAME, '__init__.py'), re.MULTILINE
    ).group('version')


def get_long_description():
    """Generate a long description from the README file"""

    return read('README.md')


setup(
    name=PACKAGE_NAME,
    url=REPOSITORY_URL,
    version=get_version(),
    description='OpenTracing instrumentation helper. '
                'Helps to easily enable tracing for any applications.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Aliaksei Urbanski',
    author_email='mimworkmail@gmail.com',
    license='MIT',
    install_requires=[
        'jaeger-client<4',
        'opentracing<2',
        'opentracing-instrumentation @ ' + OPENTRACING_INSTRUMENTATION_LINK,
        'six',
    ],
    python_requires='>=2.7',
    extras_require={
        'django': ['django_opentracing==0.1.20'],
        'flask': ['flask-opentracing==0.2.0'],
    },
    packages=find_packages(
        exclude=['tests']
    ),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Source': REPOSITORY_URL,
        'Tracker': REPOSITORY_URL + '/issues',
    },
)
