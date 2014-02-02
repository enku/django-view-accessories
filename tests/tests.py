from __future__ import unicode_literals

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_app.settings')

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django import http
from django.test import TestCase, RequestFactory

from view_accessories.generic import view, redirect_view
from view_accessories.list import list_view
from test_app.models import Widget

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
        @redirect_view('https://www.google.com/', permanent=True)
        def myview(request):
            pass

        # When we access the view
        response = myview(factory.get('/'))

        # Then we get a permanent redirect
        self.assertEqual(response['location'], 'https://www.google.com/')
        self.assertEqual(response.status_code, 301)

    def test_response_gone(self):
        # Given the view with no url
        @redirect_view(None)
        def myview(request):
            pass

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


if __name__ == '__main__':
    from django.test.simple import DjangoTestSuiteRunner
    from django.utils.unittest import main

    runner = DjangoTestSuiteRunner()
    runner.setup_test_environment()
    runner.setup_databases()
    main()
    runner.teardown_databases()
    runner.teardown_test_environment()
