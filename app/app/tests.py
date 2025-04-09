from django.test import SimpleTestCase

from app import calc

class CalcTests(SimpleTestCase):

    def test_add_nos(self):
        res = calc.add(5, 4)
        self.assertEqual(res, 9)

    def test_subtract_nos(self):
        res = calc.sub(5, 4)
        self.assertEqual(res, 1)