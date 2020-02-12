from django.http import HttpRequest
from django.test import TestCase
from django.urls import resolve
from .views import home_page


# Create your tests here.
# class SmokeTest(TestCase):
#     def test_bad_maths(self):
#         self.assertEqual(1 + 1, 3)

class HomePageTest(TestCase):
    def test_users_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')
