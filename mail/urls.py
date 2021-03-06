from django.conf.urls.defaults import *
import views

email_rx = r"^address/(?P<email>[-a-z0-9_.]+@" + \
           "(?:[-a-z0-9]+\.)+[a-z]{2,6})/$"

urlpatterns = patterns('mail',
    url(r'^$', views.home, name="home"),
    url(r'^write$', views.write, name="write"),
    url(r'^mail/(?P<mail>\w+)/$',
        views.view_mail_thread,
        name="mail"),
    url(email_rx,
        views.view_address,
        name="address"),
    url(r'^preview/(?P<mail>\w+)/$',
        views.preview,
        name="preview"),
    url(r'^approve/(?P<mail>\w+)/(?P<key>\w+)/$',
        views.approve,
        name="approve"),
    url(r'^posted/(?P<mail>\w+)/$',
        views.posted,
        name="posted"),
    url(r'^process/$',
        views.process_queue,
        name="process_queue"),
    url(r'^logout/$',
        views.logout_view,
        name="logout"),
    url(r'^login_form/$',
        views.login_form,
        name="login_form"),
    url(r'^login_form/(?P<mail>\w+)/$',
        views.login_or_register_form,
        name="login_or_register_form"),
)

