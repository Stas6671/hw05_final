import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post, Comment

User = get_user_model()
ONE_POST = 1
ONE_COMMENT = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormCreateEditTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create(username='Auth')
        cls.auth_client = Client()
        cls.author = User.objects.create(username='HasNoName')
        cls.auth_client.force_login(cls.author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='some-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create_with_image(self):
        """Проверка создания поста с картинкой."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_content = {
            'text': 'Тестовый пост',
            'image': uploaded,
        }
        posts_before_creation = Post.objects.count()

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_content,
            follow=True,
        )
        posts_after_creation = Post.objects.count()
        post = Post.objects.all().first()

        self.assertEqual(post_content['text'], post.text)
        self.assertEqual(self.user, post.author)
        self.assertEqual(
            posts_before_creation + ONE_POST,
            posts_after_creation
        )

    def test_post_create_with_group(self):
        """Проверка создания поста с группой."""
        post_content = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
        }
        posts_before_creation = Post.objects.count()

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_content,
        )
        posts_after_creation = Post.objects.count()
        post = Post.objects.all().first()

        self.assertEqual(post_content['text'], post.text)
        self.assertEqual(post_content['group'], post.group.pk)
        self.assertEqual(self.user, post.author)
        self.assertEqual(
            posts_before_creation + ONE_POST,
            posts_after_creation
        )

    def test_post_create_without_group(self):
        """Проверка создания поста без группы."""
        post_content = {
            'text': 'Пост без группы'
        }

        posts_before_creation = Post.objects.count()

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_content,
        )

        posts_after_creation = Post.objects.count()
        first_post = Post.objects.all().first()

        self.assertEqual(post_content['text'], first_post.text)
        self.assertEqual(first_post.group, None)
        self.assertEqual(self.user, first_post.author)
        self.assertEqual(
            posts_before_creation + ONE_POST,
            posts_after_creation
        )

    def test_post_edit_author(self):
        """Проверка изменения поста автором."""
        created_post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group
        )
        post_edited_content = {
            'text': 'Пост изменён',
            'group': self.group.pk
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': created_post.id}
            ),
            data=post_edited_content
        )
        edited_post = Post.objects.get(id=created_post.id)

        self.assertEqual(edited_post.pub_date, created_post.pub_date)
        self.assertEqual(edited_post.author, created_post.author)
        self.assertEqual(edited_post.text, post_edited_content['text'])
        self.assertEqual(edited_post.group.pk, post_edited_content['group'])

    def test_post_create_not_added_guest(self):
        """Проверка добавления поста гостем."""
        posts_before_creation = Post.objects.count()
        post_content = {
            'text': 'Пост не добавлен',
            'group': self.group
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=post_content,
        )
        posts_after_creation = Post.objects.count()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(posts_after_creation, posts_before_creation)

    def test_post_edit_not_chenge_not_author(self):
        """Проверка редактирования поста не автором."""
        created_post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group
        )
        post_content = {
            'text': 'Пост не изменён',
            'group': self.group
        }
        response = self.auth_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': created_post.id}
            ),
            data=post_content,
        )
        old_post = Post.objects.get(id=created_post.id)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(old_post.pub_date, created_post.pub_date)
        self.assertEqual(old_post.author, created_post.author)
        self.assertEqual(old_post.text, created_post.text)
        self.assertEqual(old_post.group, created_post.group)

    def test_post_edit_not_chenge_guest(self):
        """Проверка редактирования поста гостем."""
        created_post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group
        )
        post_content = {
            'text': 'Пост не изменён',
            'group': 'Группа не изменена'
        }
        response = self.guest_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': created_post.id}
            ),
            data=post_content,
        )
        old_post = Post.objects.get(id=created_post.id)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(old_post.pub_date, created_post.pub_date)
        self.assertEqual(old_post.author, created_post.author)
        self.assertEqual(old_post.text, created_post.text)
        self.assertEqual(old_post.group, created_post.group)

    def test_add_comment_authorized_client(self):
        """Проверка создания комментария авторизованным пользователем."""
        created_post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group
        )
        comment_content = {
            'text': 'Пустой комментарий'
        }

        comments_before_creation = Comment.objects.count()

        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': created_post.id}
            ),
            data=comment_content,
        )

        comments_after_creation = Comment.objects.count()
        first_comment = Comment.objects.all().first()

        self.assertEqual(comment_content['text'], first_comment.text)
        self.assertEqual(self.user, first_comment.author)
        self.assertEqual(
            comments_before_creation + ONE_COMMENT,
            comments_after_creation
        )

    def test_add_comment_guest_client(self):
        """Проверка создания комментария гостем."""
        created_post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group
        )
        comment_content = {
            'text': 'Пустой комментарий'
        }

        comments_before_creation = Comment.objects.count()

        response = self.guest_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': created_post.id}
            ),
            data=comment_content,
        )

        comments_after_creation = Comment.objects.count()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(comments_after_creation, comments_before_creation)
