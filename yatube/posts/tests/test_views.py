import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django import forms

from ..models import Group, Post, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.not_author = User.objects.create(username='not_author')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug',
                                         description='Тестовое описание', )
        cls.image = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        cls.uploaded_image = SimpleUploadedFile(name='image.png',
                                                content=cls.image,
                                                content_type='image/png')
        for post_id in range(25):
            if post_id % 2 == 0:
                cls.post = Post.objects.create(author=cls.user,
                                               group=cls.group,
                                               text='Тестовый пост',
                                               image=cls.uploaded_image, )
            else:
                cls.post = Post.objects.create(author=cls.user,
                                               text='Тестовый пост',
                                               image=cls.uploaded_image, )
        cls.index = reverse('posts:index')
        cls.group_list = reverse('posts:group_list',
                                 kwargs={'slug': cls.post.group.slug})
        cls.profile = reverse('posts:profile',
                              kwargs={'username': cls.post.author.username})
        cls.post_detail = reverse('posts:post_detail',
                                  kwargs={'pk': cls.post.pk})
        cls.create_post = reverse('posts:create_post')
        cls.post_edit = reverse('posts:post_edit', kwargs={'pk': cls.post.pk})
        cls.names = (cls.index, cls.group_list, cls.profile)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_names = {self.index: 'posts/index.html',
                           self.group_list: 'posts/group_list.html',
                           self.profile: 'posts/profile.html',
                           self.post_detail: 'posts/post_detail.html',
                           self.create_post: 'posts/create_post.html',
                           self.post_edit: 'posts/create_post.html', }

        for reverse_name, template in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_create_post_and_post_edit_show_correct_form_context(self):
        """Шаблоны create_post и post_edit сформируются с правильным
        контекстом.
        """
        names = {'posts:create_post': self.create_post,
                 'posts:post_edit': self.post_edit, }

        for name, rev in names.items():
            response = self.authorized_client.get(rev)
            form_fields = {'text': forms.fields.CharField,
                           'group': forms.models.ModelChoiceField,
                           'image': forms.fields.ImageField, }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)

                    self.assertIsInstance(form_field, expected)

    def test_index_group_list_profile_pages_show_correct_context(self):
        """Шаблоны index, group_list и profile сформируются с правильным
        контекстом.
        """
        names = {'posts:index': self.index,
                 'posts:group_list': self.group_list,
                 'posts:profile': self.profile, }

        for name, rev in names.items():
            response = self.authorized_client.get(rev)
            post = response.context['page_obj'].object_list[0]
            context = {'auth': post.author.username,
                       'Тестовый пост': post.text,
                       'Тестовая группа': post.group.title,
                       self.image: post.image.read(),
                       self.uploaded_image.size: post.image.size, }

            for expected_context, test_context in context.items():
                with self.subTest(expected_context=expected_context):

                    self.assertEqual(expected_context, test_context)

    def test_profile_and_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформируется с правильным
        контекстом.
        """
        response = self.authorized_client.get(self.post_detail)

        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(response.context.get('post').group.title,
                         'Тестовая группа')
        self.assertEqual(response.context.get('post').image.read(),
                         self.image)

    def test_first_page_contains_ten_records(self):
        """Тест паджинатора. На первой странице выведется 10 постов."""
        for name in self.names:
            response = self.client.get(name)

        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_PER_PAGE)

    def test_second_page_contains_ten_or_three_records(self):
        """Тест паджинатора. На второй странице выведутся оставшиеся посты
        или 10, если общее число постов больше, чем 20.
        """
        for name in self.names:
            response = self.client.get(name + '?page=2')
            if name == reverse('posts:group_list',
                               kwargs={'slug': self.post.group.slug}):

                self.assertEqual(len(response.context['page_obj']), 3)
            else:
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)

    def test_post_in_its_own_group(self):
        """Посты с указанием группы выводятся только в своей группе."""
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test-slug-2',
                                      description='Тестовое описание 2')
        Post.objects.create(author=self.user,
                            group=group2,
                            text='Тестовый пост2',
                            image=self.uploaded_image, )

        rev = reverse('posts:group_list', kwargs={'slug': group2.slug})
        response = self.authorized_client.get(rev)
        test_post = response.context['page_obj'].object_list[0]
        context = {'Тестовый пост': test_post.text,
                   'Тестовая группа': test_post.group.title, }

        for expected_context, test_context in context.items():
            with self.subTest(expected_context=expected_context):

                self.assertNotEqual(expected_context, test_context)

    def test_cache(self):
        """Кеш работает корректно."""
        text = 'Пост для тестирвания корректной работы кэша.'

        new_post = Post.objects.create(author=self.user, text=text)
        req = self.authorized_client.get(self.index)
        content_with_new_post = req.content
        latest_post = req.context['page_obj'].object_list[0]

        self.assertEqual(new_post, latest_post)

        post_to_delete = Post.objects.get(author=self.user, text=text)

        post_to_delete.delete()
        cache_with_new_post = self.authorized_client.get(self.index).content

        self.assertEqual(content_with_new_post, cache_with_new_post)

        cache.clear()
        cache_without_post = self.authorized_client.get(self.index).content

        self.assertNotEqual(content_with_new_post, cache_without_post)

    def test_auth_user_can_follow_others(self):
        """Пользователь может добвлять в подписки других пользователей."""
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.not_author.username}))

        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.not_author).
                        exists())

    def test_auth_user_canunfollow_others(self):
        """Пользователь может добвлять в подписки других пользователей."""
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.not_author.username}))

        self.assertFalse(Follow.objects.filter(user=self.user,
                                               author=self.not_author).
                         exists())

    def test_following_authors_in_following_page(self):
        """Новая запись появится в ленте только у тех, кто подписан на
        автора."""
        author1 = User.objects.create(username='Author1')
        author2 = User.objects.create(username='Author2')
        text1 = 'Пост автора1'
        text2 = 'Пост автора2'

        author1_post = Post.objects.create(author=author1, text=text1)
        author2_post = Post.objects.create(author=author2, text=text2)
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': author1.username}))
        user_follow_index = self.authorized_client.get(
            reverse('posts:follow_index')).context['page_obj']

        self.assertIn(author1_post, user_follow_index)
        self.assertNotIn(author2_post, user_follow_index)

    def test_user_cant_follow_or_unfollow_himself(self):
        """Пользователь не сможет подписаться сам на себя."""
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        user_follow_index = self.authorized_client.get(
            reverse('posts:follow_index')).context['page_obj']

        self.assertNotIn(self.post, user_follow_index)
