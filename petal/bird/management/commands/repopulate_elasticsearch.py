import logging

from django.core.management.base import BaseCommand

from neomodel import db

from petalusers.models import PetalUser
# from sb_questions.neo_models import Question
from bird.tasks import update_query_object

log = logging.getLogger(__name__)


class Command(BaseCommand):
    args = 'None.'

    def repopulate_elasticsearch(self):
        # Profiles
        skip = 0
        while True:
            query = 'MATCH (profile:PetalUser) RETURN DISTINCT profile ' \
                    'SKIP %s LIMIT 25' % skip
            skip += 24
            result, _ = db.cypher_query(query)
            if not result.one:
                break

    def handle(self, *args, **options):
        self.repopulate_elasticsearch()
        log.info("Completed elasticsearch repopulation")
