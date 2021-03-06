from __future__ import absolute_import

import opentracing
from flask import request
from flask_opentracing import FlaskTracer
from opentracing_instrumentation.request_context import RequestContextManager

from .base import IntracingTracerMixin, TracingHelper


class IntracingFlaskTracer(IntracingTracerMixin, FlaskTracer):
    pass


class FlaskTracingHelper(TracingHelper):

    COMPONENT = 'Flask'

    @classmethod
    def get_tracer(cls, app):
        return IntracingFlaskTracer(
            cls.init_jaeger_tracer, trace_all_requests=True, app=app
        )

    @classmethod
    def configure_component(cls, app):
        app.before_first_request(cls.apply_patches)
        app.before_request(cls.enter_request_context)
        app.after_request(cls.exit_request_context)

    @classmethod
    def enter_request_context(cls):
        span = opentracing.tracer.get_span()
        cls.set_request_tags(
            span,
            request.method,
            request.url,
            request.user_agent.string,
            request.content_type,
            request.data,
        )
        request.tracing_context = RequestContextManager(span)
        request.tracing_context.__enter__()

    @classmethod
    def exit_request_context(cls, response):
        span = opentracing.tracer.get_span()
        body = response.data if not response.direct_passthrough else None
        cls.set_response_tags(
            span,
            response.status_code,
            response.content_type,
            body,
        )
        request.tracing_context.__exit__()
        return response


configure_tracing = FlaskTracingHelper.configure_tracing
