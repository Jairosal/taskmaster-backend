from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/', include('users.urls')),
    path('api/', include('tasks.urls')),
]