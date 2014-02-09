from __future__ import unicode_literals

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_app.settings')

from django import forms, http
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms.models import ModelForm
from django.test import RequestFactory, TestCase

from test_app.models import Widget
from view_accessories.detail import detail_view
from view_accessories.edit import create_view, form_view
from view_accessories.generic import redirect_view, view
from view_accessories.list import list_view, paginate_queryset


factory = RequestFactory()


class ViewTest(TestCase):
    """view() decorator"""
    def test_decorator(self):
        # Given the decorated function
        @view()
        def my_myview(request):
            return http.HttpResponse('ok')

        # When we call the view
        response = my_myview(factory.get('/'))

        # Then we get a response.
        self.assertContains(response, 'ok')

    def test_methods(self):
        """methods argument"""
        # Given the decorated function that only takes GET requests
        @view(methods=['GET'])
        def my_myview(request):
            return http.HttpResponse('ok')

        # When we POST to the view
        response = my_myview(factory.post('/', {}))

        # Then we get method not allowed
        self.assertEqual(response.status_code, 405)

    def test_options(self):
        """OPTIONS verb"""
        # Given the decorated function
        @view(methods=['GET', 'POST'])
        def my_myview(request):
            return http.HttpResponse('ok')

        # When we call OPTIONS to view
        response = my_myview(factory.options('/'))

        # Then we get an 'Allow' method in the response.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['allow'], 'GET, POST')

    def test_view(self):
        view = reverse('test_app.views.my_view', args=[69])
        response = self.client.get(view)
        self.assertEqual(response.content.decode('utf-8'), '69')


class TemplateView(TestCase):
    """Test for template views"""
    def test_template_view(self):
        """template_view"""
        # Given the template view
        view = reverse('test_app.views.my_template_view',
                       args=['this is a test'])

        # When we call the view
        response = self.client.get(view)

        # Then the template is rendered and returned
        self.assertContains(response, 'this is a test')
        self.assertEqual(response.templates[0].name, 'test_app/test.html')


class RedirectView(TestCase):
    def test_redirect(self):
        """Redirect view"""
        # Given the redirect view
        view = reverse('test_app.views.my_redirect_view')

        # When we call the view
        response = self.client.get(view)

        # We are redirected
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'http://www.google.com/?')

    def test_redirect_with_querystring(self):
        # Given the view with query_string=True
        view = reverse('test_app.views.my_redirect_view')

        # When we get it with a querystring
        response = self.client.get('%s?q=test' % view)

        # Then our redirect also has the query string
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'http://www.google.com/?q=test')

    def test_redirect_permanent(self):
        # Given the view with permanent redirect
        @redirect_view(permanent=True)
        def myview(request):
            return 'https://www.google.com/'

        # When we access the view
        response = myview(factory.get('/'))

        # Then we get a permanent redirect
        self.assertEqual(response['location'], 'https://www.google.com/')
        self.assertEqual(response.status_code, 301)

    def test_response_gone(self):
        # Given the view with no url
        @redirect_view
        def myview(request):
            return None

        # When we access the view
        response = myview(factory.get('/'))

        # Then we get HTTP gone
        self.assertEqual(response.status_code, 410)


class DetailView(TestCase):
    def test_detail_view(self):
        """detail_view"""
        # Given the widget
        widget = Widget()
        widget.text = 'This is a test'
        widget.save()

        # When we go to the detail_view decorated view
        view = reverse('test_app.views.my_detail_view', args=[widget.pk])
        response = self.client.get(view)

        # Then it works
        self.assertContains(response, 'This is a test')

    def test_detail_view_404(self):
        """detail_view throws 404"""
        # When we go to the detail_view decorated view of a bogus widget
        view = reverse('test_app.views.my_detail_view', args=[99999])
        response = self.client.get(view)

        # Then we get a 404 error
        self.assertEqual(response.status_code, 404)

    def test_stacked_detail_and_template(self):
        """Stacked detail_view and template_view"""
        # Given the widget
        widget = Widget()
        widget.text = 'This is a test'
        widget.save()

        # When we go to the detail_view decorated view
        view = reverse('test_app.views.detail_view_with_template',
                       args=[widget.pk])
        response = self.client.get(view)

        # Then it works
        self.assertContains(response, 'This is a test')
        self.assertEqual(response.templates[0].name,
                         'test_app/widget_detail.html')

    def test_detail_view_with_field(self):
        """Provide field to detail_view"""
        # Given the widget
        widget = Widget()
        widget.text = 'This is a test'
        widget.save()

        # And the detail "view"
        @detail_view(model=Widget, field='text', kwarg='text')
        def my_view(request, widget):
            return widget

        # When we call the view
        response = my_view(factory.get('/'), text='This is a test')

        # Then the view gets our widget
        self.assertEqual(widget, response)


class TemplateDetailView(TestCase):
    def test_template_detail_view(self):
        """template_detail_view"""
        # Given the widget
        widget = Widget()
        widget.text = 'This is a test'
        widget.save()

        # When we go to the detail_view decorated view
        view = reverse('test_app.views.detail_view_with_template2',
                       args=[widget.pk])
        response = self.client.get(view)

        # Then it works
        self.assertContains(response, 'This is a test')
        self.assertEqual(response.templates[0].name,
                         'test_app/widget_detail.html')


class ListView(TestCase):
    def test_list_view(self):
        """list_view"""
        # Given the list of widgets
        widgets = [Widget.objects.create(text='Widget%s' % i)
                   for i in range(5)]

        # When we call the list_view
        view = reverse('test_app.views.my_list_view')
        response = self.client.get(view)

        # Then is shows me widgets
        for widget in widgets:
            self.assertContains(response, '"%s"' % widget.text)

    def test_list_view_with_queryset(self):
        # Given the widgets
        for i in range(10):
            Widget.objects.create(text='Widget%s' % i)

        # When we define a list_view with a queryset
        @list_view(queryset=Widget.objects.all()[:4])
        def my_list_view(request, widgets):
            return widgets

        # Then the view is called with that queryset
        response = my_list_view(factory.get('/'))

        # Then it filters me widgets
        self.assertEqual(response.count(), 4)

    def test_list_view_without_allow_empty(self):
        """404 on allow_empty=False"""
        # When we define a list_view with a queryset with allow_empty=False
        @list_view(model=Widget, allow_empty=False)
        def my_list_view(request, widgets):
            return widgets

        # And call it without creating any widgets
        # Then we get a 404
        with self.assertRaises(http.Http404) as context:
            my_list_view(factory.get('/'))

        exception = context.exception
        self.assertEqual(str(exception), 'Empty list')

    def test_stacked_list_and_template_view(self):
        """Stacked list_ and template_ views"""
        # Given the widgets
        for i in range(10):
            Widget.objects.create(text='StackedWidget%s' % i)

        # When we go to the stacked view
        view = reverse('test_app.views.stacked_list_view')
        response = self.client.get(view)

        # Then the widgets show
        for i in range(10):
            self.assertContains(response, 'StackedWidget%i' % i)

        self.assertNotContains(response, 'In descending order')


class TemplateListView(TestCase):
    def test_template_list_view(self):
        # Given the widgets.
        for i in range(5):
            Widget.objects.create(text='TemplateListView_%i' % i)

        # Given the template_list_view view
        view = reverse('test_app.views.my_template_list_view')

        # When we call the view
        response = self.client.get(view)

        # Then the widgets show
        for i in range(5):
            self.assertContains(response, 'TemplateListView_%i' % i)

        self.assertContains(response, 'In descending order')

    def test_template_list_view_has_pagination(self):
        # Given the widgets.
        for i in range(7):
            Widget.objects.create(text='TemplateListView_%i' % i)

        # Given the template_list_view view
        view = reverse('test_app.views.my_template_list_view') + '?page=2'

        # When we call the view
        response = self.client.get(view)

        # Then it has pagination
        self.assertContains(response, 'TemplateListView_1')
        self.assertContains(response, 'TemplateListView_0')
        self.assertNotContains(response, 'TemplateListView_3')


class Pagination(TestCase):
    def setUp(self):
        for i in range(23):
            Widget.objects.create(text='Widget %s' % i)
        self.widgets = Widget.objects.all()

    def test_paginate_queryset(self):
        """paginate_queryset()"""
        # Given the queryset
        queryset = self.widgets

        # And the request
        request = factory.get('/?page=2')

        # When we call paginate_queryset()
        pagination = paginate_queryset(request, queryset, 'page', 5)

        # Then we get a pagination with the pertinant data
        self.assertEqual(type(pagination), dict)
        self.assertEqual(len(pagination['objects']), 5)
        self.assertEqual(pagination['page'].number, 2)
        self.assertTrue(pagination['has_other_pages'])

    def test_view_with_pagination(self):
        # Given the decorated view
        @list_view(model=Widget, paginate=True, page_size=5)
        def my_view(request, widgets, pagination=None):
            widgets = pagination['objects']
            response = http.HttpResponse(
                '\n'.join(i.text for i in widgets))
            response.content_type = 'text/plain'
            # The return value is contrived for testing
            return response, pagination

        # When we access the view
        request = factory.get('/?page=last')
        response, pagination = my_view(request)

        # We have a "pagination" accessory
        self.assertTrue(isinstance(pagination, dict))

        # Our page has 3 objects
        self.assertEqual(len(response.content.decode('utf-8').split('\n')), 3)

        # Because we're on the last page
        self.assertFalse(pagination['page'].has_next())

    def test_invalid_page_raises_404(self):
        """Invalid page => HTTP 404"""
        # Given the queryset
        queryset = self.widgets

        # And the request for an invalid page
        request = factory.get('/?page=100')

        # When we call paginate_queryset() it raises 404
        with self.assertRaises(http.Http404):
            paginate_queryset(request, queryset, 'page', 5)

        # A "bugus" page does the same
        request = factory.get('/?page=invalid')
        with self.assertRaises(http.Http404):
            paginate_queryset(request, queryset, 'page', 5)

    def test_page_size_from_request(self):
        # Given the queryset
        queryset = self.widgets

        # And the request for an invalid page
        request = factory.get('/?page_size=10&page=3')

        # Then we can call paginate_queryset() to get tha page size from the
        # request
        pagination = paginate_queryset(request, queryset, 'page', 'page_size')
        self.assertEqual(pagination['paginator'].per_page, 10)
        self.assertEqual(len(pagination['objects']), 3)
        self.assertEqual(pagination['page'].number, 3)


