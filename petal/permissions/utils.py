import pytz
import logging
from time import sleep
from datetime import datetime

from django.core.cache import cache
from neomodel import (DoesNotExist, db)
from neo4j import CypherError

from .models import Permission, PetalAction

log = logging.getLogger(__name__)


def manage_permission_relation(username):
    try:
        permissions = Permission.nodes.all()
    except(CypherError, IOError) as e:
        return e
    for permission in permissions:
        try:
            requirements = permission.check_requirements(username)
        except IOError as e:
            log.exception(e)
            sleep(1)
            continue
        current_time = datetime.now(pytz.utc)
        current_time = current_time.astimezone(pytz.utc)
        epoch_date = datetime(1970, 1, 1, tzinfo=pytz.utc)
        current_time = float((current_time - epoch_date).total_seconds())
        if not requirements:
            query = 'MATCH (petaluser:PetalUser {username: "%s"})-' \
                    '[r:HAS]->(permission:Permission {name: "%s"}) ' \
                    'SET r.active=false, r.lost_on=%s ' \
                    'WITH petaluser, permission ' \
                    'MATCH (petaluser)-[r_a:CAN]->(action:PetalAction) ' \
                    'SET r_a.active=false, r_a.lost_on=%s ' \
                    'RETURN action, permission' % (
                        username, permission.name, current_time, current_time)
            result, _ = db.cypher_query(query)
            if result.one is not None:
                continue
        else:
            try:
                query = 'MATCH (petaluser:PetalUser {username: "%s"}),' \
                        '(permission:Permission {name: "%s"}) ' \
                        'CREATE UNIQUE (petaluser)-[r:HAS]->(permission) ' \
                        'SET r.active=true, r.gained_on=%s ' \
                        'RETURN permission' % (
                            username, permission.name, current_time)
                result, _ = db.cypher_query(query)
            except(CypherError, Exception):
                query = 'MATCH (petaluser:PetalUser {username: "%s"})-[r:HAS]->' \
                        '(permission:Permission {name: "%s"}) ' \
                        'SET r.active=true, r.gained_on=%s ' \
                        'RETURN permission' % (
                            username, permission.name, current_time)
                result, _ = db.cypher_query(query)
            try:
                query = 'MATCH (petaluser:PetalUser {username: "%s"}),' \
                        '(permission:Permission {name: "%s"})-[:GRANTS]->' \
                        '(action:PetalAction) ' \
                        'CREATE UNIQUE (petaluser)-[r:CAN]->(action) ' \
                        'SET r.active=true, r.gained_on=%s ' \
                        'RETURN action' % (
                            username, permission.name, current_time)
                result, _ = db.cypher_query(query)
            except(CypherError, Exception):
                query = 'MATCH (permission:Permission {name: "%s"})-[:GRANTS]->' \
                        '(action:PetalAction)<-[r:CAN]-' \
                        '(petaluser:PetalUser {username: "%s"}) ' \
                        'SET r.active=true, r.gained_on=%s ' \
                        'RETURN action' % (
                            username, permission.name, current_time)
                result, _ = db.cypher_query(query)
        # Adding short sleep so we don't DDoS ourselves
        # Because of this, this fxn should only ever be called from an async
        # task
        sleep(1)
    cache.delete(username)
    cache.delete("%s_permissions" % username)
    cache.delete("%s_actions" % username)
    return True


def create_permission(permission_data, actions):
    try:
        permission = Permission.nodes.get(name=permission_data["name"])
    except(Permission.DoesNotExist, DoesNotExist):
        try:
            permission = Permission(**permission_data).save()
        except (CypherError, IOError) as e:
            return e
    for action in actions:
        try:
            action = PetalAction.nodes.get(object_uuid=action['object_uuid'])
        except (CypherError, IOError, PetalAction.DoesNotExist,
                DoesNotExist) as e:
            return e
        try:
            permission.actions.connect(action)
            action.privilege.connect(permission)
        except (CypherError, IOError) as e:
            return e
    return True
