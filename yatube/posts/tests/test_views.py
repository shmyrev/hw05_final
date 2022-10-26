import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Follow

User = get_user_model()

# Создаем временную папку для медиа-файлов;
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.image_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.gif',
            content=cls.image_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение,
        # изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_view_pages_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'group_slug': 'test_slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'auth'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{self.post.id}'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'core/404.html': '/nonexist-page/',
        }
        # Проверяем, что при обращении к name вызывается HTML-шаблон
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка контекста главной страницы
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_image_0 = Post.objects.first().image

        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_image_0, 'posts/image.gif')

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'group_slug': 'test_slug'})
        )
        first_object = response.context['group']
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        group_description_0 = first_object.description
        post_image_0 = Post.objects.first().image

        self.assertEqual(group_title_0, 'Тестовая группа')
        self.assertEqual(group_slug_0, 'test_slug')
        self.assertEqual(group_description_0, 'Тестовое описание')
        self.assertEqual(post_image_0, 'posts/image.gif')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_image_0 = Post.objects.first().image

        self.assertEqual(response.context['author'].username, 'auth')
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_image_0, 'posts/image.gif')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_image_0 = Post.objects.first().image

        self.assertEqual(first_object, self.post)
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_image_0, 'posts/image.gif')


# Тестирование паджинатора
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса
        cls.user = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.posts = list()
        for i in range(13):
            cls.posts.append(Post(
                text=f'Текстовый пост {i}',
                author=cls.user,
                group=cls.group
            ))
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_countains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_countains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса
        cls.user = User.objects.create_user(username='auth3')

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Тест кэширования главной страницы."""
        user = CacheTest.user
        post = Post.objects.create(
            text='test_text',
            author=user
        )
        index_url = reverse('posts:index')
        response = self.authorized_client.get(index_url)
        posts = response.context['page_obj'].object_list
        posts_count = len(posts)
        self.assertIn(post, posts)
        cache.clear()
        response = self.authorized_client.get(index_url)
        posts = response.context['page_obj'].object_list
        self.assertEqual(len(posts), posts_count)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth4')
        cls.user_follower = User.objects.create_user(username='auth_follower')

        cls.post_follower = Post.objects.create(
            text='test-text-follower',
            author=cls.user_follower
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.follower_authorized_client = Client()
        self.follower_authorized_client.force_login(self.user_follower)

    def test_follow(self):
        """
            Авторизованный пользователь может подписываться на других
            пользователей и удалять их из подписок.
        """
        user = FollowTest.user
        follower_user = FollowTest.user_follower
        profile_follow_url = reverse(
            'posts:profile_follow',
            kwargs={'username': follower_user.username}
        )
        profile_unfollow_url = reverse(
            'posts:profile_unfollow',
            kwargs={'username': follower_user.username}
        )
        follower_user_profile_url = reverse(
            'posts:profile',
            kwargs={'username': follower_user.username}
        )
        response = self.authorized_client.get(profile_follow_url)
        self.assertRedirects(response, follower_user_profile_url)
        self.assertTrue(
            Follow.objects.filter(
                user=user,
                author=follower_user
            ).exists()
        )
        response = self.authorized_client.get(profile_unfollow_url)
        self.assertRedirects(response, follower_user_profile_url)
        self.assertFalse(
            Follow.objects.filter(
                user=user,
                author=follower_user
            ).exists()
        )

    def test_post_list_on_subscriber(self):
        """
            Новая запись пользователя появляется в ленте тех, кто на него
            подписан и не появляется в ленте тех, кто не подписан.
        """
        follower_user = FollowTest.user_follower
        follower_post = FollowTest.post_follower

        follow_index_url = reverse('posts:follow_index')

        profile_follow_url = reverse(
            'posts:profile_follow',
            kwargs={'username': follower_user.username}
        )
        self.authorized_client.get(profile_follow_url)
        response = self.authorized_client.get(follow_index_url)
        self.assertIn(
            follower_post, response.context.get('page_obj').object_list
        )
        response = self.follower_authorized_client.get(follow_index_url)
        self.assertNotIn(
            follower_post, response.context.get('page_obj').object_list
        )
