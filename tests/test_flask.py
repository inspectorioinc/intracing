import mock
import pytest
import requests
from faker import Faker
from flask import Response
from jaeger_client.constants import TRACE_ID_HEADER
from jaeger_client.thrift_gen.jaeger.ttypes import TagType
from jaeger_client.reporter import InMemoryReporter
from opentracing.ext import tags

from intracing.flask import FlaskTracingHelper as Helper

from .utils import (
    assert_http_view_span,
    assert_tag,
    disable_tracing,
    get_flask_app,
    with_http_body_size_limit,
)


app = pytest.fixture(get_flask_app, name='app')


@pytest.fixture(autouse=True)
def reporter():
    reporter = InMemoryReporter()
    with mock.patch('jaeger_client.config.Reporter', return_value=reporter):
        yield reporter


class TestFlaskTracingHelper(object):

    @disable_tracing
    def test_tracing_disabled(self):
        app = get_flask_app()
        assert app.before_first_request_funcs == []
        assert app.before_request_funcs == {}
        assert app.after_request_funcs == {}

    def test_tracing_enabled(self, app):
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
            assert_tag(tag_error, key=tags.ERROR,
                       vType=TagType.BOOL, vBool=True)
        else:
            for tag in reporter.spans[0].tags:
                assert tag.key != tags.ERROR

    @pytest.mark.parametrize('method', ('GET', 'POST', 'PUT', 'DELETE'))
    @pytest.mark.parametrize('status_code', (200, 404))
    def test_tag_setting(self, app, method, status_code, reporter):
        request_content_type = 'text/plain'
        request_data = Faker().text().encode('utf-8')
        response_content_type = 'application/json'
        response_data = b'{"foo": "bar"}'

        @app.route('/', methods=[method])
        def get():
            return Response(response_data, status=status_code,
                            content_type=response_content_type)

        test_client = app.test_client()
        response = test_client.open('http://localhost/',
                                    method=method,
                                    data=request_data,
                                    content_type=request_content_type)
        assert response.status_code == status_code

        user_agent = test_client.environ_base['HTTP_USER_AGENT']
        assert_http_view_span(reporter.spans[-1],
                              component='Flask',
                              method=method,
                              url='http://localhost/',
                              user_agent=user_agent,
                              status_code=status_code,
                              request_content_type=request_content_type,
                              request_body=request_data,
                              response_content_type=response_content_type,
                              response_body=response_data)

    @with_http_body_size_limit(limit=50)
    def test_http_body_size_limit_fitted(self, limit, reporter):
        data = Faker().text(limit).encode('utf-8')
        app = get_flask_app()
        assert Helper.http_body_size_limit == limit

        @app.route('/')
        def get():
            return data, 200

        response = app.test_client().get('/')
        assert response.status_code == 200

        assert_tag(reporter.spans[0].tags[-2], key='http.response.body',
                   vType=TagType.STRING, vStr=data)

    @with_http_body_size_limit(limit=50)
    def test_http_body_size_limit_exceeded(self, limit, reporter):
        data = b'0' * (limit + 1)
        app = get_flask_app()
        assert Helper.http_body_size_limit == limit

        @app.route('/')
        def get():
            return data, 200

        response = app.test_client().get('/')
        assert response.status_code == 200

        for tag in reporter.spans[0].tags:
            assert tag.key != 'http.response.body'
