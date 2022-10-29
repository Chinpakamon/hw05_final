import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from django.urls import reverse

from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def check_data_post(self, form_data):
        with self.subTest(form_data=form_data):
            post = Post.objects.latest('id')
            self.assertEqual(post.text, form_data['text'])
            self.assertEqual(post.author, self.user)
            self.assertEqual(post.pk, form_data['group'])

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Текст поста',
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user}))

        self.assertEqual(Post.objects.count(), post_count + 1)
        self.check_data_post(form_data)

    def test_edit_post(self):
        post = Post.objects.create(
            text='Текст поста для редактирования',
            group=self.group,
            author=self.user
        )
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post.id}))
        self.assertEqual(response.status_code, 200)
        self.check_data_post(form_data)


class TestCommentForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_authorized_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Текст комментария',
            post=self.post.pk,
            author=self.user).exists())
