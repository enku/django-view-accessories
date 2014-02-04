from functools import wraps

from . import accessorize
from .generic import view


def form_view(form, methods=None):
    def decorate(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                my_form = form(request.POST)
            else:
                my_form = form()
            accessorize(request, form=my_form)
            return view(func, methods=methods)(request, *args, **kwargs)
        return wrapper
    return decorate
