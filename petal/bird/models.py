from api.models import PetalObject, get_time

from neomodel import (StructuredNode, StringProperty, IntegerProperty,
                    FloatProperty, BooleanProperty, StructuredRel,
                    DateTimeProperty, RelationshipTo, Relationship)

class Impression(StructuredRel):
    viewed = DateTimeProperty(default = get_time)
    view_count = IntegerProperty(default = 0)

class ResultRel(StructuredRel):
    date_accessed = DateTimeProperty()


class KeyWordRel(StructuredRel):
    relevance = FloatProperty(default = 0)

class KeyWord(StructuredNode):
    keyword = StringProperty()
    weight = IntegerProperty(default = 0)

    # relationships
    queries = RelationshipTo('search.models.Query', 'SEARCH_QUERY')

class Result(PetalObject):
    result_id = StringProperty(unique_index = True)
    object_type = StringProperty()

    # relationships
    queries = RelationshipTo('search.models.Query', 'QUERY')
    clicked_by = RelationshipTo('users.models.User', 'ACCESSED_BY',
                                model = ResultRel)

class Query(StructuredNode):
    weight = IntegerProperty(default = 0)
    search_query = StringProperty(unique_index = True)
    search_count = IntegerProperty(default = 1)
    last_searched = DateTimeProperty(default = get_time)
    trending = BooleanProperty(default = False)

    # relationships
    searched_by = Relationship('users.models.User', 'SEARCHED_BY')
    keywords = RelationshipTo(KeyWord, 'KEYWORDS', model = KeyWordRel)
    results = RelationshipTo(Result, 'RESULT')

class Searchable(PetalObject):
    search_id = StringProperty()
    populated_es_index = BooleanProperty(default = False)
    view_count = IntegerProperty(default = 0)
    summary = StringProperty()

    # relationships
    viewed_by = RelationshipTo('users.models.User', "VIEWED_BY",
                               model = Impression)

    def get_search_count(self):
        return self.search_count

    def increment_search_count(self):
        try:
            if self.search_count >= 4611686018427387900:
                return 4611686018427387900
            self.search_count += 1
            self.save()
            return self.search_count
        except IndexError:
            return 0