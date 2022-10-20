from django.test import TestCase, Client
from http import HTTPStatus

OK = HTTPStatus.OK


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_user_url_exists_location(self):
        """Проверка доступности адреса"""
        urls_status_codes = {
            '/auth/signup/': OK,
            '/auth/logout/': OK,
            '/auth/login/': OK,
            '/auth/password_reset_form/': OK,
        }
        for urls, status_codes in urls_status_codes.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertEqual(response.status_code, status_codes)
