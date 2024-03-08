"""
URL configuration for mizdb-watchlist demo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from mizdb_watchlist.views import AdminWatchlistView

urlpatterns = [
    # TODO: mention in docs that you need to add this path before admin.site.urls:
    path("admin/watchlist/", AdminWatchlistView.as_view(), name="admin_watchlist"),
    path("admin/", admin.site.urls),
    path("mizdb_watchlist/", include("mizdb_watchlist.urls")),
    path("", include("app.urls")),
    # path("accounts/", include("django.contrib.auth.urls")),
]
