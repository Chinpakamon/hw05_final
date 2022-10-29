from django.test import TestCase

from ..models import Group, Post, User


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_1')
        cls.post = Post.objects.create(
            text='[Фокшаны.] Еще переходъ до Фокшанъ, '
                 'во время котораго я ѣхалъ съ Монго.',
            author=cls.user,
        )

    def test_post_str(self):
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_post_verbose_name(self):
        field_verbose = {
            'text': 'Текст поста',
            'group': 'Группа',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_help_text_post(self):
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_1')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_group_str(self):
        self.assertEqual(self.group.title, str(self.group))

    def test_group_verbose_name(self):
        field_verbose_name = {
            'title': 'Название группы',
            'slug': 'Краткое название группы',
            'description': 'Описание'
        }
        for field, expected_value in field_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name,
                    expected_value)
