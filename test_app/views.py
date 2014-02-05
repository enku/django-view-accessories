from __future__ import unicode_literals

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from view_accessories import __version__
from view_accessories.detail import detail_view, template_detail_view
from view_accessories.form import form_view
from view_accessories.generic import redirect_view, template_view, view
from view_accessories.list import list_view, template_list_view

from .forms import TestForm
from .models import Widget


@view
def my_view(request, arg):
    response = HttpResponse(str(arg))
    response.content_type = 'text/plain; encoding=utf-8'
    return response


@template_view(template_name='test_app/test.html')
def my_template_view(request, arg):
    return {'arg': arg}


@redirect_view(permanent=False, query_string=True)
def my_redirect_view(request):
    return 'http://www.google.com/'


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
    pass


@list_view(model=Widget)
def my_list_view(request, widgets):
    body = json.dumps([i.text for i in widgets])
    body = body.encode('utf-8')
    response = HttpResponse(body)
    response.content_type = 'application/json; encoding=utf-8'
    return response


@list_view(Widget)
@template_view('test_app/widget_list.html')
def stacked_list_view(request, widgets):
    pass


@template_list_view(queryset=Widget.objects.order_by('-pk'), allow_empty=False,
                    paginate=5, page_size=5)
def my_template_list_view(request, widgets, pagination):
    widgets = pagination['objects']
    return {'widgets': widgets, 'desc': True}


# Test with django's decorators
login_required_view = login_required(
    login_url='/accounts/login/')(my_list_view)


@template_view(template_name='test_app/form.html')
@form_view(form=TestForm, methods=['GET', 'POST'])
def form1(request, form):
    text = ''
    if form.is_bound and form.is_valid():
        text = form.cleaned_data['text']
    return {'form': form, 'text': text}


# Triple stack
@template_view(template_name='test_app/widget_edit.html')
@detail_view(model=Widget)
@form_view(form=TestForm)
def form2(request, widget, form):
    if not form.is_bound:
        form = TestForm({'text': widget.text})
    elif form.is_valid():
        widget.text = form.cleaned_data['text']
        widget.save()
    return {'form': form, 'widget': widget}


@template_view(template_name='test_app/index.html')
def index(request):
    return {'version': __version__}
