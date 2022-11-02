from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Post, Group, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(
            username='author_user')
        cls.authorized_user = User.objects.create_user(
            username='authorized_user')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author_user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)
        self.author_client = Client()
        self.author_client.force_login(self.author_user)
        cache.clear()

    def test_edit_url(self):
        response = self.author_client.get(
            f'/posts/{self.post.id}/edit/').status_code
        self.assertEqual(response, 200)

    def test_page_template(self):
        page_dict = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author_user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in page_dict.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_access(self):
        dict_page = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author_user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status in dict_page.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address).status_code
                self.assertEqual(response, status)

    def test_guest_client_redirect(self):
        dict_page = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author_user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status in dict_page.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address).status_code
                self.assertEqual(response, status)
