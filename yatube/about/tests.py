from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

OK = HTTPStatus.OK


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса"""
        urls_status_codes = {
            '/about/author/': OK,
            '/about/tech/': OK,
        }
        for urls, status_codes in urls_status_codes.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertEqual(response.status_code, status_codes)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса"""
        urls_templates = {
            '/about/author/': 'about/about.html',
            '/about/tech/': 'about/tech.html',
        }
        for urls, templates in urls_templates.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertTemplateUsed(response, templates)

    def test_pages_uses_correct_template(self):
        """При запросе к namespace:name применяется шаблон html."""
        templates_names = {
            'about/about.html': 'about:author',
            'about/tech.html': 'about:tech',
        }
        for template, name in templates_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(name))
                self.assertTemplateUsed(response, template)
