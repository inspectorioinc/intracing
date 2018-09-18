import os

import mock
import requests
from flask import Flask
from jaeger_client.constants import TRACE_ID_HEADER

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


class TestTracingHelper(object):

    TEST_ENV_VARIABLES = {
        'TRACING_ENABLED': 'y',
        'TRACING_SERVICE_NAME': 'test-service',
    }

    @property
    def app(self):
        app = Flask(__name__)
        configure_tracing(app)
        return app

    def test_disabled(self):
        app = self.app

        assert app.before_first_request_funcs == []
        assert app.before_request_funcs == {}
        assert app.after_request_funcs == {}

    @mock.patch.dict(os.environ, TEST_ENV_VARIABLES)
    def test_enabled(self):
        app = self.app

        assert app.before_first_request_funcs
        assert Helper.enter_request_context in app.before_request_funcs[None]
        assert Helper.exit_request_context in app.after_request_funcs[None]

    @mock.patch.dict(os.environ, TEST_ENV_VARIABLES)
    @mock.patch('jaeger_client.config.Config.new_tracer')
    def test_tracer_initialization(self, new_tracer_mock):
        self.app.test_client().get('/')  # making request to init tracer
        new_tracer_mock.assert_called_once()

    @mock.patch.dict(os.environ, TEST_ENV_VARIABLES)
    def test_requests_patching(self, requests_mock):
        app = self.app
        url = 'http://example.com'
        requests_mock.get(url)

        @app.route('/')
        def get():
            requests.get(url)

        @app.route('/with-headers')
        def get_with_headers():
            requests.get(url, headers={'foo': 'bar'})

        app.test_client().get('/')
        assert TRACE_ID_HEADER in requests_mock.last_request.headers

        app.test_client().get('/with-headers')
        assert TRACE_ID_HEADER in requests_mock.last_request.headers
        assert 'foo' in requests_mock.last_request.headers

        requests.get(url)
        assert TRACE_ID_HEADER not in requests_mock.last_request.headers
