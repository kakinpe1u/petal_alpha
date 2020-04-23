import logging
import requests
import pytz
from json import dumps

from uuid import uuid1
from django.core import signing
from django.conf import settings
from datetime import datetime
import collections
from django.utils import encoding
import codecs
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from rest_framework.authtoken.models import Token

log = logging.getLogger(__name__)


def encrypt(data):
    return signing.dumps(data)


def decrypt(data):
    return signing.loads(data)

def request_to_api(url, username, data=None, headers=None, req_method=None,
                   internal=True):
    if headers is None:
        headers = {"content-type": "application/json"}
    if internal is True and username is not None and username != '':
        token = Token.objects.get(user__username=username)

        headers['Authorization'] = "%s %s" % ('Token', token.key)
    response = None
    try:
        if req_method is None or req_method == "POST" or req_method == "post":
            response = requests.post(url, data=dumps(data),
                                     verify=settings.VERIFY_SECURE,
                                     headers=headers)
        elif req_method == 'get' or req_method == "GET":
            response = requests.get(url, verify=settings.VERIFY_SECURE,
                                    headers=headers)
    except requests.ConnectionError as e:
        log.exception("ConnectionError ")
        raise e

    return response


def get_oauth_client(username, password, web_address, client_id=None,
                     client_secret=None):
    if client_id is None:
        client_id = settings.OAUTH_CLIENT_ID
    if client_secret is None:
        client_secret = settings.OAUTH_CLIENT_SECRET
    response = requests.post(web_address, data={
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password,
        'grant_type': 'password'}, verify=settings.VERIFY_SECURE)
    return response.json()


def refresh_oauth_access_token(refresh_token, url, client_id=None,
                               client_secret=None):
    if client_id is None:
        client_id = settings.OAUTH_CLIENT_ID
    if client_secret is None:
        client_secret = settings.OAUTH_CLIENT_SECRET
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(url, data=data,
                             verify=settings.VERIFY_SECURE)
    json_response = response.json()
    if "error" in json_response:
        log.critical("Debugging oauth refresh issue")
        log.critical(dumps(data))

    return json_response


def check_oauth_needs_refresh(oauth_client):
    elapsed = datetime.now(pytz.utc) - oauth_client.last_modified
    expiration = oauth_client.expires_in - 600
    if elapsed.total_seconds() >= expiration:
        return True
    return False


def get_oauth_access_token(pleb, web_address=None):
    if web_address is None:
        web_address = settings.WEB_ADDRESS + '/o/token/'

    try:
        oauth_creds = [oauth_user for oauth_user in pleb.oauth.all()
                       if oauth_user.web_address == web_address][0]
    except IndexError as e:
        return e
    if check_oauth_needs_refresh(oauth_creds) is True:
        refresh_token = decrypt(oauth_creds.refresh_token)
        updated_creds = refresh_oauth_access_token(refresh_token,
                                                   oauth_creds.web_address)
        oauth_creds.last_modified = datetime.now(pytz.utc)
        try:
            oauth_creds.access_token = encrypt(updated_creds['access_token'])
        except KeyError:
            log.exception("Access Token issue")
        oauth_creds.token_type = updated_creds['token_type']
        oauth_creds.expires_in = updated_creds['expires_in']
        oauth_creds.refresh_token = encrypt(updated_creds['refresh_token'])
        oauth_creds.save()

    return decrypt(oauth_creds.access_token)


def generate_oauth_user(pleb, password, web_address=None):
    if web_address is None:
        web_address = settings.WEB_ADDRESS + '/o/token/'
    creds = get_oauth_client(pleb.username, password, web_address)

    return creds

def generate_job(job_func, job_param, countdown = 0, job_id = None):
    if job_id is None:
        job_id = str(uuid1())
    try:
        return job_func.apply_async(kwargs = job_param, countdown = countdown,
                                    job_id = job_id)
    except (IOError, Exception) as exception:
        raise exception

def collect_request_data(context, expedite_param = None, expand_param = None):
    try:
        request = context['request']
        try:
            expand = request.query_params.get('expand', 'false').lower()
            expedite = request.query_params.get('expedite', "false").lower()
            relations = request.query_params.get(
                'relations', 'primaryKey').lower()
            html = request.query_params.get('html', 'false').lower()
            expand_array = request.query_params.get('expand_attrs', [])
            if html == 'true':
                expand = 'true'
        except AttributeError:
            try:
                expand = request.GET.get('expand', 'false').lower()
                expedite = request.GET.get('expedite', 'false').lower()
                relations = request.GET.get('relations', 'primaryKey').lower()
            except AttributeError:
                expand = 'false'
                expedite = 'false',
                relations = 'primaryKey'
                request = None
            expand_array = []
    except KeyError:
        expand = 'false'
        expedite = 'false'
        relations = "primaryKey"
        request = None
        expand_array = []

    if expedite_param is not None:
        expedite = 'true'
    if expand_param:
        expand = 'true'

    return request, expand, expand_array, relations, expedite

def generate_summary(content):
    if content is None:
        return ""
    language = "english"
    stemmer = Stemmer(language)
    summarizer = LexRankSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(language)
    summary = ""
    # encoding and decoding clears up some issues with ascii
    # codec parsing.
    sentence_list = [
        codecs.encode(sentence) for sentence in summarizer(
            PlaintextParser.from_string(
                content.encode(
                    'utf-8').strip().decode('utf-8'),
                Tokenizer(language)).document,
            settings.DEFAULT_SENTENCE_COUNT)]
    for sentence in sentence_list:
        excluded = [exclude
                    for exclude in settings.DEFAULT_EXCLUDE_SENTENCES
                    if exclude.lower() in sentence.lower()]
        word_list = sentence.split(' ')
        if settings.TIME_EXCLUSION_REGEX.search(sentence) is None \
                and len(summary) < settings.DEFAULT_SUMMARY_LENGTH \
                and len(excluded) == 0 \
                and len(word_list) > 1:
            summary += " " + sentence
    return summary.replace('&gt;', '').strip()