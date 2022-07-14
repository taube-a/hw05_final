from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'group', 'image', )
        help_texts = {'title': 'Заголовок Вашего поста',
                      'text': 'Текст Вашего поста',
                      'group': 'Сообщество, к которому относится Ваш пост',
                      'image': 'Изображение к Вашему посту', }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        help_texts = {'text': 'Текст Вашего комментария', }
