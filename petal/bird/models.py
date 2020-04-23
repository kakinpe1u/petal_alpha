from django.utils.text import slugify
from django.core.cache import cache
from rest_framework.reverse import reverse

from neomodel import (db, StringProperty, IntegerProperty)

from content.models import PetalContent


class BirdSolution(PetalContent):
    table = StringProperty(default='public_solutions')
    action_name = StringProperty(default="offered a solution to your query")
    parent_id = StringProperty()


    # def get_url(self, request=None):
    #     from sb_questions.neo_models import Question
    #     question = Question.get(object_uuid=self.parent_id)
    #     return reverse('question_detail_page',
    #                    kwargs={'question_uuid': self.parent_id,
    #                            'slug': slugify(question.title)},
    #                    request=request)

    @classmethod
    def get_article(cls, object_uuid, request=None):
        from articles.models import Article
        from articles.serializers import ArticleSerializer
        article = cache.get("%s_article" % object_uuid)
        if article is None:
            query = 'MATCH (solution:BirdSolution {object_uuid:"%s"})<-' \
                    '[:POSSIBLE_ANSWER]-(species:Species)' \
                    '<-[:ASSOCIATED_WITH]-' \
                    '(article:Article) RETURN article' % object_uuid
            res, _ = db.cypher_query(query)
            if res.one:
                article = ArticleSerializer(
                    Article.inflate(res.one), context={"request": request}).data
                cache.set("%s_article" % object_uuid, article)
        return article

    @classmethod
    def get_mission(cls, object_uuid, request=None):
        from articles.models import Article
        from articles.serializers import ArticleSerializer
        mission = cache.get("%s_mission" % object_uuid)
        if mission is None:
            query = 'MATCH (solution:BirdSolution {object_uuid:"%s"})<-' \
                    '[:POSSIBLE_ANSWER]-(question:Question)' \
                    '<-[:ASSOCIATED_WITH]-' \
                    '(mission:Mission) RETURN mission' % object_uuid
            res, _ = db.cypher_query(query)
            if res.one:
                mission = MissionSerializer(
                    Mission.inflate(res.one), context={"request": request}).data
                cache.set("%s_mission" % object_uuid, mission)
        return mission