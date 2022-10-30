import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
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
        self.guest = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.user)
        cache.clear()
        post_count: list = []
        for i in range(35):
            post_count.append(Post(
                text='Тестовый пост',
                group=self.group,
                author=self.user))
        Post.objects.bulk_create(post_count)

    def check_post(self, first_object):
        with self.subTest(first_object=first_object):
            self.assertEqual(first_object.text, self.post.text)
            self.assertEqual(first_object.author, self.post.author)
            self.assertEqual(first_object.group, self.post.group)

    def test_index_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIsInstance(
            response.context['form'].fields['image'],
            forms.fields.ImageField)
        self.check_post(response.context['page_obj'][0])

    def test_group_post_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}))
        self.check_post(response.context['page_obj'][0])
        self.assertEqual(response.context['group'], self.group)
        self.assertIsInstance(
            response.context['form'].fields['image'],
            forms.ImageField)

    def test_profile_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        self.check_post(response.context['page_obj'][0])
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(
            response.context['post_count'],
            self.post.author.posts.count())
        self.assertIsInstance(
            response.context['form'].fields['image'],
            forms.ImageField)

    def test_post_detail_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        self.check_post(response.context['post'])
        self.assertIsInstance(
            response.context['form_'].fields['image'],
            forms.ImageField)

    def test_post_create_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['is_edit'], True)
        self.assertIsInstance(
            response.context['form'].fields['image'],
            forms.ImageField)

    def test_cache(self):
        post = Post.objects.create(
            text='Пост для проверки',
            author=self.user)
        content_add = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Описание',
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()
        post: list = []
        for i in range(13):
            post.append(Post(
                text='Тестовый пост',
                group=self.group,
                author=self.user))
        Post.objects.bulk_create(post)

    def test_paginator(self):
        first_page_posts = 10
        second_page_posts = 3
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}),
        ]

        for rev in url_pages:
            self.assertEqual(len(
                self.guest_client.get(rev).context['page_obj']),
                first_page_posts)
            self.assertEqual(len(
                self.guest_client.get(rev + '?page=2').context['page_obj']),
                second_page_posts)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized = User.objects.create_user(username='authorized')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый текст для подписчиков',
            author=cls.author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_follow_on_author(self):
        follow_count = Follow.objects.count()
        Follow.objects.create(author=self.author,
                              user=self.authorized)
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.authorized}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow_on_author(self):
        Follow.objects.create(author=self.author,
                              user=self.authorized)
        unfollow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), unfollow_count - 1)

    def test_list_follower(self):
        Follow.objects.create(
            author=self.author,
            user=self.authorized)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'].object_list)

    def test_list_unfollower(self):
        post = Post.objects.create(
            author=self.author,
            text='Текстовый текст')
        Follow.objects.create(user=self.authorized,
                              author=self.author)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
