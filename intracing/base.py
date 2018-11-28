import logging
import os

import opentracing
import six
from jaeger_client.thrift_gen.jaeger.ttypes import Tag, TagType
from jaeger_client.config import (
    Config, DEFAULT_REPORTING_HOST, DEFAULT_REPORTING_PORT
)
from opentracing.ext import tags
from opentracing_instrumentation.client_hooks import install_all_patches


class InspectorioTracerMixin(object):

    def inject(self, *args, **kwargs):
        return self._tracer.inject(*args, **kwargs)

    def extract(self, *args, **kwargs):
        return self._tracer.extract(*args, **kwargs)

    def start_span(self, *args, **kwargs):
        return self._tracer.start_span(*args, **kwargs)


class TracingHelperMetaclass(type):

    def __new__(mcs, name, bases, class_dict):
        component = class_dict.get('COMPONENT')
        if component:
            class_dict['TAG_COMPONENT'] = Tag(
                key=tags.COMPONENT, vType=TagType.STRING, vStr=component
            )

        return super(TracingHelperMetaclass, mcs).__new__(
            mcs, name, bases, class_dict
        )


@six.add_metaclass(TracingHelperMetaclass)
class TracingHelper(object):

    TAG_SPAN_KIND = Tag(key=tags.SPAN_KIND, vType=TagType.STRING,
                        vStr=tags.SPAN_KIND_RPC_SERVER)
    TAG_ERROR = Tag(key=tags.ERROR, vType=TagType.BOOL, vBool=True)

    tracing_configured = False
    config = None

    @classmethod
    def requests_response_handler_hook(cls, response, span):
        if not response.ok:
            with span.update_lock:
                span.tags.append(cls.TAG_ERROR)

    @classmethod
    def apply_patches(cls):
        install_all_patches(
            requests_response_handler_hook=cls.requests_response_handler_hook
        )

    @classmethod
    def set_request_tags(cls, span, method, url):
        span.tags.append(cls.TAG_SPAN_KIND)
        span.tags.append(cls.TAG_COMPONENT)
        span.tags.append(Tag(
            key=tags.HTTP_METHOD, vType=TagType.STRING, vStr=method
        ))
        span.tags.append(Tag(
            key=tags.HTTP_URL, vType=TagType.STRING, vStr=url
        ))

    @classmethod
    def set_response_tags(cls, span, status_code):
        span.tags.append(Tag(
            key=tags.HTTP_STATUS_CODE, vType=TagType.LONG, vLong=status_code
        ))
        if not 200 <= status_code < 300:
            span.tags.append(cls.TAG_ERROR)

    @staticmethod
    def is_enabled(key):
        value = os.getenv(key, '').lower()
        return value in {'true', 'on', 'ok', 'y', 'yes', '1'}

    @classmethod
    def configure_tracing(cls, *args, **kwargs):

        if not cls.is_enabled('TRACING_ENABLED'):
            return

        if not cls.tracing_configured:
            cls._configure_tracing(*args, **kwargs)

    @classmethod
    def init_config(cls):
        service_name = os.environ['TRACING_SERVICE_NAME']
        reporting_host = os.getenv('TRACING_AGENT_HOST',
                                   DEFAULT_REPORTING_HOST)
        reporting_port = os.getenv('TRACING_AGENT_PORT',
                                   DEFAULT_REPORTING_PORT)

        cls.config = Config(
            config={
                'sampler': {
                    'type': 'const',
                    'param': 1,
                },
                'local_agent': {
                    'reporting_host': reporting_host,
                    'reporting_port': reporting_port,
                },
                'logging': cls.is_enabled('TRACING_LOGGING'),
            },
            service_name=service_name,
        )

    @classmethod
    def init_jaeger_tracer(cls):
        logging.debug('Initializing Jaeger tracer')

        # this call also sets opentracing.tracer
        return cls.config.new_tracer()

    @classmethod
    def _configure_tracing(cls, *args, **kwargs):
        cls.init_config()
        opentracing.tracer = cls.get_tracer(*args, **kwargs)
        cls.configure_component(*args, **kwargs)

        try:
            from celery.signals import worker_init
        except ImportError:
            pass
        else:
            @worker_init.connect(weak=False)
            def apply_patches(**kwargs):
                cls.apply_patches()

        cls.tracing_configured = True

    @classmethod
    def get_tracer(cls, *args, **kwargs):
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def configure_component(cls, *args, **kwargs):
        raise NotImplementedError  # pragma: no cover


configure_tracing = TracingHelper.configure_tracing
