from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^register/', 'views.register', name='register'),
    url(r'^login/', 'views.user_login', name='login'),
    url(r'^logout/', 'views.user_logout', name='logout'),

    url(r'^admin/', include(admin.site.urls)),
)
