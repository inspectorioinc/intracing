from setuptools import find_packages, setup

setup(
    python_requires='>=2.7',
    name='intracing',
    version='1.0.0',
    description='Inspectorio Tracing Helper',
    install_requires=[
        'flask',
        'flask-opentracing',
        'jaeger-client',
        'opentracing-instrumentation',
        'requests',
    ],
    packages=find_packages(
        exclude=['tests']
    )
)
