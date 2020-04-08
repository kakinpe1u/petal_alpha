from api.models import PetalObject, get_time

from neomodel import (StructuredNode, StringProperty, IntegerProperty,
                      FloatProperty, BooleanProperty, StructuredRel,
                      DateTimeProperty, RelationshipTo, Relationship)


class Impression(StructuredRel):
    viewed = DateTimeProperty(default=get_time)
    view_count = IntegerProperty(default=0)


class ResultRel(StructuredRel):
    date_accessed = DateTimeProperty()


class KeywordRel(StructuredRel):
    relevance = FloatProperty(default=0)


class Keyword(StructuredNode):
    keyword = StringProperty()
    weight = IntegerProperty(default=0)

    # relationships
    queries = RelationshipTo('bird.models.Query', 'SEARCH_QUERY')


class Result(PetalObject):
    result_id = StringProperty(unique_index=True)
    object_type = StringProperty()

    # relationships
    queries = RelationshipTo('bird.models.Query', 'QUERY')
    clicked_by = RelationshipTo('petalusers.models.PetalUser', 'ACCESSED_BY',
                                model=ResultRel)


class Query(StructuredNode):
    weight = IntegerProperty(default=0)
    search_query = StringProperty(unique_index=True)
    search_count = IntegerProperty(default=1)
    last_searched = DateTimeProperty(default=get_time)
    trending = BooleanProperty(default=False)

    # relationships
    searched_by = Relationship('petalusers.models.PetalUser', 'SEARCHED_BY')
    keywords = RelationshipTo(Keyword, 'KEYWORDS', model=KeywordRel)
    results = RelationshipTo(Result, 'RESULT')


class Searchable(PetalObject):
    search_id = StringProperty()
    populated_es_index = BooleanProperty(default=False)
    view_count = IntegerProperty(default=0)
    summary = StringProperty()

    # relationships
    viewed_by = RelationshipTo('petalusers.models.PetalUser', "VIEWED_BY",
                               model=Impression)

    def get_search_count(self):
        return self.search_count

# ensure the view count doesn't get too big
    def increment_search_count(self):
        try:
            if self.search_count >= 9223372036854775807:
                return 9223372036854775807
            self.search_count += 1
            self.save()
            return self.search_count
        except IndexError:
            return 0
