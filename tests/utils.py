import os
from functools import wraps

import mock
from flask import Flask

from intracing import configure_tracing
from intracing.flask import FlaskTracingHelper
from jaeger_client.thrift_gen.jaeger.ttypes import TagType
from opentracing.ext import tags


TRACING_DISABLED_ENV_VARIABLES = {
    'TRACING_ENABLED': '0',
}


def assert_tag(tag, **attrs):
    for key, value in attrs.items():
        assert getattr(tag, key) == value


def assert_http_view_span(span, component, method, url, status_code):
    span_tags = span.tags

    assert_tag(span_tags[2], key=tags.SPAN_KIND,
               vType=TagType.STRING, vStr=tags.SPAN_KIND_RPC_SERVER)

    assert_tag(span_tags[3], key=tags.COMPONENT,
               vType=TagType.STRING, vStr=component)

    assert_tag(span_tags[4], key=tags.HTTP_METHOD,
               vType=TagType.STRING, vStr=method)

    assert_tag(span_tags[5], key=tags.HTTP_URL,
               vType=TagType.STRING, vStr=url)

    assert_tag(span_tags[6], key=tags.HTTP_STATUS_CODE,
               vType=TagType.LONG, vLong=status_code)

    if status_code == 404:
        tag_error = span_tags[-1]
        assert_tag(tag_error, key=tags.ERROR,
                   vType=TagType.BOOL, vBool=True)
    else:
        for tag in span_tags:
            assert tag.key != tags.ERROR


def disable_tracing(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        with mock.patch.dict(os.environ, TRACING_DISABLED_ENV_VARIABLES):
            return func(*args, **kwargs)
    return wrapped


def get_flask_app():
    app = Flask(__name__)
    FlaskTracingHelper.tracing_configured = False
    configure_tracing(app)
    return app
