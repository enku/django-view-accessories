from __future__ import unicode_literals

from functools import wraps

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.translation import ugettext as _

from .generic import template_view, view
from . import accessorize


__all__ = ('list_view', 'template_list_view', 'paginate_queryset')


def list_view(model=None, queryset=None, paginate=False, page_size='page_size',
              paginate_orphans=0, page_kwarg='page', allow_empty=True,
              methods=None):
    """A list view.

    Note  unlike  Django's ListView  this  does  not return  a  rendered
    template (see *template_list_view* for that).

    This decorator requires either *model*  or *queryset* (but not both)
    to be passed  to it. The decorated view function  will be passed the
    queryset as it's second  positional argument (behind the HttpRequest
    object).

    If *allow_empty*  is False and the  queryset to be passed  is empty,
    then the decorator, instead of  calling the decorated function, will
    raise an EmptyPage exception.

    Pagination
    ----------
    This decorator supports pagination using Django's built-in Paginator
    class. If  *paginate* is True,  then the request object  passed into
    the  decorated function  will  be "accessorized"  with a  pagination
    attribute.  This attribute  is  a Python  dictionary with  following
    key/value pairs:

        "paginator": The actual Paginator object.
        "page": The paginator page for this request,
        "objects": The actual list of objects for this request,
        "has_other_pages": True if the queryset has more than one page.

    If *paginate* is  True, then *page_size* is the  (maximum) number of
    objects per page. If this parameter is passed as a string (as in the
    default),  then  the  page  size  is  instead  determined  from  the
    request's query string, i.e.::

        page_size = int(request.GET[page_size])

    This is to allow the page size to be determined dynamically from the
    request.

    *paginate_orphans* is the minimum number of orphans to allow on the.
    last page See Django's Pagination documentation for details        .

    *page_kwarg* is the GET paremeter used to determine the page number.
    For example if the request is "/?page=2" and page_kwargs="page" then
    the  "page" will  be the  second page.  The default  *page_kwarg* is
    "page".

    In  addition  it   accepts  the  *methods*  argument   as  all  view
    decorators.

    A quick example::

        @list_view(model=Widget, paginate=True, page_size=5)
        def my_view(request, widgets):
            page_widgets = request.accessories['pagination']['objects']
            response = http.HttpResponse(json.dumps(page_widgets))
            response.content_type = 'application/json'
            return response
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            qs = _get_qs_or_404(model, queryset, allow_empty)

            if paginate:
                paginate_queryset(
                    request,
                    qs,
                    page_kwarg,
                    page_size,
                    orphans=paginate_orphans,
                    allow_empty_first_page=allow_empty
                )

            return view(methods)(func)(request, qs, *args, **kwargs)
        return wrapper
    return decorate


def template_list_view(model=None, queryset=None, allow_empty=True,
                       template_name=None, paginate=False,
                       page_size='page_size', paginate_orphans=0,
                       page_kwarg='page', content_type=None,
                       template_name_suffix='_list', methods=None):
    """A list_view that renders a template.

    This   is  probably   the   view  decorator   that   you  want.   It
    works   like   *list_view*   but  expects   the   decorated   view
    to   return   a  context   dictionary   which   will  be   used   to
    render   and  return   a  template.   The  default   *template_name*
    is   computed  dynamically   based  on   the  app   &  model   names
    (just   as   Django's).  For   example,   **some_app.models.Book**'s
    default *template_name*  would be  **some_app/book_list.html**. If
    *template_name_suffix* is  passed instead, it will  default to, e.g.
    **some_app/book_customsuffix.html**.

    The *model* and *queryset* arguments are the same as in *list_view*.
    as  are the  pagination  arguments. The  *content_type* argument  is
    self-explanatory (same as *generic.template_view*).

    In  addition  it   accepts  the  *methods*  argument   as  all  view
    decorators.

    A quick example::

        @template_list_view(model=Widget, paginate=True, page_size=5)
        def my_view(request, widgets):
            pagination = request.accessories['pagination']
            return {'widgets': pagination['objects'],
                    'total': widgets.count(),
                    'page': paginaton['page']
                    'next_page': pagination['page'].has_next()}
    """
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            qs = _get_qs_or_404(model, queryset, allow_empty)

            if paginate:
                paginate_queryset(
                    request,
                    qs,
                    page_kwarg,
                    page_size,
                    orphans=paginate_orphans,
                    allow_empty_first_page=allow_empty
                )

            my_template_name = template_name
            if not my_template_name:
                my_template_name = '%s/%s%s.html' % (
                    qs.model._meta.app_label,
                    qs.model._meta.model_name,
                    template_name_suffix)

            return template_view(
                template_name=my_template_name,
                content_type=content_type,
                methods=methods)(func)(request, qs, *args, **kwargs)

        return wrapper
    return decorate


def paginate_queryset(request, queryset, page_kwarg, per_page, orphans=0,
                      allow_empty_first_page=True, **kwargs):
    """Accessorize a list_view queryset with pagination.

    This function is used by *list_view* and *template_list_view* but is
    exposed because  it can also  be used on  its own or  by third-party
    view decorators.

    The *request*  will be  "accessorized" with a  pagination attribute.
    This  attribute  is a  Python  dictionary  with following  key/value
    pairs:

        "paginator": The actual Paginator object.
        "page": The paginator page for this request,
        "objects": The actual list of objects for this request,
        "has_other_pages": True if the queryset has more than one page.

    *per_page*  is the  (maximum) number  of objects  per page.  If this
    parameter  is passed  as  a string  then the  page  size is  instead
    determined from the request's query string, i.e.::

        per_page = int(request.GET[per_page])

    This is to allow the page size to be determined dynamically from the
    request.

    *orphans* is  the minimum number  of orphans  to allow on  the last.
    page See Django's Pagination documentation for details             .

    *page_kwarg* is the GET paremeter used to determine the page number.
    For example if the request is "/?page=2" and page_kwargs="page" then
    the  "page" will  be the  second page.  The default  *page_kwarg* is
    "page".

    If *allow_empty_first_page*  and the first  page is empty  then this
    function  will instead  raise  an Http404  exception,  else it  will
    return an empty first page.

    *kwargs* are additional  keyword arguments to pass  to the Paginator
    on instantiation.
    """
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = int(request.GET[per_page])

    paginator = Paginator(queryset, per_page, orphans=orphans,
                          allow_empty_first_page=allow_empty_first_page,
                          **kwargs)
    page = request.GET.get(page_kwarg, 1)

    try:
        page_number = int(page)
    except ValueError:
        if page == 'last':
            page_number = paginator.num_pages
        else:
            raise Http404(
                _("Page is not 'last', nor can it be converted to an int."))

    try:
        page = paginator.page(page_number)
        accessorize(request, pagination={
            'paginator': paginator,
            'page': page,
            'objects': page.object_list,
            'has_other_pages': page.has_other_pages(),
        })
    except InvalidPage as exception:
        raise Http404(
            _('Invalid page %s: %s' % (page_number, str(exception))))


def _get_qs_or_404(model, queryset, allow_empty):
    if model:
        qs = model._default_manager.all()
    elif queryset:
        qs = queryset
    else:
        raise ImproperlyConfigured("Must define 'queryset' or 'model'")

    if hasattr(qs, '_clone'):
        qs = qs._clone()

    if not (allow_empty or qs.exists()):
        raise Http404('Empty list')

    return qs
