from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', 'views.home', name='home'),
    url(r'^register/$', 'views.register', name='register'),
    url(r'^login/$', 'views.user_login', name='login'),
    url(r'^logout/$', 'views.user_logout', name='logout'),

    url(r'^j/register/$', 'views.register', name='j_register'),
    url(r'^j/login/$', 'views.user_login', name='j_login'),
    url(r'^j/logout/$', 'views.user_logout', name='j_logout'),
    url(r'^j/process_lessons/$', 'views.process_lessons', name='j_process_lessons'),
    url(r'^j/process_lesson_requests/$', 'views.process_lesson_requests', name='j_process_lesson_requests'),
    url(r'^j/process_lesson_regs/$', 'views.process_lesson_regs', name='j_process_lesson_regs'),
    url(r'^j/process_lesson_reg_logs/$', 'views.process_lesson_reg_logs', name='j_process_lesson_reg_logs'),
    url(r'^j/process_lesson_messages/$', 'views.process_lesson_messages', name='j_process_lesson_messages'),

    url(r'^j/user_search$', 'views.user_search', name='j_user_search'),
    url(r'^j/lesson_search$', 'views.lesson_search', name='j_lesson_search'),


    url(r'^debug_reset_db/$', 'views.debug_reset_db', name='debug_reset_db'),

    url(r'^admin/', include(admin.site.urls)),
)
