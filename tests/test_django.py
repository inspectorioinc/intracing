import sys

import mock
import opentracing
import pytest
from django.conf import settings
from django.test.client import Client
from faker import Faker
from jaeger_client.reporter import InMemoryReporter

from intracing.django import IntracingDjangoMiddleware

from .utils import assert_http_view_span, assert_not_contain_tag
from .django_app.urls import RESPONSE_CONTENT_TYPE, RESPONSE_DATA


@pytest.fixture(scope='module', autouse=True)
def django_tracer():
    IntracingDjangoMiddleware.tracing_configured = False
    IntracingDjangoMiddleware.configure_tracing()


@pytest.fixture
def reporter():
    reporter = InMemoryReporter()
    opentracing.tracer._tracer.reporter = reporter
    return reporter


class TestIntracingDjangoMiddleware(object):

    @staticmethod
    def _test_django(client, reporter, **kwargs):
        response = client.post('/', **kwargs)
        assert response.status_code == 200
        assert response.content == RESPONSE_DATA

        view_span = reporter.spans[0]
        assert view_span.operation_name == 'home'

        return view_span

    def test_django_middleware(self, reporter):
        faker = Faker()

        request_content_type = 'text/plain'
        request_data = faker.text().encode('utf-8')
        user_agent = faker.user_agent()

        client = Client(HTTP_USER_AGENT=user_agent)

        view_span = self._test_django(client, reporter,
                                      data=request_data,
                                      content_type=request_content_type)
        assert_http_view_span(view_span,
                              component='Django',
                              method='POST',
                              url='http://testserver/',
                              user_agent=user_agent,
                              status_code=200,
                              request_content_type=request_content_type,
                              request_body=request_data,
                              response_content_type=RESPONSE_CONTENT_TYPE,
                              response_body=RESPONSE_DATA)

    def test_django_with_no_user_agent(self, client, reporter):
        view_span = self._test_django(client, reporter)
        assert_not_contain_tag(view_span.tags, 'http.user_agent')

    def test_django_not_found(self, client, reporter):
        response = client.get('/foo')
        assert response.status_code == 404
        assert not reporter.spans

    @pytest.mark.parametrize('middleware', (None, []))
    @mock.patch.dict(sys.modules)
    def test_configure_component(self, middleware, client, reporter):
        with mock.patch.object(settings, 'MIDDLEWARE', middleware):
            assert settings.MIDDLEWARE == middleware
            IntracingDjangoMiddleware.configure_component()
            assert settings.MIDDLEWARE == [
                'intracing.' + IntracingDjangoMiddleware.__name__
            ]
