from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'views.home', name='home'),
    url(r'^register/$', 'views.register', name='register'),
    url(r'^login/$', 'views.user_login', name='login'),
    url(r'^logout/$', 'views.user_logout', name='logout'),

    url(r'^j/register/$', 'views.register', name='j_register'),
    url(r'^j/login/$', 'views.user_login', name='j_login'),
    url(r'^j/logout/$', 'views.user_logout', name='j_logout'),
    url(r'^j/get_teach_lessons/(?P<user_id>\d+)/$', 'views.get_teach_lessons', name='j_teach_lessons'),
    url(r'^j/get_study_lessons/$', 'views.get_study_lessons', name='j_study_lessons'),
    url(r'^j/get_user_lessons/$', 'views.get_user_lessons', name='j_user_lessons'),
    url(r'^j/get_lesson_regs/(?P<lesson_id>\d+)/$', 'views.get_lesson_regs', name='j_lesson_regs'),
    url(r'^j/get_lesson_reg_logs/(?P<reg_id>\d+)/$', 'views.get_lesson_reg_logs', name='j_lesson_reg_logs'),
    url(r'^j/user_search$', 'views.user_search', name='j_user_search'),
    url(r'^j/update_lesson/$', 'views.update_lesson', name='j_update_lesson'),
    url(r'^j/update_lesson_reg_and_logs/$', 'views.update_lesson_reg_and_logs', name='j_update_lesson_reg_and_logs'),

    url(r'^j/lesson_messages/$', 'views.lesson_messages', name='j_lesson_messages'),


    url(r'^debug_reset_db/$', 'views.debug_reset_db', name='debug_reset_db'),

    url(r'^admin/', include(admin.site.urls)),
)
