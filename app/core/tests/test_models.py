from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch

from core import models

class ModelTests(TestCase):
    def test_user_is_created(self):
        email = 'test@example.com'
        password = 'qwerety12345'
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_email_is_normalized(self):
        sample_emails = [
            ['test@EXAMPLe.com', 'test@example.com'],
            ['test2@EXAMPLe.com', 'test2@example.com']
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample12')
            self.assertEqual(user.email, expected)

    def test_invalid_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'sample12')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser('test@email.com', '123swe')

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(email='test@email.com', password='qwert123456', name='Test User')

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description.',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_ingredient(self):
        user = get_user_model().objects.create_user(email='test@email.com', password='qwert123456', name='Test User')

        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Sample ingredient name',
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test-123-test'
        mock_uuid.return_value = uuid
        file_path = models.recipe_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
