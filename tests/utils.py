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


def assert_next_tag(span_tags, **attrs):
    assert_tag(span_tags.pop(0), **attrs)


def assert_http_view_span(span, component, method, url, status_code,
                          request_content_type=None, request_body=None,
                          response_content_type=None, response_body=None):
    span_tags = span.tags[2:]

    assert_next_tag(span_tags, key=tags.SPAN_KIND,
                    vType=TagType.STRING, vStr=tags.SPAN_KIND_RPC_SERVER)

    assert_next_tag(span_tags, key=tags.COMPONENT,
                    vType=TagType.STRING, vStr=component)

    assert_next_tag(span_tags, key=tags.HTTP_METHOD,
                    vType=TagType.STRING, vStr=method)

    assert_next_tag(span_tags, key=tags.HTTP_URL,
                    vType=TagType.STRING, vStr=url)

    if request_content_type:
        assert_next_tag(span_tags, key='http.request.content_type',
                        vType=TagType.STRING, vStr=request_content_type)

    if request_body:
        assert_next_tag(span_tags, key='http.request.body',
                        vType=TagType.STRING, vStr=request_body)

    if response_content_type:
        assert_next_tag(span_tags, key='http.response.content_type',
                        vType=TagType.STRING, vStr=response_content_type)

    if response_body:
        assert_next_tag(span_tags, key='http.response.body',
                        vType=TagType.STRING, vStr=response_body)

    assert_next_tag(span_tags, key=tags.HTTP_STATUS_CODE,
                    vType=TagType.LONG, vLong=status_code)

    if status_code == 404:
        tag_error = span_tags
        assert_next_tag(tag_error, key=tags.ERROR,
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


def with_http_body_size_limit(limit):
    def wrapper(func):
        def wrapped(self, reporter):
            with mock.patch.dict(os.environ,
                                 TRACING_HTTP_BODY_SIZE_LIMIT=str(limit)):
                return func(self, limit, reporter)
        return wrapped
    return wrapper


def get_flask_app():
    app = Flask(__name__)
    FlaskTracingHelper.tracing_configured = False
    configure_tracing(app)
    return app
