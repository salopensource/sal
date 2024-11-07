import django.contrib.auth.views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles import views
from django.urls import path, include, re_path

admin.autodiscover()
urlpatterns = []
urlpatterns += [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.logout_then_login, name="logout_then_login"),
    path(
        "changepassword/",
        auth_views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "changepassword/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("", include("server.urls")),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("api.v1.urls")),
    path("api/v1/", include("api.v1.urls")),
    path("api/v2/", include("api.v2.urls")),
    path("inventory/", include("inventory.urls")),
    path("search/", include("search.urls")),
    path("licenses/", include("licenses.urls")),
    path("catalog/", include("catalog.urls")),
    path("profiles/", include("profiles.urls")),
    path("healthcheck/", include("health_check.urls")),
]

if settings.DEBUG:
    urlpatterns.append(path("static/<path>", views.serve))

if settings.USE_SAML:
    urlpatterns += [
        re_path(r"^saml2/", include("djangosaml2.urls")),
    ]
