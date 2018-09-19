from setuptools import find_packages, setup

setup(
    python_requires='>=2.7',
    author='Aliaksei Urbanski',
    author_email='aliaksei@inspectorio.com',
    url='https://gitlab.inspectorio.com/saas/libs/inspectorio-tracing',
    name='intracing',
    version='1.0.0',
    description='Inspectorio Tracing Helper',
    install_requires=[
        'flask',
        'flask-opentracing',
        'jaeger-client',
        'opentracing<2',
        'opentracing-instrumentation',
        'requests',
    ],
    packages=find_packages(
        exclude=['tests']
    )
)
