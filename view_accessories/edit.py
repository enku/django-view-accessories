"""View decorators for Django View Accessories"""
from functools import wraps

from django.forms import models as model_forms
from django.shortcuts import redirect
from .generic import template_view, view


def form_view(form=None, success_url=None, methods=None):
    """A form view.

    This decorator  takes one required  argument, *form* which  shall be
    the  Django form  class to  instantiate.  If the  decorated view  is
    called  with the  POST method,  then the  given form  class will  be
    instantiated  (bound) with  the  request's POST  dictionary. If  the
    request is not a POST, then an empty (unbound) form is instantiated.
    Either  way, the  decorated view  is  then called  with the  keyword
    argument "form" which will equal the instantiated form.

    If *success_url* is passed and the request is POSTed with valid form
    data, then the  view is executed, but the response  is redirected to
    *success_url*.

    A quick example::

        from .forms import EntryForm

        @form_view(EntryForm)
        @template_view('some_app/entry_form.html')
        def entry_view(request, form):
            if form.is_bound and form.is_valid():
                process_data(form.cleaned_data)
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                my_form = form(request.POST)
            else:
                my_form = form()

            assert 'form' not in kwargs
            kwargs['form'] = my_form

            if request.method == 'POST':
                valid = my_form.is_valid()
                if valid and hasattr(form, 'save'):
                    my_form.save()

                response = view(func, methods=methods)(request, *args,
                                                       **kwargs)
                if success_url and valid:
                    return redirect(success_url)
                return response
            return view(func, methods=methods)(request, *args, **kwargs)
        return wrapper
    return decorate


def create_view(model, fields, success_url=None, methods=None):
    """A form_view for Models.

    This view  decorator works  much like  the *form_view*,  except that
    instead of taking  a form as an argument, it  tiaks a django *model*
    The decorator  then dynamically  creates a form  based on  the model
    using the  fields specified  in *fields*. After  that the  view acts
    pretty much like a *form_view*, except that in addition, if the form
    is POSTed  and is valid, then  the mode is saved  before calling the
    decorated view function.

    *success_url* works just as in *form_view*.

    A quick example::

        @create_view(model=Widget, fields=['text'], success_url='/')
        @template_view(template_name='test_app/widget_create.html')
        def create_widget(request, form):
            pass

    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            form_cls = model_forms.modelform_factory(model, fields=fields)

            return form_view(form=form_cls, success_url=success_url,
                             methods=methods)(func)(request, *args, **kwargs)
        return wrapper
    return decorate


def template_create_view(model, fields, template_name=None, content_type=None,
                         template_name_suffix='_create', success_url=None,
                         methods=None):
    """A create_view that renders a template.

    This is  a creat_view decorated with  a template view. It  takes the
    same arguments as `template_view` and `create_view`. By default, the
    *template_name*  is  taken  from  the  model  name  with  "_created"
    added (though  that can  be changed with  the *template_name_suffix*
    argument. A quick example::

        @template_create_view(model=Widget, success_url='/')
        def create_form(request, form):
            pass
    """
    def decorate(func):
        def wrapper(request, *args, **kwargs):
            my_template_name = template_name
            if not my_template_name:
                my_template_name = '%s/%s%s.html' % (
                    model._meta.app_label,
                    model._meta.model_name,
                    template_name_suffix)
            myview = template_view(my_template_name, content_type=content_type,
                                   methods=methods)(func)
            myview = create_view(model, fields, success_url=success_url,
                                 methods=methods)(myview)
            return myview(request, *args, **kwargs)
        return wrapper
    return decorate
