from django.test import SimpleTestCase
from django.urls import reverse, resolve

from .views import PetalHomeView

class HomepageTests(SimpleTestCase):

    def test_homepage_url_name(self):
        response = self.client.get(reverse('petalhome'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def setUp(self):
        url = reverse('petalhome')
        self.response = self.client.get(url)

# index.html that's declared in the petal home view extends navbar.html'
    def test_homepage_template(self):
        self.assertTemplateUsed(self.response, 'navbar.html')

    def test_homepage_contains_correct_html(self):  # new
        self.assertContains(self.response, 'PeTaL')

    def test_homepage_does_not_contain_incorrect_html(self):  # new
        self.assertNotContains(self.response, 'I should not be on the page.')

    def test_homepage_url_resolves_homepageview(self):
        view = resolve('/')
        self.assertEqual(
            view.func.__name__,
            PetalHomeView.as_view().__name__
        )
