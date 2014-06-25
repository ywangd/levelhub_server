from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^register/$', 'views.register', name='register'),
    url(r'^login/$', 'views.user_login', name='login'),
    url(r'^logout/$', 'views.user_logout', name='logout'),
    url(r'^teaches/(?P<user_id>\d+)/$', 'views.teaches', name='teaches'),
    url(r'^teachregs/(?P<teach_id>\d+)/$', 'views.teach_regs', name='teach_regs'),
    url(r'^teachreglogs/(?P<reg_id>\d+)/$', 'views.teach_reg_logs', name='teach_reg_logs'),


    url(r'^debug_reset_db/$', 'views.debug_reset_db', name='debug_reset_db'),

    url(r'^admin/', include(admin.site.urls)),
)
