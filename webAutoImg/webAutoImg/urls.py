"""webAutoImg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin

from uploadpic.views import show
from uploadpic.views import upload
from autoimage.views import savedemand
from autoimage.views import index
from autoimage.views import showimages

from django.conf.urls.static import static
from django.conf import settings

from . import view

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^index/', index),
    url(r'^autoimage', view.imageDemand),
    url(r'^upload', upload),
    url(r'^show$', show),
    url(r'^savedemand', savedemand),
    url(r'^showimages', showimages),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
