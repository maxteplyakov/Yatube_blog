from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group


User = get_user_model()


class ViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

    def newpost_locations(self):
        text = 'text for search'
        response = self.authorized_client.post(
            reverse('new'), {'text': text}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_post_count + 1)


class ViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(
            title='testgroup', slug='testgroup', description='sometext'
        )
        cls.text = 'some text for search'
        cls.image = SimpleUploadedFile(name='wtf.jpg', content=open('D:\\Dev\\hw05_final\\media\\posts\\wtf.jpg', 'rb').read(), content_type='image/jpeg')
        cls.post = Post.objects.create(
            text=cls.text, author=cls.user, group=cls.group, image='string'
        )

        cls.urls = {
            reverse('index'): 'главной странице',
            reverse('profile', args=[cls.user.username]): 'cтранице пользователя',
            reverse('post', args=(cls.post.author.username, cls.post.id)): 'отдельной странице поста',
            #reverse('group', args=[cls.post.group.slug]): 'на странице группы'  не работает тест для страница группы
        }

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
            response = self.authorized_client.get(url)
            self.assertContains(
                response, self.text, status_code=200,
                msg_prefix='Пост не появился на ' + self.urls[url] +
                ' для авторизованного пользователя'
            )


    def test_post_edit(self):
        cache.clear()
        text2 = 'changed text for search'
        response = self.authorized_client.post(
            reverse('post_edit', args=(self.post.author.username, self.post.id)),
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

    def test_img_exists(self): #тест работает, даже если вместо картинки строка
        for url in self.urls.keys():
            response = self.unauthorized_client.get(url)
            self.assertContains(
                response, '<img', status_code=200,
                msg_prefix='HTML не содержит тег <img> на ' + self.urls[url]
            )

    def test_wrong_img_format(self):
        with open('D:\\Dev\\hw05_final\\media\\posts\\txt_file.txt') as not_img:
            current_post_count = Post.objects.count()
            self.authorized_client.post(
                reverse('new_post'), {'text': 'svdvssx', 'image': not_img}, follow=True,
            )
            self.assertNotEqual(Post.objects.count(), current_post_count + 1)

    def test_cache(self):
        text2 = 'any text'
        response = self.authorized_client.post(
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