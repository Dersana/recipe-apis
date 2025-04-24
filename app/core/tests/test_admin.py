from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

class AdminTests(TestCase):  # Fixed 'def' to 'class'
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(email='admin@example.com', password='password')  # Fixed typo in email
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(email='user@email.com', password='password111', name='Test User')  # Removed duplicate user creation

    def test_users_list(self):
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.user.email)

    def test_can_create_user(self):
        url = reverse('admin:core_user_add')
        res = self.client.post(url, {
            'email': 'abc@gmail.com',
            'name': 'Test Name',
            'password': 'password123'
        })
        last_user = get_user_model().objects.last()

        self.assertEqual(res.status_code, 302)
        self.assertEqual(last_user.email, 'abc@gmail.com')
