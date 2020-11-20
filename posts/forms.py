from django import forms

from captcha.fields import CaptchaField

from .models import Post, Comment


class PostForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Краткость - сестра таланта',
            'group': 'Выберите сообщество для публикации',
            'image': 'Загрузить изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)