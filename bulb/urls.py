from django.conf.urls import patterns, include, url
from bulb.views import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('bulb.views',
  url(r'^idea/(?P<ideaId>\d+)/$', IdeaAPIView.as_view(), name='IdeaAPIView'),
  url(r'^idea/(?P<ideaId>\d+)/neighbours/$', NeighbourAPIView.as_view(), name='NeighbourAPIView'),
  url(r'^idea/$', IdeaCollectionAPIView.as_view(), name='idea'),
  url(r'^loginStatus/$', loginStatus, name='login'),
  url(r'^logout/$', logout, name='logout'),
  url(r'^$', interface, name='interface'),
  # Examples:
  # url(r'^$', 'bulb.views.home', name='home'),
  # url(r'^bulb/', include('bulb.foo.urls')),

  # Uncomment the admin/doc line below to enable admin documentation:
  # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

  # Uncomment the next line to enable the admin:
  # url(r'^admin/', include(admin.site.urls)),
)
