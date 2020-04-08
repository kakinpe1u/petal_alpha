from api.models import PetalObject
from django.db import models

from neomodel import (StructuredNode, StringProperty, IntegerProperty,
                      FloatProperty, BooleanProperty, StructuredRel,
                      DateTimeProperty, RelationshipTo, Relationship)
class Entity(PetalObject):
    name                     = StringProperty()
    sourceID                 = StringProperty()
    status                   = StringProperty()
    # node_id                  = StringProperty(index = True)
    uuid = StringProperty()

    # # Relationships
    # articles                 = RelationshipFrom('.article.Article', 'ARTICLE_OF')
    # species           = RelationshipFrom('.species.Species', 'SPECIES_OF')
    # entities                 = Relationship('.entity.Entity', None)

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj