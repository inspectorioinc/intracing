import logging
import os

import opentracing
import requests
from flask import request
from flask_opentracing import FlaskTracer
from jaeger_client.config import (
    Config, DEFAULT_REPORTING_HOST, DEFAULT_REPORTING_PORT
)
from opentracing_instrumentation.client_hooks import install_all_patches
from opentracing_instrumentation.request_context import RequestContextManager


class InspectorioTracer(FlaskTracer):

    def inject(self, *args, **kwargs):
        return self._tracer.inject(*args, **kwargs)

    def start_span(self, *args, **kwargs):
        return self._tracer.start_span(*args, **kwargs)


class TracingHelper(object):

    @staticmethod
    def patch_requests():
        original_request = requests.api.request

        def wrapped_request(*args, **kwargs):
            headers = kwargs.pop('headers', None)
            tracer = opentracing.tracer
            span = tracer.get_span()
            if span:
                if headers is None:
                    headers = {}
                tracer.inject(
                    span, opentracing.Format.HTTP_HEADERS, headers
                )
            return original_request(*args, headers=headers, **kwargs)

        requests.api.request = wrapped_request

    @classmethod
    def apply_patches(cls):
        install_all_patches()
        cls.patch_requests()

    @staticmethod
    def enter_request_context():
        span = opentracing.tracer.get_span()
        request.tracing_context = RequestContextManager(span)
        request.tracing_context.__enter__()

    @staticmethod
    def exit_request_context(response):
        request.tracing_context.__exit__()
        return response

    @classmethod
    def configure_tracing(cls, app):
        tracing_enabled = os.getenv('TRACING_ENABLED', '').lower() in {
            'true', 'on', 'ok', 'y', 'yes', '1'
        }
        if not tracing_enabled:
            return

        service_name = os.environ['TRACING_SERVICE_NAME']
        reporting_host = os.getenv('TRACING_AGENT_HOST',
                                   DEFAULT_REPORTING_HOST)
        reporting_port = os.getenv('TRACING_AGENT_PORT',
                                   DEFAULT_REPORTING_PORT)

        config = Config(
            config={
                'sampler': {
                    'type': 'const',
                    'param': 1,
                },
                'local_agent': {
                    'reporting_host': reporting_host,
                    'reporting_port': reporting_port,
                },
                'logging': __debug__,
            },
            service_name=service_name,
        )

        def init_jaeger_tracer():
            logging.debug('Initializing Jaeger tracer')

            # this call also sets opentracing.tracer
            return config.new_tracer()

        opentracing.tracer = InspectorioTracer(
            init_jaeger_tracer, trace_all_requests=True, app=app
        )
        app.before_first_request(cls.apply_patches)
        app.before_request(cls.enter_request_context)
        app.after_request(cls.exit_request_context)


configure_tracing = TracingHelper.configure_tracing
