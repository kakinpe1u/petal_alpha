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
        self.species = Species(content='test content',
                               object_uuid=str(uuid1()),
                               name=str(uuid1())).save()