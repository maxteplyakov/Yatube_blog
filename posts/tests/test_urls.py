from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post


User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

    def test_homepage(self):
        response = self.unauthorized_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        response = self.authorized_client.get(reverse('new_post'))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        current_post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('new_post'), {'text': 'Это текст публикации'}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_post_count + 1)

    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.get(reverse('new_post'))
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse('new_post'),
            status_code=302, target_status_code=200
        )

    def test_profile_page(self):
        response = self.authorized_client.get('/%s/' % (self.user.username))
        self.assertEqual(response.status_code, 200)

    def test_404(self):
        response = self.unauthorized_client.get('/urls_that_does_not_exist/')
        self.assertEqual(response.status_code, 404)