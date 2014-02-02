from __future__ import unicode_literals

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from view_accessories import __version__
from view_accessories.detail import detail_view, template_detail_view
from view_accessories.generic import redirect_view, template_view, view
from view_accessories.list import list_view, template_list_view

from .models import Widget


@view
def my_view(request, arg):
    response = HttpResponse(str(arg))
    response.content_type = 'text/plain; encoding=utf-8'
    return response


@template_view(template_name='test_app/test.html')
def my_template_view(request, arg):
    return {'arg': arg}


@redirect_view(url='http://www.google.com/', permanent=False,
               query_string=True)
def my_redirect_view(request):
    pass


@view(methods=['POST'])
def post_only(request):
    pass


@detail_view(model=Widget)
def my_detail_view(request, widget):
    response = HttpResponse(widget.text.encode('utf-8'))
    response.content_type = 'text/plain; encoding=utf-8'
    return response


@template_view(template_name='test_app/widget_detail.html')
@detail_view(model=Widget)
def detail_view_with_template(request, widget):
    return {'widget': widget}


@template_detail_view(model=Widget)
def detail_view_with_template2(request, widget):
    return {'widget': widget}


@list_view(model=Widget)
def my_list_view(request, widgets):
    body = json.dumps([i.text for i in widgets])
    body = body.encode('utf-8')
    response = HttpResponse(body)
    response.content_type = 'application/json; encoding=utf-8'
    return response


@template_view(template_name='test_app/widget_list.html')
@list_view(model=Widget)
def stacked_list_view(request, widget):
    return {'widgets': widget}


@template_list_view(queryset=Widget.objects.order_by('-pk'), allow_empty=False,
                    paginate=5, page_size=5)
def my_template_list_view(request, widgets):
    widgets = request.accessories['pagination']['objects']
    return {'widgets': widgets, 'desc': True}


# Test with django's decorators
login_required_view = login_required(
    login_url='/accounts/login/')(my_list_view)


@template_view(template_name='test_app/index.html')
def index(request):
    return {'version': __version__}
