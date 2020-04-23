import pytz
from datetime import datetime, timedelta, date

from neomodel import DoesNotExist
from neo4j import CypherError

from api.utils import generate_job
from petalusers.models import PetalUser
from django.conf import settings
from django.contrib.auth.models import User


def create_user_util_test(email, first_name="test", last_name="test",
                          password="test_test", birthday=None, task=False):
    from petalusers.serializers import generate_username

    if birthday is None:
        birthday = datetime.now(pytz.utc) - timedelta(days=18 * 365)
    try:
        user = User.objects.get(email=email)
        username = user.username
    except User.DoesNotExist:
        username = generate_username(first_name, last_name)
        user = User.objects.create_user(first_name=first_name,
                                        last_name=last_name,
                                        email=email, password=password,
                                        username=username)
        user.save()
    try:
        petaluser = PetalUser.get(username=user.username, cache_buster=True)
    except (PetalUser.DoesNotExist, DoesNotExist):
        try:
            petaluser = PetalUser(email=user.email, first_name=user.first_name,
                                  last_name=user.last_name, username=user.username,
                                  date_of_birth=birthday)
            petaluser.save()
        except(CypherError, IOError):
            return False
    except(CypherError, IOError):
        raise False
    return petaluser
