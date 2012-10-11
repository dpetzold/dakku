import unittest

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.db import models
from dakku.fields import RandomCharField

class RandomCharTestModel(models.Model):
    chars = RandomCharField(length=12)

class RandomCharTestModelAlpha(models.Model):
    chars = RandomCharField(length=12, alpha_only=True)

class RandomCharTestModelDigits(models.Model):
    chars = RandomCharField(length=12, digits_only=True)

class RandomCharTestModelPunctuation(models.Model):
    chars = RandomCharField(length=12, include_punctuation=True)

class RandomCharTestModelLower(models.Model):
    chars = RandomCharField(length=12, lower=True, alpha_only=True)

class RandomCharTestModelLowerAlphaDigits(models.Model):
    chars = RandomCharField(length=12, lower=True, include_punctuation=False)


class RandomCharFieldTest(unittest.TestCase):

    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('dakku.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        RandomCharTestModel.objects.all().delete()
        settings.INSTALLED_APPS = self.old_installed_apps

    def testRandomCharField(self):
        m = RandomCharTestModel()
        m.save()
#        print(m.chars)
        self.assertEqual(len(m.chars), 12)

    def testRandomCharFieldLower(self):
        m = RandomCharTestModelLower()
        m.save()
#        print(m.chars)
        for c in m.chars:
            if c.isalpha():
                self.assertTrue(c.islower())

    def testRandomCharFieldAlpha(self):
        m = RandomCharTestModelAlpha()
        m.save()
#        print(m.chars)
        for c in m.chars:
            self.assertTrue(c.isalpha())

    def testRandomCharFieldDigits(self):
        m = RandomCharTestModelDigits()
        m.save()
#        print(m.chars)
        for c in m.chars:
            self.assertTrue(c.isdigit())

    def testRandomCharFieldPunctuation(self):
        m = RandomCharTestModelPunctuation()
        m.save()
#        print(m.chars)
        self.assertEqual(len(m.chars), 12)

    def testRandomCharTestModelLowerAlphaDigits(self):
        m = RandomCharTestModelLowerAlphaDigits()
        m.save()
#        print(m.chars)
        for c in m.chars:
            self.assertTrue(c.isdigit() or (c.isalpha() and c.islower()))