class WithDjangoDecorators(TestCase):
    def test_login_required(self):
        """Django's login_required"""
        # Given the list_view that is decorated with Django's login_required
        view = reverse('test_app.views.login_required_view')

        # When we access the view
        response = self.client.get(view)

        # Then we are redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].endswith(
            '/accounts/login/?next=%s' % view))

        # When we are given a user and login
        User.objects.create_user(username='test', email='test@test.invalid',
                                 password='test')
        logged_in = self.client.login(username='test', password='test')
        assert logged_in

        # Then we can access the view successfully
        response = self.client.get(view)
        self.assertEqual(response.status_code, 200)


class FormView(TestCase):
    def test_form_view(self):
        # Given the form
        class TestForm(forms.Form):
            name = forms.CharField(max_length=100)
            age = forms.IntegerField()

        # And the form_view that uses the form
        @form_view(form=TestForm)
        def test_view(request, form):
            return form

        # When we post to the form
        post_data = {'name': 'Sally', 'age': 5}
        form = test_view(factory.post('/', post_data))

        # Then I get a bound form with the data posted
        self.assertTrue(isinstance(form, TestForm))
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Sally')
        self.assertEqual(form.cleaned_data['age'], 5)

    def test_success_url(self):
        # Given the form
        class TestForm(forms.Form):
            name = forms.CharField(max_length=100)
            age = forms.IntegerField()

        # And the form_view that uses the form
        @form_view(form=TestForm, success_url='https://www.google.com/')
        def test_view(request, form):
            response = http.HttpResponse(form.as_p(), content_type='text/html')
            return response

        # When I post the form invalidly
        post_data = {'name': 'Sally'}  # missing required age
        response = test_view(factory.post('/', post_data))

        # Then I am taken back to the form
        self.assertContains(response, 'This field is required.')

        # When I post with valid data
        post_data = {'name': 'Sally', 'age': 5}
        response = test_view(factory.post('/', post_data))

        # Then I am redirected
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'https://www.google.com/')

    def test_form_view_stacked_with_detail_and_template_views(self):
        # And the following widget
        widget = Widget.objects.create(text='Original Text')

        # Given the triple-stacked form_view
        view = reverse('test_app.views.form2', args=[widget.pk])

        response = self.client.get(view)
        self.assertContains(response, 'Original Text')

        # When we post to the detail-like form_view with template
        post_data = {'text': 'New Text'}
        response = self.client.post(view, post_data)

        # Then the response shows the new text
        self.assertContains(response, 'New Text')

        # And the model is updated
        widget = Widget.objects.get(pk=widget.pk)  # refetch
        self.assertEqual(widget.text, 'New Text')


class CreateView(TestCase):
    def test_create_view(self):
        # Given the create_view
        @create_view(model=Widget, fields=['text'],
                     success_url='https://www.google.com/')
        def test_view(request, form):
            self.assertTrue(isinstance(form, ModelForm))
            self.assertNotEqual(form.instance.pk, None)
            response = http.HttpResponse(form.as_p(), content_type='text/html')
            return response

        # When I post to the form
        post_data = {'text': 'CreateView'}
        response = test_view(factory.post('/', post_data))

        # Then a model is saved
        widget = Widget.objects.filter(text='CreateView')
        self.assertEqual(widget.count(), 1)

        # And I am redirected
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'https://www.google.com/')

    def test_create_view_with_invalid(self):
        # Given the create_view
        view = reverse('test_app.views.create_form')

        # When I incorrectly post
        post_data = {}
        response = self.client.post(view, post_data)

        # Then we are taken back to the form
        self.assertContains(response, 'This field is required.')

    def test_template_create_form(self):
        # Given the template_create_view
        view = reverse('test_app.views.create_template')

        # When I
        post_data = {'text': 'test_template_create_form'}
        response = self.client.post(view, post_data)

        # Then a model is saved
        widget = Widget.objects.filter(text='test_template_create_form')
        self.assertEqual(widget.count(), 1)

        # And I am redirected
        self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    from django.test.simple import DjangoTestSuiteRunner
    from django.utils.unittest import main

    runner = DjangoTestSuiteRunner()
    runner.setup_test_environment()
    runner.setup_databases()
    main()
    runner.teardown_databases()
    runner.teardown_test_environment()
