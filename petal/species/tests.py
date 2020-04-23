from uuid import uuid1
from django.test import TestCase
from django.contrib.auth.models import User

from neomodel import db

from species.models import Species
from articles.models import Article


class TestSpeciesModel(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.species = Species(object_uuid=str(uuid1()),
                               name=str(uuid1())).save()

    def test_get_article_mentions(self):
        self.species.get_article_mentions()

