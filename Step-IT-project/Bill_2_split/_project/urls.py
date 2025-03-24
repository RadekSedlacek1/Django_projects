from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('Bill_2_split.urls', namespace='Bill_2_split')), #adds prefix bill_2_split:index
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns.extend(debug_toolbar_urls())
