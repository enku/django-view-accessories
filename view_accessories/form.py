from functools import wraps

from .generic import view


def form_view(form, methods=None):
    """A form view.

    This decorator  takes one required  argument, *form* which  shall be
    the  Django form  class to  instantiate.  If the  decorated view  is
    called  with the  POST method,  then the  given form  class will  be
    instantiated  (bound) with  the  request's POST  dictionary. If  the
    request is not a POST, then an empty (unbound) form is instantiated.
    Either  way, the  decorated view  is  then called  with the  keyword
    argument "form" which will equal the instantiated form.

    A quick example::

        from .forms import EntryForm

        @template_view('some_app/entry_form.html')
        @form_view(EntryForm)
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
            kwargs['form'] = my_form
            return view(func, methods=methods)(request, *args, **kwargs)
        return wrapper
    return decorate
