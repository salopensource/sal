from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
admin.autodiscover()
import django.contrib.auth.views as auth_views
from django.contrib.staticfiles import views


urlpatterns = [
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^login$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout_then_login, name='logout_then_login'),
    url(
        r'^changepassword/$', auth_views.password_change,
        name='password_change'),
    url(
        r'^changepassword/done/$', auth_views.password_change_done,
        name='password_change_done'),
    path('', include('server.urls')),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'admin/', admin.site.urls),
    url(r'^api/', include('api.urls')),
    url(r'^inventory/', include('inventory.urls')),
    url(r'^search/', include('search.urls')),
    path('licenses/', include('licenses.urls')),
    path('catalog/', include('catalog.urls')),

]

if settings.DEBUG:
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', views.serve),
    ]
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
