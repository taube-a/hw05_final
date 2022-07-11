from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()


class PostsURLTest(TestCase):
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
        cls.nonauthor = User.objects.create_user(username='nonauthor')
        cls.index_url = '/'
        cls.group_list_url = f'/group/{cls.post.group.slug}/'
        cls.profile_url = f'/profile/{cls.post.author.username}/'
        cls.post_detail_url = f'/posts/{cls.post.pk}/'
        cls.create_url = '/create/'
        cls.add_comment_url = f'/posts/{cls.post.pk}/comment/'
        cls.post_edit_url = f'/posts/{cls.post.pk}/edit/'
        cls.follow_url = f'/profile/{cls.post.author.username}/follow/'
        cls.unfollow_url = f'/profile/{cls.post.author.username}/unfollow/'

        cls.URLS_for_test = {cls.index_url: 'posts/index.html',
                             cls.group_list_url: 'posts/group_list.html',
                             cls.profile_url: 'posts/profile.html',
                             cls.post_detail_url: 'posts/post_detail.html', }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.nonauthor_client = Client()
        self.nonauthor_client.force_login(self.nonauthor)

    def test_public_pages(self):
        """Проверит доступность публичных страниц."""
        for url in self.URLS_for_test:
            with self.subTest(field=url):
                response = self.guest_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_correct_template(self):
        """Проверит шаблоны для публичных адресов."""
        for url, template_name in self.URLS_for_test.items():
            with self.subTest(field=url):
                response = self.guest_client.get(url)

                self.assertTemplateUsed(response, template_name)

    def test_create_url_redirect_anonymous_on_login(self):
        """Страница по адресу /cteate/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.create_url, follow=True)

        self.assertRedirects(response, f'/auth/login/?next={self.create_url}')

    def test_edit_url_redirect_nonauthor_on_post_detail(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит неавтора
         поста на страницу поста.
        """
        response = self.nonauthor_client.get(self.post_edit_url, follow=True)

        self.assertRedirects(response, self.post_detail_url)

    def test_edit_url_redirect_guest_on_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.post_edit_url,
                                         follow=True)

        self.assertRedirects(response,
                             f'/auth/login/?next={self.post_edit_url}')

    def test_add_comment_url_redirect_anonymous_on_login(self):
        """Страница по адресу posts/<int:pk>/comment/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.add_comment_url, follow=True)

        self.assertRedirects(response,
                             f'/auth/login/?next={self.add_comment_url}')

    def test_add_comment_url_redirect_user_on_post_detail(self):
        """Страница по адресу posts/<int:pk>/comment/ перенаправит
        пользователя на страницу поста после отправки комментария.
        """
        response = self.nonauthor_client.get(self.add_comment_url,
                                             follow=True)

        self.assertRedirects(response, self.post_detail_url)

    def test_strange_url_return_404(self):
        """Несуществующая страница вернёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_add_comment_url_redirect_anonymous_on_login(self):
        """Страницы profile/<str:username>/follow/ и
        profile/<str:username>/unfollow/ перенаправят анонимного
        пользователя на страницу логина.
        """
        un_follow_urls = (self.follow_url, self.unfollow_url)

        for url in un_follow_urls:
            response = self.guest_client.get(url, follow=True)
            self.assertRedirects(response,
                                 f'/auth/login/?next={url}')

    def test_add_comment_url_redirect_anonymous_on_login(self):
        """Страница по адресу posts/<int:pk>/comment/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.add_comment_url, follow=True)

        self.assertRedirects(response, f'/auth/login/?next='
                                       f'{self.add_comment_url}')
