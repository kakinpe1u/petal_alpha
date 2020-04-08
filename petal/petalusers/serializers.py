from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.core.cache import cache
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.utils.text import slugify
from django.template.loader import get_template
from django.template import Context
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.http import int_to_base36, base36_to_int
from django.utils.crypto import constant_time_compare, salted_hmac

from rest_framework import serializers, status
from rest_framework.validators import UniqueValidator
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError

from neomodel import db, DoesNotExist
from .models import PetalUser
from unidecode import unidecode
import codecs

from api.serializers import PetalSerializer
from api.utils import generate_job, collect_request_data


def generate_username(first_name, last_name):
    profile_count = User.objects.filter(first_name__iexact = first_name).filter(
        last_name__iexact = last_name).count()
    username = "%s_%s" % (first_name.lower(), last_name.lower())

    if len(username) > 30:
        username = username[:30]
        profile_count = User.objects.filter(username__iexact = username).count()

        if profile_count > 0:
            username = username[:(30 - profile_count)] + str(profile_count)

    elif len(username) < 30 and profile_count == 0:
        username = "%s_%s" % (
            (''.join(e for e in first_name if e.isalnum())).lower(),
            (''.join(e for e in last_name if e.isalnum())).lower())
    else:
        username = "%s_%s%d" % (
            (''.join(e for e in first_name if e.isalnum())).lower(),
            (''.join(e for e in last_name if e.isalnum())).lower(),
            profile_count)
    try:
        username = unidecode(codecs.encode(username, "utf-8"))
    except TypeError:
        # Handles cases where the username is already in unicode format
        username = unidecode(username)
    return username

class PetalUserSerializer(PetalSerializer):

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField(read_only = True)
    password = serializers.CharField(max_length = 128, required = True,
                                     write_only = True, min_length = 8,
                                     style = {'input_type': 'password'})
    # email = serializers.EmailField(required = True, write_only = True,
    #                                validators = [PetalUniqueValidator(
    #                                    queryset = User.objects.all(),
    #                                    message = "That email is already taken.")],)
    date_of_birth = serializers.DateTimeField(required = True, write_only = True)
    occupation_name = serializers.CharField(required = False, allow_null = True,
                                            max_length = 240)
    employer_name = serializers.CharField(required = False, allow_null = True,
                                          max_length = 240)
    is_verified = serializers.BooleanField(read_only = True)
    email_verified = serializers.BooleanField(read_only = True)
    profile_pic = serializers.CharField(required = False)
    actions = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    name_summary = serializers.SerializerMethodField()

    def create(self, valid_request_data):
        request, _, _, _, _ = collect_request_data(self.context)
        username = generate_username(valid_request_data['first_name'],
                                     valid_request_data['last_name'])
        birthdate = valid_request_data.pop('date_of_birth', None)

        user = User.objects.create_user(
            first_name=valid_request_data['first_name'],
            last_name=valid_request_data['last_name'],
            email=valid_request_data['email'].lower().strip(),
            password=valid_request_data['password'], username=username)
        user.save()
        petaluser = PetalUser(email=user.email.lower().strip(),
                              first_name=user.first_name.title(),
                              last_name=user.last_name.title(),
                              username=user.username,
                              date_of_birth=birthdate,
                              occupation=valid_request_data.get('occupation', None),
                              employer=valid_request_data.get('employer', None))
        petaluser.save()

        if not request.user.is_authenticated():
            user = authenticate(username=user.username,
                                password=valid_request_data['password'])
            login(request, user)
        serializer = EmailVerificationSerializer(
            data={}, context={"profile": petaluser, 'request': request,
                              "user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        petaluser.initial_verification_email_sent = True
        petaluser.save()
        generate_job(task_func=create_wall_task,
                   task_param={"username": petaluser.username})
        generate_job(task_func=generate_oauth_info,
                   task_param={'username': petaluser.username,
                               'password': validated_data['password']},
                   countdown=20)
        cache.delete(petaluser.username)
        return petaluser


































