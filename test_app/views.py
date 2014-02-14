from __future__ import unicode_literals

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from view_accessories import __version__
from view_accessories import detail
from view_accessories import edit
from view_accessories import generic
from view_accessories import list as lists

from .forms import TestForm
from .models import Widget


@generic.view
def my_view(request, arg):
    response = HttpResponse(str(arg))
    response.content_type = 'text/plain; encoding=utf-8'
    return response


@generic.template_view
def my_template_view(request):
    widget = Widget.objects.order_by('?')[0]
    return {'widget': widget}


@generic.redirect_view(permanent=False, query_string=True)
def my_redirect_view(request):
    return 'http://www.google.com/'


@generic.view(methods=['POST'])
def post_only(request):
    pass


@detail.detail_view(model=Widget)
def my_detail_view(request, widget):
    response = HttpResponse(widget.text.encode('utf-8'))
    response.content_type = 'text/plain; encoding=utf-8'
    return response


@generic.template_view(template_name='test_app/widget_detail.html')
@detail.detail_view(model=Widget)
def detail_view_with_template(request, widget):
    return {'widget': widget}


@detail.template_detail_view(model=Widget)
def detail_view_with_template2(request, widget):
    pass


@lists.list_view(model=Widget)
def my_list_view(request, widgets):
    body = json.dumps([i.text for i in widgets])
    body = body.encode('utf-8')
    response = HttpResponse(body)
    response.content_type = 'application/json; encoding=utf-8'
    return response


@lists.list_view(Widget)
@generic.template_view(template_name='test_app/widget_list.html')
def stacked_list_view(request, widgets):
    pass


@lists.template_list_view(queryset=Widget.objects.order_by('-pk'),
                          allow_empty=False, paginate=True, page_size=5)
def my_template_list_view(request, widgets, pagination):
    widgets = pagination['objects']
    return {'widgets': widgets, 'desc': True}


# Test with django's decorators
login_required_view = login_required(
    login_url='/accounts/login/')(my_list_view)


@generic.template_view(template_name='test_app/form.html')
@edit.form_view(form=TestForm, methods=['GET', 'POST'])
def form1(request, form):
    text = ''
    if form.is_bound and form.is_valid():
        text = form.cleaned_data['text']
    return {'form': form, 'text': text}


# Triple stack
@edit.form_view(form=TestForm)
@generic.template_view(template_name='test_app/widget_edit.html')
@detail.detail_view(model=Widget)
def form2(request, widget, form):
    if not form.is_bound:
        form = TestForm({'text': widget.text})
    elif form.is_valid():
        widget.text = form.cleaned_data['text']
        widget.save()
    return {'form': form, 'widget': widget}


@edit.create_view(model=Widget, fields=['text'], success_url='/')
@generic.template_view(template_name='test_app/widget_create_form.html')
def create_form(request, form):
    pass


@edit.template_create_view(model=Widget, fields=['text'], success_url='/')
def create_template(request, form):
    pass


@edit.update_view(model=Widget, success_url='/')
@generic.template_view(template_name='test_app/widget_update_form.html')
def update1(request, widget, form):
    pass


@edit.template_update_view(model=Widget, success_url='/')
def update2(request, widget, form):
    pass


@edit.delete_view(model=Widget, success_url='/')
@generic.template_view(template_name='test_app/widget_confirm_delete.html')
def delete1(request, widget):
    pass


@edit.template_delete_view(model=Widget, success_url='/')
def delete2(request, widget):
    pass


@generic.template_view(template_name='test_app/index.html')
def index(request):
    widget = Widget.objects.order_by('?')[0]
    return {'version': __version__, 'widget': widget}
