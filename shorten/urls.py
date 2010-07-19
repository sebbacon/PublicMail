from django.conf.urls.defaults import *
import views

################################################################################
urlpatterns = patterns('shorten',
    url(r'^(?P<key>[\w-]+)$', views.index, name="shorten"),
)
