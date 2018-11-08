import logging
import os

import opentracing
from flask import request
from flask_opentracing import FlaskTracer
from jaeger_client.thrift_gen.jaeger.ttypes import Tag, TagType
from jaeger_client.config import (
    Config, DEFAULT_REPORTING_HOST, DEFAULT_REPORTING_PORT
)
from opentracing.ext import tags
from opentracing_instrumentation.client_hooks import install_all_patches
from opentracing_instrumentation.request_context import RequestContextManager


TAG_SPAN_KIND = Tag(key=tags.SPAN_KIND, vType=TagType.STRING,
                    vStr=tags.SPAN_KIND_RPC_SERVER)
TAG_COMPONENT = Tag(key=tags.COMPONENT, vType=TagType.STRING, vStr='Flask')
TAG_ERROR = Tag(key=tags.ERROR, vType=TagType.BOOL, vBool=True)


class InspectorioTracer(FlaskTracer):

    def inject(self, *args, **kwargs):
        return self._tracer.inject(*args, **kwargs)

    def start_span(self, *args, **kwargs):
        return self._tracer.start_span(*args, **kwargs)


class TracingHelper(object):

    @staticmethod
    def requests_response_handler_hook(response, span):
        if not response.ok:
            with span.update_lock:
                span.tags.append(TAG_ERROR)

    @classmethod
    def apply_patches(cls):
        install_all_patches(
            requests_response_handler_hook=cls.requests_response_handler_hook
        )

    @staticmethod
    def enter_request_context():
        span = opentracing.tracer.get_span()
        span.tags.append(TAG_SPAN_KIND)
        span.tags.append(TAG_COMPONENT)
        span.tags.append(Tag(
            key=tags.HTTP_METHOD, vType=TagType.STRING, vStr=request.method
        ))
        span.tags.append(Tag(
            key=tags.HTTP_URL, vType=TagType.STRING, vStr=request.url
        ))
        request.tracing_context = RequestContextManager(span)
        request.tracing_context.__enter__()

    @staticmethod
    def exit_request_context(response):
        span = opentracing.tracer.get_span()
        status_code = response.status_code
        span.tags.append(Tag(
            key=tags.HTTP_STATUS_CODE, vType=TagType.LONG, vLong=status_code
        ))
        if not 200 <= status_code < 300:
            span.tags.append(TAG_ERROR)
        request.tracing_context.__exit__()
        return response

    @classmethod
    def configure_tracing(cls, app):
        def is_enabled(key):
            value = os.getenv(key, '').lower()
            return value in {'true', 'on', 'ok', 'y', 'yes', '1'}

        if not is_enabled('TRACING_ENABLED'):
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
                'logging': is_enabled('TRACING_LOGGING'),
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

        try:
            from celery.signals import worker_init
        except ImportError:
            pass
        else:
            @worker_init.connect(weak=False)
            def apply_patches(**kwargs):
                cls.apply_patches()


configure_tracing = TracingHelper.configure_tracing
