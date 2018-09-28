from setuptools import find_packages, setup

OPENTRACING_INSTRUMENTATION_VERSION = '2.5.0.dev0'

setup(
    python_requires='>=2.7',
    author='Aliaksei Urbanski',
    author_email='aliaksei@inspectorio.com',
    url='https://gitlab.inspectorio.com/saas/libs/inspectorio-tracing',
    name='intracing',
    version='1.0.1',
    description='Inspectorio Tracing Helper',
    install_requires=[
        'flask',
        'flask-opentracing',
        'jaeger-client',
        'opentracing<2',
        'opentracing-instrumentation==' + OPENTRACING_INSTRUMENTATION_VERSION,
        'requests',
    ],
    dependency_links=[
        'git+https://github.com/Jamim/opentracing-python-instrumentation.git'
        '@feature/response-handler-hook'
        '#egg=opentracing_instrumentation-{version}'.format(
            version=OPENTRACING_INSTRUMENTATION_VERSION
        )
    ],
    packages=find_packages(
        exclude=['tests']
    )
)
