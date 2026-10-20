from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from website.sitemaps import StaticViewSitemap


# ---------------------------------------------------------------------
# Sitemap
# ---------------------------------------------------------------------

sitemaps = {
    "static": StaticViewSitemap,
}


# ---------------------------------------------------------------------
# URL routes
# ---------------------------------------------------------------------

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),

    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt",
            content_type="text/plain",
        ),
        name="robots_txt",
    ),

    path("", include("website.urls")),
]


# ---------------------------------------------------------------------
# Media files (development only)
# ---------------------------------------------------------------------

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )