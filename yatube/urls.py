"""yatube URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib.flatpages import views
from django.conf.urls import handler404, handler500
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from django.views.static import serve

import django.urls

handler404 = "posts.views.page_not_found" # noqa
handler500 = "posts.views.server_error" # noqa

urlpatterns = [
    django.urls.path('auth/', django.urls.include('users.urls')),
    django.urls.path('auth/',
                     django.urls.include('django.contrib.auth.urls')
                     ),
    django.urls.path('admin/', admin.site.urls),
    django.urls.path('about/',
                     django.urls.include('django.contrib.flatpages.urls')
                     ),
    django.urls.path('', django.urls.include('posts.urls')),
    ]

urlpatterns += [
        django.urls.path('about-us/', views.flatpage,
                         {'url': '/about-us/'}, name='about'
                         ),
        django.urls.path('terms/', views.flatpage,
                         {'url': '/terms/'}, name='terms'
                         ),
        django.urls.path('about-author/', views.flatpage,
                         {'url': '/about-author/'}, name='developer'
                         ),
        django.urls.path('about-spec/', views.flatpage,
                         {'url': '/about-spec/'}, name='spec'
                         ),

]

urlpatterns += [
    django.urls.path('captcha/', django.urls.include('captcha.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    urlpatterns += (
        django.urls.path("__debug__/",
        django.urls.include(debug_toolbar.urls)),
    )

if not settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT}),
        url(r'^static/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT}),
    ]