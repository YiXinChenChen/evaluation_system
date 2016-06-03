"""medusa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, patterns, include
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='sqa/', permanent=False)),
    #url(r'^admin/', admin.site.urls),
    url(r'^sqa/', include('sqa.urls')),
    # url(r'^management/', include('management.urls')),
]

# Local urls
try:
    url_module = __import__('medusa.dev_urls', globals(), locals(), 'dev_urls')
    urlpatterns = url_module.urlpatterns
except ImportError, e:
    # Ignore
    print e
    pass
