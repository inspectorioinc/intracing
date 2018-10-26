from setuptools import find_packages, setup

import intracing

OPENTRACING_INSTRUMENTATION_VERSION = '2.5.0.dev0'

setup(
    python_requires='>=2.7',
    author='Aliaksei Urbanski',
    author_email='aliaksei@inspectorio.com',
    url='https://gitlab.inspectorio.com/saas/libs/inspectorio-tracing',
    name='intracing',
    version=intracing.__version__,
    description='Inspectorio Tracing Helper',
    install_requires=[
        'flask',
        'flask-opentracing',
        'jaeger-client',
        'opentracing<2',
        'opentracing-instrumentation==' + OPENTRACING_INSTRUMENTATION_VERSION,
    ],
    dependency_links=[
        'git+https://github.com/Jamim/opentracing-python-instrumentation.git'
        '@fix/register-type'
        '#egg=opentracing_instrumentation-{version}'.format(
            version=OPENTRACING_INSTRUMENTATION_VERSION
        )
    ],
    packages=find_packages(
        exclude=['tests']
    )
)
