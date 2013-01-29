from django.conf.urls import patterns, include, url
from bulb.views import IdeaAPIView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('bulb.views',
  url(r'^idea/(?P<ideaId>\d+)/$', IdeaAPIView.as_view(), name='idea')
  # Examples:
  # url(r'^$', 'bulb.views.home', name='home'),
  # url(r'^bulb/', include('bulb.foo.urls')),

  # Uncomment the admin/doc line below to enable admin documentation:
  # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

  # Uncomment the next line to enable the admin:
  # url(r'^admin/', include(admin.site.urls)),
)
