from neomodel import (StructuredNode, StringProperty,
                      RelationshipTo, RelationshipFrom, Relationship)

class Entity(StructuredNode):
    name                     = StringProperty()
    sourceID                 = StringProperty()
    status                   = StringProperty()
    node_id                  = StringProperty(index = True)

    # Relationships
    articles                 = RelationshipFrom('.article.Article', 'ARTICLE_OF')
    species           = RelationshipFrom('.species.Species', 'SPECIES_OF')
    entities                 = Relationship('.entity.Entity', None)

class Article(StructuredNode):
    __abstract_node__ = True
    __label__ = "Article"

    summary = StringProperty()
    images = StringProperty()
    references = StringProperty()
    links = StringProperty()
    title = StringProperty()
    content = StringProperty()
    uuid = StringProperty()
    # node_id = StringProperty(index = True)

    # Relationships
    article = Relationship(".article.Article", None)
    species = RelationshipTo(".species.Species", "MENTIONS_IN_ARTICLE")

class WikipediaArticle(Article):
    __label__ = "WikipediaArticle"
    pass

class Species(StructuredNode):
    Order = StringProperty()
    CatalogSource = StringProperty()
    Phylum = StringProperty()
    Genus = StringProperty()
    Family = StringProperty()
    Class = StringProperty()
    Name = StringProperty(required = True)
    node_id = StringProperty(index = True)

    # Relationships (edges
    species = Relationship(".species.Species", None)
    articles = RelationshipTo(".article.Article", "MENTIONS_SPECIES")