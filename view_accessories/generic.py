"""This is analogous to Django's django.views.generic.

It  defines   the  "base"   *view*  as   well  as   *template_view*  and
*redirect_view*.

django-view-accessories'  "views" are  just  function  decorators. As  a
consumer you write one view function and decorate it with a "view".
"""
from __future__ import unicode_literals

from functools import wraps

from django import http
from django.shortcuts import render

from . import accessorize

HTTP_METHODS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS',
                'TRACE')

__all__ = ('view', 'template_view', 'redirect_view', 'HTTP_METHODS')


def view(func=None, methods=None):
    """Generic view decorator.

    This is  the base decorator  (think base  class for OOO).  All other
    view  decorators should  call this  one.  Currently all  it does  is
    accept the  *methods* argument, which should  be a list or  tuple of
    the  HTTP methods  allowed by  the decorated  view. If  the view  is
    called using  a method  not allowed  in *methods*  then an  HTTP 405
    (method now allowed) is returned to the client.

    Some decorators in this package may modify the request object passed
    to the decorated view. When doing  so they are said to "accessorize"
    the  request.  decorated  views'   requests  have  an  "accessories"
    atribute, which is a dictionary.

    For example, views that are decorated with the *list_view* decorator
    and  have pagination  enabled will  have a  request object  that has
    pagination data. This data is accessed like the following::

        pagination = request.accessories['pagination']

    When used  on its  own this *view()*  decorator merely  createds the
    .accessories attribute with an empty dictionary.
    """
    methods = methods or HTTP_METHODS

    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Make sure we have an .accessories attribute
            accessorize(request)

            if request.method == 'OPTIONS':
                return options(request, methods)

            if request.method not in methods:
                return http.HttpResponseNotAllowed(methods)

            return func(request, *args, **kwargs)
        return wrapper

    if func:
        return decorate(func)
    return decorate


def template_view(template_name, content_type=None, methods=None):
    """Template view decorator.

    This is  analogous to Django's  TemplateView. It takes  2 arguments:
    *template_name* (required)  is the  path name  to the  template. The
    optional *content_type* is just as it sounds.

    In  addition  it   accepts  the  *methods*  argument   as  all  view
    decorators.

    The decorated  function shall return  a context dictionary  which is
    used to render the template. A quick example::

        @template_view(template_name='some_app/version.html')
        def version(request):
            return {'version': 2.0}

    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            response = view(methods)(func)(request, *args, **kwargs)
            return render(request, template_name, response,
                          content_type=content_type)
        return wrapper
    return decorate


def redirect_view(func=None, permanent=True, query_string=False, methods=None):
    """Redirect view decorator.

    This is analogous to Django's RedirectView, but instead the url to
    redirect to is expected to be returned by the decorated view. If the
    view returns an empty string (or None or False) the decorator will
    return the HTTP GONE status to the client.

    The two  optional arguments are  *permanent* which defaults  to True
    and *query_string*  which, if True  takes the QUERY_STRING  from the
    request and appends it to the redirect *url*.

    In  addition  it   accepts  the  *methods*  argument   as  all  view
    decorators.

    The simple example::

        @redirect_view
        def someothersite(request):
            return 'http://someothersite.com/'

    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            url = func(request, *args, **kwargs)
            if not url:
                return http.HttpResponseGone()

            proper_url = url
            if query_string:
                proper_url = '%s?%s' % (url,
                                        request.META.get('QUERY_STRING', ''))

            if permanent:
                return http.HttpResponsePermanentRedirect(proper_url)
            return http.HttpResponseRedirect(proper_url)
        return wrapper

    if func:
        return decorate(func)
    return decorate


def options(request, methods):
    """Return an HttpResponse of methods allowed."""
    response = http.HttpResponse()
    response['Allow'] = ', '.join(methods)
    response['Content-Length'] = '0'
    return response
