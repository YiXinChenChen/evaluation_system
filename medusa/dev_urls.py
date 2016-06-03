from django.conf.urls import url, patterns, include
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='sqa/', permanent=False)),
    url(r'^admin/', admin.site.urls),
    url(r'^sqa/', include('sqa.urls')),
    url(r'^management/', include('management.urls')),
]