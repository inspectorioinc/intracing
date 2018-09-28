import os

import mock
import pytest
import requests
from flask import Flask
from jaeger_client.constants import TRACE_ID_HEADER
from jaeger_client.reporter import InMemoryReporter
from jaeger_client.thrift_gen.jaeger.ttypes import TagType

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


@pytest.fixture(autouse=True, scope='module')
def reporter():
    reporter = InMemoryReporter()
    with mock.patch('jaeger_client.config.Reporter', return_value=reporter):
        yield reporter


class TestTracingHelper(object):

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
    @pytest.mark.parametrize('headers,ok', [
        (None, True),
        (None, False),
        ({'foo': 'bar'}, True),
        ({'foo': 'bar'}, False),
    ])
    def test_requests_patching(self, get_connection_mock, cert_verify_mock,
                               app, headers, ok, reporter):
        url = 'http://example.com'
        urlopen = get_connection_mock.return_value.urlopen
        urlopen.return_value.status = 200 if ok else 404

        @app.route('/')
        def get():
            requests.get(url, headers=headers)

        app.test_client().get('/')
        actual_headers = urlopen.call_args[1]['headers']
        assert TRACE_ID_HEADER in actual_headers
        if headers:
            assert 'foo' in actual_headers

        if not ok:
            error_tag = reporter.spans[-1].tags[-1]
            assert error_tag.key == 'error'
            assert error_tag.vType == TagType.BOOL
            assert error_tag.vBool
