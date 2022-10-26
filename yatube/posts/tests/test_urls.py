from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client


from ..models import Group, Post

User = get_user_model()
OK = HTTPStatus.OK


class StaticUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем общедоступные страницы
    def test_url_exists_at_desired_location(self):
        """Страница доступна любому пользователю."""
        url_exists = {
            '/': OK,
            '/group/test-slug/': OK,
            '/profile/auth/': OK,
            f'/posts/{ self.post.id }/': OK,
            '/page_not_found/': HTTPStatus.NOT_FOUND,
        }
        for url, status_code in url_exists.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_url_exists_at_desired_authorized(self):
        """Страница доступна авторизованному пользователю."""
        url_exists = {
            '/create/': OK,
            f'/posts/{ self.post.id }/edit/': HTTPStatus.FOUND,
        }
        for url, status_code in url_exists.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)
