from django.conf.urls import url
from django.http import HttpResponse


def home(request):
    return HttpResponse()


urlpatterns = [
    url(r'^$', home),
]
