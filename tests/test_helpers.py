import mock
import opentracing
import pytest

import intracing
from intracing.base import TracingHelper
from intracing.django import IntracingDjangoMiddleware
from intracing.flask import FlaskTracingHelper


class TestHelpers(object):

    @pytest.mark.parametrize('helper,args', (
            (TracingHelper, []),
            (IntracingDjangoMiddleware, []),
            (FlaskTracingHelper, [mock.Mock()]),
    ))
    def test_configure_twice(self, helper, args):
        helper.tracing_configured = False
        helper.configure_tracing(*args)
        assert helper.tracing_configured

        tracer = opentracing.tracer
        if helper is not TracingHelper:
            tracer = tracer._tracer

        assert tracer.tags['intracing.version'] == intracing.__version__

        with mock.patch.object(helper, '_configure_tracing') as configure_mock:
            helper.configure_tracing(*args)
            configure_mock.assert_not_called()
