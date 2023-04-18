import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from typing import List

from ..forms import CommentForm
from ..models import Group, Post, Comment, Follow
from ..views import VARIABLE_NUM_POSTS

User = get_user_model()

ONE_POST = 1
TEST_CREATE_NUM_POSTS = 13
VARIABLE_NUM_POSTS_ON_SECOND_PAGE = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTemplateViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.user = User.objects.create_user('Auth')
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='cats',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=UPLOADED,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'Auth'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/post_create.html',
        }
        for adress, template in templates_pages_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostContextViewsTests(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.auth_client = Client()
        self.author = User.objects.create_user('HasNoName')
        self.user = User.objects.create_user('Auth')
        self.auth_client.force_login(self.author)
        self.authorized_client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='cats',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.author,
            text='Тестовый пост',
            group=self.group,
            image=UPLOADED,
        )
        self.comments = Comment.objects.create(
            post=self.post,
            author=self.author,
            text='Тестовый комментарий',
        )
        self.follower = Follow.objects.create(
            user=self.user,
            author=self.author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_page_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_page_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        )
        self.assertIn('group', response.context)
        self.assertEqual(
            response.context.get('group'), self.group
        )
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_page_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.author})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.post.author)
        self.assertIn('page_obj', response.context)
        self.assertIn('following', response.context)
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        self.assertIn('post', response.context)
        self.assertIn('form', response.context)
        self.assertIn('comments', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertIsNotNone(response.context.get('post').comments)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIn('form', response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for field, content in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, content)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id})
        )
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)
        self.assertTrue('is_edit')
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for field, content in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, content)

    def test_page_follow_show_correct_context(self):
        """Шаблон follow сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        list_of_posts: List[Post] = []
        cls.guest_client = Client()
        cls.user = User.objects.create(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.auth_client = Client()
        cls.author = User.objects.create(username='Auth')
        cls.auth_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='cats',
            description='Тестовое описание',
        )
        for post in range(TEST_CREATE_NUM_POSTS):
            list_of_posts.append(
                Post(
                    text='Тестовый текст поста',
                    author=cls.user,
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(list_of_posts)
        Follow.objects.create(
            user=cls.author,
            author=cls.user,
        )

    def test_index_first_page_contains_ten_records(self):
        cache.clear()
        """Проверка количества постов на первой странице равно 10."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), VARIABLE_NUM_POSTS)

    def test_index_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            VARIABLE_NUM_POSTS_ON_SECOND_PAGE
        )

    def test_group_post_first_page_contains_ten_records(self):
        """Проверка количества постов на первой странице равно 10."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
        )
        self.assertEqual(len(response.context['page_obj']), VARIABLE_NUM_POSTS)

    def test_group_post_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            VARIABLE_NUM_POSTS_ON_SECOND_PAGE
        )

    def test_profile_first_page_contains_ten_records(self):
        """Проверка количества постов на первой странице равно 10."""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )
        self.assertEqual(len(response.context['page_obj']), VARIABLE_NUM_POSTS)

    def test_profile_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            VARIABLE_NUM_POSTS_ON_SECOND_PAGE
        )

    def test_follow_index_first_page_contains_ten_records(self):
        cache.clear()
        """Проверка количества постов на первой странице равно 10."""
        response = self.auth_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), VARIABLE_NUM_POSTS)

    def test_follow_index_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.auth_client.get(
            reverse('posts:follow_index') + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            VARIABLE_NUM_POSTS_ON_SECOND_PAGE
        )


class PostCacheTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create(username='HasNoName')
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )

    def test_cache_index(self):
        response = self.guest_client.get(reverse('posts:index'))
        content = response.content
        Post.objects.all().delete()
        new_response = self.guest_client.get(reverse('posts:index'))
        old_content = new_response.content
        self.assertEqual(content, old_content)
        cache.clear()
        updated_response = self.guest_client.get(reverse('posts:index'))
        new_content = updated_response.content
        self.assertNotEqual(old_content, new_content)


class PostFollowTest(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.auth_client = Client()
        self.author = User.objects.create_user('HasNoName')
        self.user = User.objects.create_user('Auth')
        self.auth_client.force_login(self.author)
        self.authorized_client.force_login(self.user)
        self.follower = Follow.objects.create(
            user=self.user,
            author=self.author,
        )

    def test_post_appears_on_follower_page(self):
        """Cообщение появилось на странице подписчика."""
        post_content = {
            'text': 'Тестовый пост для проверки подписки',
        }
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        posts_before_creation = len(response.context['page_obj'])

        self.auth_client.post(
            reverse('posts:post_create'),
            data=post_content,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        posts_after_creation = len(response.context['page_obj'])
        self.assertNotEqual(
            posts_before_creation,
            posts_after_creation
        )

    def test_follower_deleted_during_requests(self):
        follower_before = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        follower_after = Follow.objects.count()
        self.assertNotEqual(
            follower_before,
            follower_after
        )

    def test_follower_created_during_requests(self):
        Follow.objects.all().delete()
        follower_before = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author}))
        follower_after = Follow.objects.count()
        self.assertNotEqual(
            follower_before,
            follower_after
        )
