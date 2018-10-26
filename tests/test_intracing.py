import os

import mock
import pytest
import requests
from flask import Flask
from jaeger_client.constants import TRACE_ID_HEADER
from jaeger_client.reporter import InMemoryReporter
from jaeger_client.thrift_gen.jaeger.ttypes import TagType
from opentracing.ext import tags

from intracing import configure_tracing
from intracing.intracing import InspectorioTracer, TracingHelper as Helper


class TestInspectorioTracer(object):

    def test_inject(self):
        args = ('foo', 'bar')
        kwargs = {'foo': 'bar'}
        jaeger_tracer_mock = mock.NonCallableMock()
        tracer = InspectorioTracer(jaeger_tracer_mock)
        tracer.inject(*args, **kwargs)
        jaeger_tracer_mock.inject.assert_called_once_with(*args, **kwargs)

    def test_start_span(self):
        args = ('foo', 'bar')
        kwargs = {'foo': 'bar'}
        jaeger_tracer_mock = mock.NonCallableMock()
        tracer = InspectorioTracer(jaeger_tracer_mock)
        tracer.start_span(*args, **kwargs)
        jaeger_tracer_mock.start_span.assert_called_once_with(*args, **kwargs)


TEST_ENV_VARIABLES = {
    'TRACING_ENABLED': 'y',
    'TRACING_SERVICE_NAME': 'test-service',
}


def get_app():
    app = Flask(__name__)
    configure_tracing(app)
    return app


@pytest.fixture
def app():
    with mock.patch.dict(os.environ, TEST_ENV_VARIABLES):
        return get_app()


@pytest.fixture(autouse=True)
def reporter():
    reporter = InMemoryReporter()
    with mock.patch('jaeger_client.config.Reporter', return_value=reporter):
        yield reporter


class TestTracingHelper(object):

    @staticmethod
    def assert_tag(tag, **attrs):
        for key, value in attrs.items():
            assert getattr(tag, key) == value

    def test_disabled(self):
        app = get_app()
        assert app.before_first_request_funcs == []
        assert app.before_request_funcs == {}
        assert app.after_request_funcs == {}

    def test_enabled(self, app):
        assert app.before_first_request_funcs
        assert Helper.enter_request_context in app.before_request_funcs[None]
        assert Helper.exit_request_context in app.after_request_funcs[None]

    @mock.patch('jaeger_client.config.Config.new_tracer')
    def test_tracer_initialization(self, new_tracer_mock, app):
        app.test_client().get('/')  # making request to init tracer
        new_tracer_mock.assert_called_once()

    @mock.patch('requests.adapters.HTTPAdapter.cert_verify')
    @mock.patch('requests.adapters.HTTPAdapter.get_connection')
    @pytest.mark.parametrize('headers', (None, {'foo': 'bar'}))
    @pytest.mark.parametrize('status_code', (200, 404))
    def test_requests_patching(self, get_connection_mock, cert_verify_mock,
                               app, headers, status_code, reporter):
        url = 'http://example.com'
        urlopen = get_connection_mock.return_value.urlopen
        urlopen.return_value.status = status_code

        @app.route('/')
        def get():
            requests.get(url, headers=headers)
            return ''

        response = app.test_client().get('/')
        assert response.status_code == 200

        actual_headers = urlopen.call_args[1]['headers']
        assert TRACE_ID_HEADER in actual_headers
        if headers:
            assert 'foo' in actual_headers

        if status_code == 404:
            tag_error = reporter.spans[0].tags[-1]
            self.assert_tag(tag_error, key=tags.ERROR,
                            vType=TagType.BOOL, vBool=True)
        else:
            for tag in reporter.spans[0].tags:
                assert tag.key != tags.ERROR

    @pytest.mark.parametrize('method', ('GET', 'POST', 'PUT', 'DELETE'))
    @pytest.mark.parametrize('status_code', (200, 404))
    def test_tag_setting(self, app, method, status_code, reporter):

        @app.route('/', methods=[method])
        def get():
            return '', status_code

        response = app.test_client().open('/', method=method)
        assert response.status_code == status_code

        view_span_tags = reporter.spans[-1].tags

        self.assert_tag(view_span_tags[2], key=tags.SPAN_KIND,
                        vType=TagType.STRING, vStr=tags.SPAN_KIND_RPC_SERVER)

        self.assert_tag(view_span_tags[3], key=tags.COMPONENT,
                        vType=TagType.STRING, vStr='Flask')

        self.assert_tag(view_span_tags[4], key=tags.HTTP_METHOD,
                        vType=TagType.STRING, vStr=method)

        self.assert_tag(view_span_tags[5], key=tags.HTTP_URL,
                        vType=TagType.STRING, vStr='http://localhost/')

        tag_http_status_code = view_span_tags[6]
        self.assert_tag(tag_http_status_code, key=tags.HTTP_STATUS_CODE,
                        vType=TagType.LONG, vLong=status_code)

        if status_code == 404:
            tag_error = view_span_tags[-1]
            self.assert_tag(tag_error, key=tags.ERROR,
                            vType=TagType.BOOL, vBool=True)
        else:
            for tag in view_span_tags:
                assert tag.key != tags.ERROR
