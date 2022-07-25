from django.contrib.auth import get_user_model
from django.db import models
from taggit.managers import TaggableManager

from .ru_taggit import RuTaggedItem

User = get_user_model()


class Group(models.Model):
    """Таблица Сообщества."""
    title = models.CharField(verbose_name='Название группы', max_length=200,
                             unique=True)
    slug = models.SlugField(verbose_name='Адрес', unique=True)
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'сообщество'
        verbose_name_plural = 'сообщества'

    def __str__(self):
        return self.title


class Post(models.Model):
    """Таблица Посты."""
    title = models.CharField(verbose_name='Заголовок', max_length=200,
                             unique=False)
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Выберите группу'
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    tags = TaggableManager(through=RuTaggedItem, blank=True,)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    """Таблица Комментарии."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост комментария'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(verbose_name='Текст')
    created = models.DateTimeField(verbose_name='Дата публикации',
                                   auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [models.UniqueConstraint(fields=('user', 'author'),
                                               name='unique_follow')]
