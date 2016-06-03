from django.conf.urls import url

import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^index$', views.index),
    url(r'^(?P<suite_uuid>(\w|\-)+)/?$', views.redirect_to_welcome),
    url(r'^(?P<suite_uuid>(\w|\-)+)/welcome$', views.welcome),
    url(r'^(?P<suite_uuid>(\w|\-)+)/wechat/callback$', views.wechat_oath_callback),
    url(r'^(?P<suite_uuid>(\w|\-)+)/intro$', views.intro),
    # url(r'^(?P<suite_uuid>(\w|\-)+)/presentation', views.presentation),
    url(r'^(?P<suite_uuid>(\w|\-)+)/presentation', views.presentation_and_vote),
    url(r'^(?P<suite_uuid>(\w|\-)+)/vote$', views.vote),
    url(r'^(?P<suite_uuid>(\w|\-)+)/user-info', views.submit_user_info),
    url(r'^(?P<suite_uuid>(\w|\-)+)/thx$', views.thx),
    url(r'^(?P<suite_uuid>(\w|\-)+)/get-execution$', views.get_execution),
    url(r'^(?P<suite_uuid>(\w|\-)+)/error$', views.error),
    url(r'^(?P<suite_uuid>(\w|\-)+)/suite-end$', views.suite_end),
    url(r'^(?P<suite_uuid>(\w|\-)+)/has-been-finished', views.has_been_finished),
    url(r'^(?P<suite_uuid>(\w|\-)+)/debug$', views.debug),
]
