from django.conf.urls.defaults import *
import views

urlpatterns = patterns('mail',
    url(r'^$', views.home, name="home"),
    url(r'^write$', views.write, name="write"),
    url(r'^mail/(?P<message>\w+)/$',
        views.view_mail_thread,
        name="mail"),
    url(r'^preview/(?P<message>\w+)/$',
        views.preview,
        name="preview"),
    url(r'^process/$',
        views.process_queue,
        name="process_queue"),
    url(r'^logout/$',
        views.logout_view,
        name="logout"),
    url(r'^login_form/$',
        views.login_form,
        name="login_form"),
    url(r'^login_form/(?P<message>\w+)/$',
        views.login_or_register_form,
        name="login_or_register_form"),
)

