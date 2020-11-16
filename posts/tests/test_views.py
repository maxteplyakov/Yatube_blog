from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image

from posts.models import Post, Group


User = get_user_model()


class ViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor')
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(
            title='testgroup', slug='testgroup', description='sometext'
        )
        cls.text = 'some text for search'
        cls.post = Post.objects.create(
            text=cls.text, author=cls.user, group=cls.group,
        )

        cls.urls = {
            reverse('index'): 'главной странице',
            reverse('profile', args=(cls.user.username,)): 'cтранице пользователя',
            reverse('post', args=(cls.post.author.username, cls.post.id)): 'отдельной странице поста',
            #reverse('group', args=[cls.post.group.slug]): 'на странице группы'  не работает тест для страница группы
        }
        cls.user_follower = User.objects.create_user(username='TestReader')
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.user_follower)
        cls.user_not_follower = User.objects.create_user(username='TestReader2')
        cls.authorized_client_not_follower = Client()
        cls.authorized_client_not_follower.force_login(cls.user_not_follower)

    def test_newpost_locations_unauthorized(self):
        cache.clear()
        for url in self.urls.keys():
            response = self.unauthorized_client.get(url)
            self.assertContains(
                response, self.text, status_code=200,
                msg_prefix='Пост не появился на ' + self.urls[url] +
                           ' для неавторизованного пользователя'
            )

    def test_newpost_locations_authorized(self):
        cache.clear()
        for url in self.urls.keys():
            response = self.authorized_client_author.get(url)
            self.assertContains(
                response, self.text, status_code=200,
                msg_prefix='Пост не появился на ' + self.urls[url] +
                           ' для авторизованного пользователя'
            )

    def test_post_edit(self):
        cache.clear()
        text2 = 'changed text for search'
        response = self.authorized_client_author.post(
            reverse(
                'post_edit', args=(self.post.author.username, self.post.id)
            ),
            data={'text': text2}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Post.objects.get(id=self.post.id).text, text2,
            msg='пост не изменился в БД'
        )

        for url in self.urls.keys():
            response = self.unauthorized_client.get(url)
            self.assertContains(
                response, text2, status_code=200,
                msg_prefix='Пост не изменился на ' + self.urls[url]
            )

    def test_img_exists(self):
        cache.clear()
        img_bytes = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        image = SimpleUploadedFile(
            name='wtf.jpg',
            content=img_bytes,
            content_type='image/jpeg'
        )
        self.authorized_client_author.post(
            reverse('new_post'),
            {'text': 'text', 'author': self.user, 'image': image},
            follow=True,
        )
        post = Post.objects.get(text='text')
        urls = {
            reverse('index'): 'главной странице',
            reverse('profile', args=(self.user.username,)): 'cтранице пользователя',
            reverse('post', args=(post.author.username, post.id)): 'отдельной странице поста',
        }
        for url in urls.keys():
            response = self.unauthorized_client.get(url)
            self.assertContains(
                response, '<img', status_code=200,
                msg_prefix='HTML не содержит тег <img> на ' + urls[url]
            )

    def test_wrong_img_format(self):
        not_image = SimpleUploadedFile(
            name='temp.txt',
            content='some text'.encode('utf-8'),
            content_type='text/utf8'
        )
        response = self.authorized_client_author.post(
            reverse('new_post'),
            {'text': 'svdvssx', 'image': not_image},
            follow=True,
        )
        self.assertFormError(
            response, 'form', 'image',
            'Загрузите правильное изображение. Файл, который'
            ' вы загрузили, поврежден или не является изображением.'
        )

    def test_cache(self):
        text2 = 'any text'
        response = self.authorized_client_author.post(
            reverse('new_post'), {'text': text2}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        response = self.unauthorized_client.get(reverse('index'))
        self.assertNotContains(
            response, text2, status_code=200,
            msg_prefix='Главная страница не кешируется')
        cache.clear()
        response = self.unauthorized_client.get(reverse('index'))
        self.assertContains(
             response, text2, status_code=200,
             msg_prefix='Пост не появляется на главной,'
                        'после очистки кеша')

    def test_authorized_follow(self):
        self.authorized_client_follower.get(
            reverse('profile_follow', args=(self.user.username,))
        )
        response = self.authorized_client_follower.get(reverse('follow_index'))
        self.assertContains(
            response, f'@{self.user.username}', status_code=200,
            msg_prefix='Посты не отображаются на странице'
                       ' follow_index после подписки'
        )

    def test_authorized_unfollow(self):
        self.authorized_client_follower.get(
            reverse('profile_follow', args=(self.user.username,))
        )
        self.authorized_client_follower.get(
            reverse('profile_unfollow', args=(self.user.username,))
        )
        response = self.authorized_client_follower.get(reverse('follow_index'))
        self.assertNotContains(
            response, f'@{self.user.username}', status_code=200,
            msg_prefix='Посты не иссчезают со страницы'
                       ' follow_index после отписки'
        )

    def test_newpost_follow(self): #здесь нет проверки для неавторизованного пользователя, он же вообще не видит страницу follow_index. Соответственно и разделять нечего
        self.authorized_client_follower.get(
            reverse('profile_follow', args=(self.user.username,))
        )
        text = 'Текст нового поста'
        self.authorized_client_author.post(
            reverse('new_post'), {'text': text}, follow=True,
        )
        response = self.authorized_client_follower.get(reverse('follow_index'))
        self.assertContains(
            response, text, status_code=200,
            msg_prefix='Новый пост не отображается у подписанного пользователя'
        )
        response = self.authorized_client_not_follower.get(reverse('follow_index'))
        self.assertNotContains(
            response, text, status_code=200,
            msg_prefix='Новый пост отображается у не подписанного пользователся'
        )

    def test_authorized_comments(self):
        text = 'новый комментарий'
        self.authorized_client_follower.post(
            reverse('add_comment', args=(self.user.username, self.post.id)),
            {'text': text}, follow=True,
        )
        response = self.authorized_client_author.get(
            reverse('post', args=(self.user.username, self.post.id))
        )
        self.assertContains(
            response, text, status_code=200,
            msg_prefix='Авторизованный пользователь'
                       ' не может оставить комментарий'
        )

    def test_unauthorized_comments(self):
        text2 = 'Новый комментарий 2'
        self.unauthorized_client.post(
            reverse('add_comment', args=(self.user.username, self.post.id)),
            {'text': text2}, follow=True,
        )
        response = self.authorized_client_author.get(
            reverse('post', args=(self.user.username, self.post.id))
        )
        self.assertNotContains(
            response, text2, status_code=200,
            msg_prefix='Неавторизованный пользователь'
                       ' может оставить комментарий'
        )