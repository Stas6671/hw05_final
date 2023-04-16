from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow, SHORT_DESCRIPTION

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки отображения __str__',
        )

    def test_post_models_verbose_name(self):
        """verbose_name в полях модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses_post = {
            'author': 'автор',
            'text': 'текст',
            'group': 'сообщество',
            'image': 'картинка',
        }

        for field, expected_value in field_verboses_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_post_have_correct_object_names(self):
        """Проверка отображения значения поля __str__ модели Post."""
        post = PostModelTest.post
        self.assertEqual(self.post.text[:SHORT_DESCRIPTION], str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_models_verbose_name(self):
        """verbose_name в полях модели Group совпадает с ожидаемым."""
        group = GroupModelTest.group
        field_verboses_group = {
            'description': 'Описание',
            'slug': 'Каталог',
            'title': 'Заголовок',
        }

        for field, expected_value in field_verboses_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_group_have_correct_object_names(self):
        """Проверка отображения значения поля __str__ модели Group."""
        group = GroupModelTest.group
        self.assertEqual(self.group.title, str(group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    def test_comment_models_verbose_name(self):
        """verbose_name в полях модели Comment совпадает с ожидаемым."""
        comment = CommentModelTest.comment
        field_verboses_comment = {
            'post': 'пост',
            'author': 'автор',
            'text': 'текст',
        }

        for field, expected_value in field_verboses_comment.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, expected_value
                )

    def test_comment_have_correct_object_names(self):
        """Проверка отображения значения поля __str__ модели Comment."""
        comment = CommentModelTest.comment
        self.assertEqual(self.comment.text[:SHORT_DESCRIPTION], str(comment))


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.author = User.objects.create_user(username='HasNoName')
        cls.follower = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def test_follow_models_verbose_name(self):
        """verbose_name в полях модели Comment совпадает с ожидаемым."""
        follower = FollowModelTest.follower
        field_verboses_follower = {
            'user': 'подписчик',
            'author': 'автор',
        }

        for field, expected_value in field_verboses_follower.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follower._meta.get_field(
                        field
                    ).verbose_name, expected_value
                )
