from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug',
                                         description='Тестовое описание', )
        cls.post = Post.objects.create(author=cls.user,
                                       text='Lorem ipsum dolor sit amet,'
                                            'consectetur adipiscing elit.'
                                            'Fusce sodales tortor et nulla '
                                            'vehicula consequat.')

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""
        post = self.post
        group = self.group
        models_for_test = {post: post.text[:15],
                           group: group.title, }
        for model, expected_meaning in models_for_test.items():
            with self.subTest(field=model):
                self.assertEqual(str(model), expected_meaning)
