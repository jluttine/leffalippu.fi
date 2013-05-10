from django.conf.urls import patterns, include, url
from leffalippu import views
from leffalippu import bitcoin

# Uncomment the next two lines to enable the admin:
#from leffalippu import admin
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'leffalippu.views.home', name='home'),
    url(r'^$', views.order, name='order'),
    #url(r'^cancel/$', views.cancel, name='cancel'),
    url(r'^peru/(?P<order_id>.+)/$', views.cancel, name='cancel'),
#url(r'^pay/(?P<order_id>.+)/$', views.pay, name='pay'),
#url(r'^delete/(?P<order_id>.+)/$', views.delete, name='delete'),
    url(r'^callback/(?P<encrypted_pk>.+)/$', bitcoin.callback, name='callback'),
#url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
#url(r'^$', views.OrderView.as_view(), name='order'),
    # url(r'^leffalippu/', include('leffalippu.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Captcha URLs for simple-captcha
    #url(r'^captcha/', include('captcha.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
