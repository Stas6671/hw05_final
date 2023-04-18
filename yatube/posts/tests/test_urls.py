from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from http import HTTPStatus

from ..models import Group, Post, Follow

User = get_user_model()
UNEXISTING_URL = '/unexisting/'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user('Auth')
        cls.author = User.objects.create_user('HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='cats',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.author)
        self.authorized_client.force_login(self.user)
        self.unexisting_url = UNEXISTING_URL

    def test_urls_uses_correct_template(self):
        """Общедоступные страницы используют правильные шаблоны."""
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author}/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_url_uses_correct_template(self):
        """Cтраница создания поста использует правильный шаблон."""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_post_edit_url_uses_correct_template(self):
        """Cтраница редактирования поста использует правильный шаблон."""
        response = self.auth_client.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_create_url_exists_at_desired_location_authorized(self):
        """Авторизованному пользователю доступно создание поста."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_auth(self):
        """Автору доступно редактирование поста."""
        response = self.auth_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_authorized_no_auth(self):
        """Пользователю не автору недоступно редактирование поста."""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertRedirects(response, ('/posts/1/'))

    def test_post_edit_url_redirect_guest(self):
        """Гостя перенаправляет при попытке редактирования поста."""
        response = self.guest_client.get('/posts/1/edit/')
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/edit/'))

    def test_post_create_url_redirect_guest(self):
        """Гостя перенаправляет при попытке создания поста."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_unexisting_page_exists_at_desired_location(self):
        """Запрос к несуществующей странице возвращает ошибку 404."""
        response = self.guest_client.get(self.unexisting_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_follow_url_uses_correct_template(self):
        """Cтраница подписок использует правильный шаблон."""
        response = self.authorized_client.get('/follow/')
        self.assertTemplateUsed(response, 'posts/follow.html')

    def test_follow_url_redirect_guest(self):
        """Гостя перенаправляет при попытке просмотра постов по подписке."""
        response = self.guest_client.get('/follow/')
        self.assertRedirects(response, ('/auth/login/?next=/follow/'))

    def test_profile_unfollow_url_exists_at_follower(self):
        """Подписчику доступна отписка."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client.get(
            f'/profile/{self.author}/unfollow/'
        )
        self.assertRedirects(response, (f'/profile/{self.author}/'))

    def test_profile_follow_url_exists_at_authorized(self):
        """Авторизованному пользователю доступна подписка."""
        response = self.authorized_client.get(
            f'/profile/{self.author}/follow/'
        )
        self.assertRedirects(response, (f'/profile/{self.author}/'))
