import django.contrib.auth.views as auth_views
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles import views

admin.autodiscover()

urlpatterns = [
    url(r'^login/*$', auth_views.LoginView, name='login'),
    url(r'^logout/$', auth_views.logout_then_login, name='logout_then_login'),
    url(r'^changepassword/$', auth_views.PasswordChangeView, name='password_change'),
    url(r'^changepassword/done/$', auth_views.PasswordChangeDoneView, name='password_change_done'),
    url(r'^', include('server.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('api.v1.urls')),
    url(r'^api/v1/', include('api.v1.urls')),
    url(r'^api/v2/', include('api.v2.urls')),
    url(r'^inventory/', include('inventory.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^licenses/', include('licenses.urls')),
    url(r'^catalog/', include('catalog.urls')),
    url(r'^profiles/', include('profiles.urls')),
]

if settings.DEBUG:
    urlpatterns += [url(r'^static/(?P<path>.*)$', views.serve),]
