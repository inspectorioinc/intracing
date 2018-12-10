from django.conf.urls import url
from django.http import HttpResponse


RESPONSE_CONTENT_TYPE = 'application/json'
RESPONSE_DATA = b'{"foo": "bar"}'


def home(request):
    return HttpResponse(RESPONSE_DATA, content_type=RESPONSE_CONTENT_TYPE)


urlpatterns = [
    url(r'^$', home),
]
