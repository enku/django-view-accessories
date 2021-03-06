=======================
django-view-accessories
=======================

Author: Albert Hopkins <marduk@python.net>

Django View Accessories is an alternative to Django's Class-based views.
Instead of creating views by subclassing classes, one simply creates
views by applying decorators to functions.

Examples
--------

From Django's documentation, creating a TemplateView using CBVs looks
like this::

    # some_app/views.py
    from django.views.generic import TemplateView

    class AboutView(TemplateView):
        template_name = "about.html"


Then setting up the urlconf::

    # urls.py
    from django.conf.urls import patterns
    from some_app.views import AboutView

    urlpatterns = patterns('',
        (r'^about/', AboutView.as_view()),
    )


With django-view-accessories, this is the equivalent::

    # some_app/views.py
    from view_accessories.generic import template_view

    @template_view(template_name="about.html")
    def about_view(request):
        pass


Then setting up the urlconf::

    # urls.py
    from django.conf.urls import patterns
    urlpatterns = patterns('some_app.views',
        (r'^about/', 'about_view'),
    )


You can already perform something similar to the above with Django's
classic views, but for other things, like ListViews and DetailViews you
have to either write a lot of boiler plate or use class-based-views,
which is still a lot of bioler plate. However consider the following::

    # some_app/views.py
    from view_accessories.detail import detail_view
    
    from .models import Book

    @detail_view(model=Book)
    def book_detail(request, book):
        response = HttpResponse(book.title.encode('utf-8'))
        response.content_type = 'text/plain; encoding=utf-8'
        return response


    # urls.py
    from django.conf.urls import patterns

    urlpatterns = patterns('some_app.views',
        (r'^book/(?P<id>\d+)/', 'book_view'),
    )


In the above example, when you access "/book/12/" the Book model with
primary key 12 is added as a keyword argument the decorated view. If no
such Book exists then the decorator raises an Http404.

You only need to define one function/method. And just pass a parameter
to the @detail_view decorator.

The above example is fine and dandy, but what if you want to use a
template instead of creating a raw HttpResponse? With class-based-views
you subclass using mixins. With django-view-accessories you simply
"stack" decorators::

    from view_accessories.generic import template_view
    from view_accessories.detail import detail_view

    @detail_view(model=Book)
    @template_view(template_name='some_app/book_detail.html')
    def book_detail_with_template(request, book):
        return {'book': book, 'version': '0.1.0'}

Stacking decorators not your cup of tea? You can use the
template_detail_view instead::

    from view_accessories.detail import template_detail_view

    @template_detail_view(model=Book)
    def book_detail_with_template(request, book):
        return {'book': book, 'version': '0.1.0'}


The equivalent of the above, with class-based views is::

    from django.views.generic import DetailView

    class BookDetail(DetailView):

        model = Book

        def get_context_data(self, **kwargs):
            context = super(BookDetail, self).get_context_data(**kwargs)
            context['version'] = '0.1.0'
            return context


Even better, if All the context you wanted to pass to the template in the above
example wat the book itself, you can define your function to simply return
nothing::

    @template_detail_view(model=Book)
    def book_detail_with_template(request, book):
        pass

This is equivalent to::

    @template_detail_view(model=Book, template_name='some_app/book_detail.html')
    def book_detail_with_template(request, book):
        return {'book': book}

If you prefer the CBV way that's fine. It's also more flexible than
django-view-accessories. But django-view-accesories is for people who
prefer the function-based views with just a little sugar.


Want to do list views?  It's similar::

    from view_accessories.list import template_list_view

    from .models import Book

    @template_list_view(model=Book)
    def book_list(request, books):
        pass
        

If you don't want all Books you can instead pass
queryset=Book.objects.filter() to the template_list_view decorator. The
default template is "app_name/book_list.html", but you can override it
passing "template_name" to the decorator.

All django-view-accessories decorators also support the methods=
argument::

    @view(methods=['GET', 'POST'])
    def my_view(request):
        ...

You can also stack them with Django's view decorators, e.g::

    from view_accessories.detail import detail_view
    from django.contrib.auth.decorators import permission_required

    from .models import Book

    @permission_required('some_app.delete_book')
    @detail_view(model=Book, methods=['DELETE'])
    def delete_book(request, book):
        book.delete()
        return HttpResponse('', status=204)
