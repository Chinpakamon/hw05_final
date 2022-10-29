from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='Название группы',
                             max_length=200)
    slug = models.SlugField(verbose_name='Краткое название группы',
                            unique=True)
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста')
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        related_name='selected_posts',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Текст нового комментария')
    author = models.ForeignKey(User, verbose_name='Автор комментария',
                               on_delete=models.CASCADE, related_name='comments')
    created = models.DateTimeField(verbose_name='Дата публикации комментария',
                                   auto_now_add=True,
                                   db_index=True)
    post = models.ForeignKey(Post, verbose_name='Пост', related_name='comments',
                             on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created']
        verbose_name_plural = 'Коментарии'
        verbose_name = 'Коментарий'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User, verbose_name='Подписчик',
                             on_delete=models.CASCADE, related_name='follower', null=True)
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE, related_name='following', null=True)

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
