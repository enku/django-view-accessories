"""View decorators for Django View Accessories"""
from functools import wraps

from django.forms import models as model_forms
from django.shortcuts import get_object_or_404, redirect
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
                         template_name_suffix='_create_form', success_url=None,
                         methods=None):
    """A create_view that renders a template.

    This is a  create_view decorated with a template view.  It takes the
    same arguments as `template_view` and `create_view`. By default, the
    *template_name*  is taken  from the  model name  with "_create_form"
    added (though  that can  be changed with  the *template_name_suffix*
    argument. A quick example::

        @template_create_view(model=Widget, success_url='/')
        def create_form(request, form):
            pass
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            my_template_name = template_name
            if not my_template_name:
                my_template_name = '%s/%s%s.html' % (
                    model._meta.app_label,
                    model._meta.model_name,
                    template_name_suffix)
            myview = template_view(template_name=my_template_name,
                                   content_type=content_type,
                                   methods=methods)(func)
            myview = create_view(model, fields, success_url=success_url,
                                 methods=methods)(myview)
            return myview(request, *args, **kwargs)
        return wrapper
    return decorate


def update_view(model, field='pk', kwarg='id', fields=None, success_url=None,
                methods=None):
    """A view to update a model.

    This decorator is a cross between a detail view and a form view. The
    decorator is passed and argument  *model* and, like the detail_view,
    is expected to  be called via the urlconf with  the keyword argument
    "id" to  the view,  though this  can be  overriden with  the *kwarg*
    parameter.  The decorator  will then  *get_object_or_404* that  that
    *model* to get the model  instance, then a ModelForm is instantiated
    from  that  model instance.  When  the  view  is POSTed,  the  model
    instance  is  saved.  Like  other  edit views,  this  view  takes  a
    *success_url*  and, if  passed and  the  POST's form  is valid,  the
    response will be an HTTP redirect to the given url.

    The decorated  view will  be passed 2  keyword arguments:  the first
    would be the model name (lowercased and underscored), and it's value
    will be  the model instance,  the second keyword argument  is "form"
    and will be the ModelForm instance.

    If  *field* is  specified, then  the model  will be  queried by  the
    specified field instead of the default primary key.

    A quick example::

        @update_view(model=Widget, success_url='/')
        @template_view(template_name='some_app/widget_update_form.html')
        def edit_widget(request, widget, form):
            pass

    And in urls.py::

        (r'^widget/(?P<id>\d+)/', 'some_app.views.edit_widget')

    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            lookup = kwargs.pop(kwarg)
            obj = get_object_or_404(model, **{field: lookup})
            obj_name = obj._meta.model_name
            form_cls = model_forms.modelform_factory(model, fields=fields)
            if request.method == 'POST':
                form = form_cls(request.POST, instance=obj)
                if form.is_valid():
                    form.save()
                    obj = form.instance
            else:
                form = form_cls(instance=obj)

            kwargs['form'] = form
            kwargs[obj_name] = obj

            response = view(methods=methods)(func)(request, *args, **kwargs)
            if request.method == 'POST' and success_url and form.is_valid():
                return redirect(success_url)
            return response
        return wrapper
    return decorate


def template_update_view(model, field='pk', kwarg='id', fields=None,
                         template_name=None, content_type=None,
                         template_name_suffix='_update_form', success_url=None,
                         methods=None):
    """An update_view that renders a template.

    This is an update_view decorated with  a template view. It takes the
    same arguments as `template_view` and `update_view`. By default, the
    *template_name*  is taken  from the  model name  with "_update_form"
    added (though  that can  be changed with  the *template_name_suffix*
    argument. A quick example::

        @template_update_view(model=Widget, success_url='/')
        def create_form(request, widget, form):
            pass
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            my_template_name = template_name
            if not my_template_name:
                my_template_name = '%s/%s%s.html' % (
                    model._meta.app_label,
                    model._meta.model_name,
                    template_name_suffix)
            myview = template_view(template_name=my_template_name,
                                   content_type=content_type,
                                   methods=methods)(func)
            myview = update_view(model=model, field=field, kwarg=kwarg,
                                 fields=fields, success_url=success_url,
                                 methods=methods)(myview)
            return myview(request, *args, **kwargs)
        return wrapper
    return decorate


def delete_view(model, field='pk', kwarg='id', success_url=None, methods=None):
    """A view to delete a model.

    The  delete_view is  like the  detail_view,  except if  the view  is
    POSTed to  then the model instance  in question is deleted,  and the
    response is an HTTP redirect if *success_url* is passed.

    This decorator  requires one  argument, *model*  which is  the model
    name  queried by  the decorator.  The decorator  expects urlconf  to
    pass  the keyword  argument "id"  to the  view, though  this can  be
    overriden  with  the  *kwarg*  parameter. The  decorator  will  then
    *get_object_or_404* that  that *model*  and then call  the decorated
    function  with an  keyword  argument  whose key  is  the model  name
    (lowercase) and whose value will be the object retrieved.

    If  *field* is  specified, then  the model  will be  queried by  the
    specified field instead of the default primary key.

    If the view is POSTed to,  then the model is deleted. Upon deletion,
    if the  *success_url* is passed, then  the HTTP response will  be an
    HTTP redirect  to the  success_url instead  of the  decorated view's
    response.

    A quick example::

        @delete_view(model=Widget, success_url='/')
        @template_view(template_name='some_app/widget_confirm_delete.html')
        def delete_widget(request, widget):
            pass
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            lookup = kwargs.pop(kwarg)
            obj = get_object_or_404(model, **{field: lookup})
            obj_name = obj._meta.model_name
            kwargs[obj_name] = obj

            response = view(methods=methods)(func)(request, *args, **kwargs)

            if request.method == 'POST':
                # confirmed.  Delete
                obj.delete()
                if success_url:
                    return redirect(success_url)
            return response
        return wrapper
    return decorate


def template_delete_view(model, field='pk', kwarg='id', template_name=None,
                         content_type=None,
                         template_name_suffix='_confirm_delete',
                         success_url=None, methods=None):
    """An delete_view that renders a template.

    This is an delete_view decorated with  a template view. It takes the
    same arguments as `template_view` and `delete_view`. By default, the
    *template_name* is taken from  the model name with "_confirm_delete"
    added (though  that can  be changed with  the *template_name_suffix*
    argument.

    A quick example::

        @template_delete_view(model=Widget, success_url='/')
        def delete_widget(request, widget):
            pass
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            my_template_name = template_name
            if not my_template_name:
                my_template_name = '%s/%s%s.html' % (
                    model._meta.app_label,
                    model._meta.model_name,
                    template_name_suffix)
            myview = template_view(template_name=my_template_name,
                                   content_type=content_type,
                                   methods=methods)(func)
            myview = delete_view(model=model, field=field, kwarg=kwarg,
                                 success_url=success_url,
                                 methods=methods)(myview)
            return myview(request, *args, **kwargs)
        return wrapper
    return decorate
