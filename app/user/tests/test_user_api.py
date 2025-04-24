from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
PROFILE_URL = reverse('user:me')

class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_created_successfully(self):
        payload = {
            'email': 'test@email.com',
            'password': 'pass123rtyui',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.all()[0].email, payload['email'])

    def test_user_email_is_unique(self):
        get_user_model().objects.create_user(email='test@email.com', password='pass123', name='Test Name')

        payload = {
            'email': 'test@email.com',
            'password': 'pass12344',
            'name': 'Test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_strength(self):
        payload = {
            'email': 'test@email.com',
            'password': 'pas',
            'name': 'Test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(get_user_model().objects.filter(email=payload['email']).exists())

    def test_user_get_token(self):
        user_data = {
            'email': 'test@email.com',
            'password': 'password1234567',
            'name': 'Test'
        }

        get_user_model().objects.create_user(**user_data)

        payload = { 'email': user_data['email'], 'password': user_data['password'] }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)


    def test_token_creation_fails_for_wrong_password(self):
        user_data = {
            'email': 'test@email.com',
            'password': 'password1234567',
            'name': 'Test'
        }

        get_user_model().objects.create_user(**user_data)

        payload = { 'email': user_data['email'], 'password': 'wwwww' }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

class PrivateUserTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@email.com', password='password1234567', name='Test Name')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_user_can_view_profile(self):
        res = self.client.get(PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_can_update_profile(self):
        user_data = { 'name': 'Test' }

        res = self.client.patch(PROFILE_URL, user_data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, user_data['name'])
