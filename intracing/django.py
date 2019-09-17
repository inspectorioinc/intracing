from __future__ import absolute_import

import opentracing
from django.apps import AppConfig
from django.conf import settings
from django_opentracing import DjangoTracer, OpenTracingMiddleware
from opentracing_instrumentation.request_context import RequestContextManager

from intracing.base import IntracingTracerMixin, TracingHelper


class IntracingAppConfig(AppConfig):
    name = 'intracing'

    def ready(self):
        IntracingDjangoMiddleware.configure_tracing()


class IntracingDjangoTracer(IntracingTracerMixin, DjangoTracer):

    def __init__(self, tracer_getter):
        self.__tracer = None
        self.__tracer_getter = tracer_getter
        self._current_spans = {}
        self._trace_all = True

    @property
    def _tracer(self):
        if not self.__tracer:
            self.__tracer = self.__tracer_getter()
        return self.__tracer


class IntracingDjangoMiddleware(OpenTracingMiddleware, TracingHelper):

    COMPONENT = 'Django'

    @classmethod
    def get_tracer(cls):
        return IntracingDjangoTracer(cls.init_jaeger_tracer)

    @classmethod
    def configure_component(cls):
        super(IntracingDjangoMiddleware, cls).configure_component()
        middleware_path = 'intracing.' + cls.__name__
        if settings.MIDDLEWARE is None:
            settings.MIDDLEWARE = []
        if middleware_path not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.insert(0, middleware_path)

    def __init__(self, get_response):
        self.get_response = get_response
        self._tracer = opentracing.tracer

    def _get_request_body(self, request):
        # we should avoid getting of the body
        # in case it would cause an exception
        if self.store_http_body and (
                settings.DATA_UPLOAD_MAX_MEMORY_SIZE is None or
                int(
                    request.META.get('CONTENT_LENGTH') or 0
                ) <= settings.DATA_UPLOAD_MAX_MEMORY_SIZE
        ):
            return request.body

    def process_view(self, request, view_func, view_args, view_kwargs):
        super(IntracingDjangoMiddleware, self).process_view(
            request, view_func, view_args, view_kwargs
        )
        span = opentracing.tracer.get_span(request)
        self.set_request_tags(
            span,
            request.method,
            request.get_raw_uri(),
            request.META.get('HTTP_USER_AGENT'),
            request.content_type,
            self._get_request_body(request),
        )
        request.tracing_context = RequestContextManager(span)
        request.tracing_context.__enter__()

    def process_response(self, request, response):
        span = opentracing.tracer.get_span(request)
        if span is None:
            return response

        self.set_response_tags(
            span,
            response.status_code,
            response.get('Content-Type'),
            response.content,
        )
        response = super(IntracingDjangoMiddleware, self).process_response(
            request, response
        )
        request.tracing_context.__exit__()
        return response
