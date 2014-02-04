"""Detail decorators.

This is analogous to Django's *django.views.detail* module.
"""
from __future__ import unicode_literals

from functools import wraps

from django.shortcuts import get_object_or_404

from . import accessorize
from .generic import template_view, view

__all__ = ('detail_view', 'template_detail_view')


def detail_view(model, methods=None):
    """A detail view.

    Note  unlike Django's  DetailView this  does not  return a  rendered
    template (see *template_detail_view* for that).

    This decorator accepts one argument, *model* which is the model name
    queried by the decorator. The decorator expects urlconf to pass
    the first positional argument as the primary key of *model*. The
    decorator will then *get_object_or_404* that model and then call the
    decorated function. The request's accessories will have an "object"
    key that references the model object that was fetched.

    A quick example::

        from .models import Book

        @detail_view(Book)
        def book_detail(request, book_id):
            book = request.accessories['object']
            return HttpResponse(book.title, content_type='text/plain')

    The urlconf would look something like this::

        (r'^book/(\d+)/', 'some_app.views.book_detail')

    In addition it accepts the *methods* argument as all view decorators.
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            obj = get_object_or_404(model, pk=args[0])
            accessorize(request, object=obj)
            return view(methods)(func)(request, *args, **kwargs)
        return wrapper
    return decorate


def template_detail_view(model, template_name=None, content_type=None,
                         template_name_suffix='_detail', methods=None):
    """A detail view that renders a template.

    This   is  probably   the   view  decorator   that   you  want.   It
    works   like   *detail_view*   but  expects   the   decorated   view
    to   return   a  context   dictionary   which   will  be   used   to
    render   and  return   a  template.   The  default   *template_name*
    is   computed  dynamically   based  on   the  app   &  model   names
    (just   as   Django's).  For   example,   **some_app.models.Book**'s
    default *template_name*  would be  **some_app/book_detail.html**. If
    *template_name_suffix* is  passed instead, it will  default to, e.g.
    **some_app/book_customsuffix.html**.

    The   *model*   argument   is   the  same   as   in   *detail_view*.
    The   *content_type*   argument   is   self-explanatory   (same   as
    *generic.template_view*).

    In  addition  it   accepts  the  *methods*  argument   as  all  view
    decorators.
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            obj = get_object_or_404(model, pk=args[0])
            accessorize(request, object=obj)

            my_template_name = template_name
            if not my_template_name:
                my_template_name = '%s/%s%s.html' % (
                    obj._meta.app_label,
                    obj._meta.model_name,
                    template_name_suffix)

            return template_view(
                template_name=my_template_name,
                content_type=content_type,
                methods=methods)(func)(request, *args, **kwargs)
        return wrapper
    return decorate
