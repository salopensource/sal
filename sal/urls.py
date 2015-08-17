from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^changepassword/$', 'django.contrib.auth.views.password_change', name='password_change'),
    url(r'^changepassword/done/$', 'django.contrib.auth.views.password_change_done', name='password_change_done'),
   	url(r'^', include('server.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    (r'^api/', include('api.urls')),
    (r'^inventory/', include('inventory.urls'))
    #url(r'^$', 'namer.views.index', name='home'),

)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if 'config' in settings.INSTALLED_APPS:
    config_pattern = patterns('',
    url(r'^config/', include('config.urls'))
    )
    urlpatterns += config_pattern
