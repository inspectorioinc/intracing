# Inspectorio tracing

This library provides helpers that simplifies
[instrumentation](https://en.wikipedia.org/wiki/Instrumentation_(computer_programming))
of `Django` and `Flask` web applications
for distributed trace collection following
[OpenTracing](http://opentracing.io/documentation/) specification.
Currently, it only supports [Jaeger](https://github.com/jaegertracing/jaeger)
as a backend for trace collection.


### Installation

Starting from `1.1.0` version, you have to use `django` or `flask` extras
in your `Pipfile` in purpose to install corresponding dependencies, e.g.
```toml
intracing = {git = "ssh://git@gitlab.inspectorio.com/saas/libs/inspectorio-tracing.git", ref = "v1.1.0", extras = ["django"]}
```

### Usage

#### Flask

You just need to call `configure_tracing` to instrument your `Flask` app.
```python
from flask import Flask
from intracing import configure_tracing

app = Flask(__name__)
configure_tracing(app)
```

#### Django

You just need to add `'intracing'` into the
[`INSTALLED_APPS` list](https://docs.djangoproject.com/en/stable/ref/settings/#installed-apps)
in your Django settings.
```python
INSTALLED_APPS = [
    'intracing',
    # some other apps here
]
```

### Configuration

To enable tracing, you must provide both
`TRACING_ENABLED` and `TRACING_SERVICE_NAME` environment variables:
```bash
TRACING_ENABLED=1
TRACING_SERVICE_NAME="mock-service-staging"
```

`TRACING_ENABLED` variable might be `true`, `on`, `ok`, `y`, or `yes` as well.
It's also case-insensitive.  
Any other values will be casted as `False`,
so tracing will be disabled in that case.

Value of `TRACING_SERVICE_NAME` variable will be used
to identify your service at the `APM`.

You can also configure `APM` agent location using
`TRACING_AGENT_HOST` and `TRACING_AGENT_PORT` environment variables.
Usually you should provide at least `TRACING_AGENT_HOST` variable,
since the default value is `localhost`.

Logging can be enabled using `TRACING_LOGGING` variable.

### Testing

The following versions of Python interpreter should be available locally:
* 2.7
* 3.6
* 3.7

Use [tox](https://tox.readthedocs.io/en/latest/) to run tests.
```bash
PIP_PROCESS_DEPENDENCY_LINKS=1 tox
```
