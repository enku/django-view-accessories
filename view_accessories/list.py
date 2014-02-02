from __future__ import unicode_literals

from functools import wraps

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404

from .generic import template_view, view

__all__ = ('list_view', 'template_list_view')


# TODO: Pagination
def list_view(model=None, queryset=None, allow_empty=True, methods=None):
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            qs = _get_qs_or_404(model, queryset, allow_empty)

            return view(methods)(func)(request, qs, *args, **kwargs)
        return wrapper
    return decorate


def template_list_view(model=None, queryset=None, allow_empty=True,
                       template_name=None, content_type=None,
                       template_name_suffix='_list', methods=None):
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            qs = _get_qs_or_404(model, queryset, allow_empty)

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
