import mock
import pytest

from intracing.django import InspectorioDjangoTracer
from intracing.flask import InspectorioFlaskTracer


class TestTracers(object):

    @pytest.mark.parametrize('method', ('inject', 'extract', 'start_span'))
    @pytest.mark.parametrize('tracer_class', (
            InspectorioDjangoTracer,
            InspectorioFlaskTracer,
    ))
    def test_tracer_method(self, method, tracer_class):
        args = ('foo', 'bar')
        kwargs = {'foo': 'bar'}
        jaeger_tracer_mock = mock.Mock()
        tracer_getter_mock = mock.Mock(return_value=jaeger_tracer_mock)
        tracer = tracer_class(tracer_getter_mock)
        getattr(tracer, method)(*args, **kwargs)
        getattr(jaeger_tracer_mock, method).assert_called_once_with(
            *args, **kwargs
        )
