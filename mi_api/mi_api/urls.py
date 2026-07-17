"""
URL configuration for mi_api project.
"""
from django.urls import path
from mi_api import settings
from mi_api.api import api
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse


def home(request):
    return HttpResponse(
        "<h1>Mi API</h1>"
        "<p>Documentación: <a href='/api/docs'>/api/docs</a> (Swagger)</p>"
        "<p>ReDoc: <a href='/api/redoc'>/api/redoc</a></p>"
    )


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)