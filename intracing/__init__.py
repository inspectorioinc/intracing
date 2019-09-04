import six
from thrift.compat import str_to_binary
from thrift.protocol.TCompactProtocol import TCompactProtocol

try:
    from .django import IntracingDjangoMiddleware  # noqa: F401
    default_app_config = 'intracing.django.IntracingAppConfig'
except ImportError:
    pass

try:
    from .flask import configure_tracing  # noqa: F401
except ImportError:
    pass


def write_string(proto, value):
    if not isinstance(value, six.binary_type):
        value = str_to_binary(value)
    proto.writeBinary(value)


# monkey patching in purpose to avoid Python 3 compatibility issue
TCompactProtocol.writeString = write_string


__version__ = '1.1.10.dev0'
