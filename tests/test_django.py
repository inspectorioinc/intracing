import sys

import mock
import opentracing
import pytest
from django.conf import settings
from jaeger_client.reporter import InMemoryReporter

from intracing.django import IntracingDjangoMiddleware

from .utils import assert_http_view_span


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

    def test_django_middleware(self, client, reporter):
        response = client.get('/')
        assert response.status_code == 200

        view_span = reporter.spans[0]
        assert view_span.operation_name == 'home'

        assert_http_view_span(view_span,
                              component='Django',
                              method='GET',
                              url='http://testserver/',
                              status_code=200)

    @pytest.mark.parametrize('middleware', (None, []))
    @mock.patch.dict(sys.modules)
    def test_configure_component(self, middleware, client, reporter):
        with mock.patch.object(settings, 'MIDDLEWARE', middleware):
            assert settings.MIDDLEWARE == middleware
            IntracingDjangoMiddleware.configure_component()
            assert settings.MIDDLEWARE == [
                'intracing.' + IntracingDjangoMiddleware.__name__
            ]
