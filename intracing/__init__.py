def module_available(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


if module_available('django'):
    from .django import IntracingDjangoMiddleware  # noqa: F401
    default_app_config = 'intracing.django.IntracingAppConfig'

if module_available('flask'):
    from .flask import configure_tracing  # noqa: F401


__version__ = '1.1.2'
