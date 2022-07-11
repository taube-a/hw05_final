import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from django.conf import settings
from ..models import Group, Post, Comment
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Test group',
                                         slug='test-slug',
                                         description='Test group description')
        cls.post = Post.objects.create(author=cls.user,
                                       group=cls.group,
                                       text='Lorem ipsum dolor sit amet,'
                                            'consectetur adipiscing elit.'
                                            'Fusce sodales tortor et nulla '
                                            'vehicula consequat.')
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создаcт запись поста в БД."""

        posts_count = Post.objects.count()
        text = 'Lorem ipsum'
        username = self.post.author.username
        image = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                 b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(name='image.png',
                                      content=image,
                                      content_type='image/png')
        form_data = {'text': text,
                     'image': uploaded}

        response = self.authorized_client.post(reverse('posts:create_post'),
                                               data=form_data, follow=True)

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': username}),
                             msg_prefix='Ошибка редиректа при создании поста.')
        self.assertEqual(Post.objects.count(), posts_count + 1,
                         'Ошибка при создании поста.')
        self.assertTrue(Post.objects.filter(text=text, author=self.user,
                                            image='posts/image.png',
                                            group=None).exists(),
                        'Ошибка содержания нового поста.')

    def test_edit_post(self):
        """Валидная форма редактирует запись поста в БД."""
        posts_count = Post.objects.count()
        text = 'Lorem ipsum dolor'
        group = self.post.group.id
        form_data = {'text': text, 'group': group, }

        rev = reverse('posts:post_edit', kwargs={'pk': posts_count})
        response = self.authorized_client.post(rev, data=form_data,
                                               follow=True)

        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'pk': posts_count}),
                             msg_prefix='Ошибка редиректа при редактировании'
                                        ' поста.')
        self.assertEqual(Post.objects.count(), posts_count,
                         'Ошибка при редактировании поста.')
        self.assertTrue(Post.objects.filter(text=text, author=self.user,
                                            group=group).exists(),
                        'Ошибка содержания при редактировании поста.')

    def test_create_comment(self):
        """Валидная форма создаcт запись комментария в БД."""
        comments_count = Comment.objects.count()
        post_id = self.post.pk
        text = 'Lorem ipsum'
        form_data = {'text': text}

        rev = reverse('posts:add_comment', kwargs={'pk': post_id})
        response = self.authorized_client.post(rev, data=form_data,
                                               follow=True)

        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'pk': post_id}),
                             msg_prefix='Ошибка редиректа при создании '
                                        'комментария.')
        self.assertEqual(Comment.objects.count(), comments_count + 1,
                         'Ошибка при создании комментария.')
        self.assertTrue(Comment.objects.filter(text=text, author=self.user)
                        .exists(),
                        'Ошибка содержания нового комментария.')
