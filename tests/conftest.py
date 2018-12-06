from os import environ

environ['TRACING_ENABLED'] = '1'
environ['TRACING_SERVICE_NAME'] = 'test-service'
environ['TRACING_STORE_HTTP_BODY'] = '1'
