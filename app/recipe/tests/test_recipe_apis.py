from django.test import TestCase
from rest_framework import status
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
from decimal import Decimal

import tempfile, os
from PIL import Image

RECIPE_URL = reverse('recipe:recipe-list')

def image_upload_url(recipe_id):
     return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, title='Sample title'):
    return Recipe.objects.create(user = user,
                                 title = title,
                                 time_minutes = 5,
                                 price = Decimal('5.50'),
                                 description = 'New description.',)
 

class RecipeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@email.com', password='pass123', name='Test Name')
        self.recipe = Recipe.objects.create(user = self.user,
                                            title = 'Sample recipe name',
                                            time_minutes = 5,
                                            price = Decimal('5.50'),
                                            description = 'Sample recipe description.',)
        self.client = APIClient()

    def test_should_not_list_recipes_if_user_is_not_looged_in(self):
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test2@email.com', password='pass123', name='Test Name')
        self.recipe = Recipe.objects.create(user = self.user,
                                            title = 'Sample recipe name',
                                            time_minutes = 5,
                                            price = Decimal('5.50'),
                                            description = 'Sample recipe detail.',)
        self.client = APIClient()
        self.client.force_authenticate(user = self.user)
        
    def test_should_list_user_recipes(self):
        res = self.client.get(RECIPE_URL)

        serializer_data = RecipeSerializer(Recipe.objects.all().order_by('-id'), many=True)

        self.assertEqual(res.data, serializer_data.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_should_only_list_recipes_of_the_logged_in_user(self):
        new_user = get_user_model().objects.create_user(email='test@email.com', password='pass123', name='Test Name')
        new_recipe = Recipe.objects.create(user = new_user,
                                           title = 'New name',
                                           time_minutes = 5,
                                           price = Decimal('5.50'),
                                           description = 'New description.',)
        
        res = self.client.get(RECIPE_URL)
    
        self.assertNotIn(new_recipe, res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_should_show_a_recipe_detail(self):
        url = reverse('recipe:recipe-detail', args=[self.recipe.id])
        res = self.client.get(url)

        serializer_data = RecipeDetailSerializer(self.recipe)

        self.assertEqual(res.data, serializer_data.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_should_create_recipe(self):
        payload = {
            'title': 'Sample name',
            'time_minutes': 5,
            'price': Decimal('5.50'),
            'description': 'Sample description.',
            'link': 'ttttttt'
        }

        res = self.client.post(RECIPE_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)

    def test_should_not_delete_other_user_recipe(self):
        new_user = get_user_model().objects.create_user(email='test@email.com', password='pass123', name='Test Name')
        new_recipe = Recipe.objects.create(user = new_user,
                                           title = 'New name',
                                           time_minutes = 5,
                                           price = Decimal('5.50'),
                                           description = 'New description.',)
        url = reverse('recipe:recipe-detail', args=[new_recipe.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=new_recipe.id).exists())
    
    def test_create_recipe_with_new_tags(self):
         """Test creating a recipe with new tags."""
         payload = {
             'title': 'Thai Prawn Curry',
             'time_minutes': 30,
             'price': Decimal('2.50'),
             'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
             'description': 'test test test',
             'link': 'ttttttt'
         }
         res = self.client.post(RECIPE_URL, payload, format='json')

         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
         recipes = Recipe.objects.filter(user=self.user)
         self.assertEqual(recipes.count(), 2)
         recipe = recipes[1]
         self.assertEqual(recipe.tags.count(), 2)
         for tag in payload['tags']:
             exists = recipe.tags.filter(
                 name=tag['name'],
                 user=self.user,
             ).exists()
             self.assertTrue(exists)
 
    def test_create_recipe_with_existing_tags(self):
         """Test creating a recipe with existing tag."""
         tag_indian = Tag.objects.create(user=self.user, name='Indian')
         payload = {
             'title': 'Pongal',
             'time_minutes': 60,
             'price': Decimal('4.50'),
             'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
             'description': 'test test test',
             'link': 'ttttttt'
         }
         res = self.client.post(RECIPE_URL, payload, format='json')

         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
         recipes = Recipe.objects.filter(user=self.user)
         self.assertEqual(recipes.count(), 2)
         recipe = recipes[1]
         self.assertEqual(recipe.tags.count(), 2)
         self.assertIn(tag_indian, recipe.tags.all())
         for tag in payload['tags']:
             exists = recipe.tags.filter(
                 name=tag['name'],
                 user=self.user,
             ).exists()
             self.assertTrue(exists)

    def test_update_recipe_assign_tag(self):
         """Test assigning an existing tag when updating a recipe."""
         tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
         self.recipe.tags.add(tag_breakfast)
 
         tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
         payload = {'tags': [{'name': 'Lunch'}]}
         url = url = reverse('recipe:recipe-detail', args=[self.recipe.id])
         res = self.client.patch(url, payload, format='json')
 
         self.assertEqual(res.status_code, status.HTTP_200_OK)
         self.assertIn(tag_lunch, self.recipe.tags.all())
         self.assertNotIn(tag_breakfast, self.recipe.tags.all())
 
    def test_clear_recipe_tags(self):
        tag = Tag.objects.create(user=self.user, name='Dessert')
        self.recipe.tags.add(tag)

        payload = {'tags': []}
        url = url = reverse('recipe:recipe-detail', args=[self.recipe.id])
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
         payload = {
             'title': 'Cauliflower Tacos',
             'time_minutes': 60,
             'price': Decimal('4.30'),
             'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
             'description': 'test test test',
             'link': 'ttttttt'
         }
         res = self.client.post(RECIPE_URL, payload, format='json')

         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
         recipes = Recipe.objects.filter(user=self.user)
         self.assertEqual(recipes.count(), 2)
         recipe = recipes[1]
         self.assertEqual(recipe.ingredients.count(), 2)
         for ingredient in payload['ingredients']:
             exists = recipe.ingredients.filter(
                 name=ingredient['name'],
                 user=self.user,
             ).exists()
             self.assertTrue(exists)
 
    def test_create_recipe_with_existing_ingredient(self):
        Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 25,
            'price': '2.55',
            'ingredients': [{'name': 'Lemon'}, {'name': 'Fish Sauce'}],
            'description': 'test test test',
            'link': 'ttttttt'
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ingredient.objects.all().count(), 2)

    def test_create_ingredient_on_update(self):
         payload = {'ingredients': [{'name': 'Limes'}]}
         url = reverse('recipe:recipe-detail', args=[self.recipe.id])
         res = self.client.patch(url, payload, format='json')
 
         self.assertEqual(res.status_code, status.HTTP_200_OK)
         new_ingredient = Ingredient.objects.get(user=self.user, name='Limes')
         self.assertIn(new_ingredient, self.recipe.ingredients.all())
 
    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        self.recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        payload = {'ingredients': [{'name': 'Chili'}]}
        url = reverse('recipe:recipe-detail', args=[self.recipe.id])
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, self.recipe.ingredients.all())
        self.assertNotIn(ingredient1, self.recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Garlic')
        self.recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = reverse('recipe:recipe-detail', args=[self.recipe.id])
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
         r1 = create_recipe(user=self.user, title='Thai Vegetable Curry')
         r2 = create_recipe(user=self.user, title='Aubergine with Tahini')
         tag1 = Tag.objects.create(user=self.user, name='Vegan')
         tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
         r1.tags.add(tag1)
         r2.tags.add(tag2)
         r3 = create_recipe(user=self.user, title='Fish and chips')
 
         params = {'tags': f'{tag1.id},{tag2.id}'}
         res = self.client.get(RECIPE_URL, params)
 
         s1 = RecipeSerializer(r1)
         s2 = RecipeSerializer(r2)
         s3 = RecipeSerializer(r3)
         self.assertIn(s1.data, res.data)
         self.assertIn(s2.data, res.data)
         self.assertNotIn(s3.data, res.data)
 
    def test_filter_by_ingredients(self):
        r1 = create_recipe(user=self.user, title='Posh Beans on Toast')
        r2 = create_recipe(user=self.user, title='Chicken Cacciatore')
        in1 = Ingredient.objects.create(user=self.user, name='Feta Cheese')
        in2 = Ingredient.objects.create(user=self.user, name='Chicken')
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        r3 = create_recipe(user=self.user, title='Red Lentil Daal')

        params = {'ingredients': f'{in1.id},{in2.id}'}
        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

class ImageUploadTests(TestCase):
 
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = Recipe.objects.create(user = self.user,
                                           title = 'New name',
                                           time_minutes = 5,
                                           price = Decimal('5.50'),
                                           description = 'New description.',)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

