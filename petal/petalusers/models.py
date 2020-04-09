import pytz
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static

from neomodel import (StructuredNode, StringProperty, IntegerProperty,
                      DateTimeProperty, RelationshipTo,
                      StructuredRel, BooleanProperty,
                      DoesNotExist, db)

from api.models import PetalObject, RelationshipWeight
from bird.models import Searchable, Impression


def get_current_time():
    return datetime.now(pytz.utc)


class SearchCount(StructuredRel):
    times_searched = IntegerProperty(default=1)
    last_searched = DateTimeProperty(default=lambda: datetime.now(pytz.utc))

# class OauthUser(PetalObject):
#     web_address = StringProperty(default=settings.WEB_ADDRESS + '/o/token/')
#     access_token = StringProperty()
#     expires_in = IntegerProperty()
#     refresh_token = StringProperty()
#     last_modified = DateTimeProperty(default=get_current_time)
#     token_type = StringProperty(default="Bearer")


class PetalUser(Searchable):
    sex = StringProperty()
    # oauth_token = StringProperty()
    username = StringProperty(unique_index=True)
    first_name = StringProperty()
    last_name = StringProperty()
    middle_name = StringProperty()
    email = StringProperty(index=True)
    date_of_birth = DateTimeProperty()
    # profile_pic = StringProperty(default=get_default_profile_pic)
    is_admin = BooleanProperty(default=False)
    is_verified = BooleanProperty(default=True)
    search_index = StringProperty()
    employer = StringProperty()
    occupation = StringProperty()
    # base_index_id is the plebs id in the base search index
    base_index_id = StringProperty()
    email_verified = BooleanProperty(default=False)
    initial_verification_email_sent = BooleanProperty(default=False)

    searches = RelationshipTo('bird.models.Query', 'SEARCHED',
                              model=SearchCount)
    accessed_results = RelationshipTo('bird.models.Result',
                                      'ACCESSED_RESULT')

    @classmethod
    def get(cls, username, cache_buster=False):
        profile = None
        if username is None:
            return None
        if cache_buster is False:
            profile = cache.get(username)
        if profile is None or cache_buster:
            res, _ = db.cypher_query(
                "MATCH (a:%s {username:'%s'}) RETURN a" % (
                    cls.__name__, username))
            if res.one:
                res.one.pull()
                profile = cls.inflate(res.one)
            else:
                raise DoesNotExist('Profile with username: %s does not exist' % username)
            cache.set(username, profile)
        return profile

    def deactivate(self):
        pass
