from __future__ import unicode_literals

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'test_app.views',
    url('^my_view/(.+)/$', 'my_view'),
    url('^my_template_view/$', 'my_template_view'),
    url('^redirect/$', 'my_redirect_view'),
    url('^post/$', 'post_only'),
    url('^widget/(?P<id>\d+)/$', 'my_detail_view'),
    url('^widget2/(?P<id>\d+)/$', 'detail_view_with_template'),
    url('^widget3/(?P<id>\d+)/$', 'detail_view_with_template2'),
    url('^widgets1/$', 'my_list_view'),
    url('^widgets2/$', 'stacked_list_view'),
    url('^widgets3/$', 'my_template_list_view'),
    url('^widgets4/$', 'login_required_view'),
    url('^form1/$', 'form1'),
    url('^form2/(?P<id>\d+)/$', 'form2'),
    url('^create1/$', 'create_form'),
    url('^create2/$', 'create_template'),
    url('^update1/(?P<id>\d+)/$', 'update1'),
    url('^update2/(?P<id>\d+)/$', 'update2'),
    url('^delete1/(?P<id>\d+)/$', 'delete1'),
    url('^delete2/(?P<id>\d+)/$', 'delete2'),
    url('^$', 'index'),
)
