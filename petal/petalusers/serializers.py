from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.core.cache import cache
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, authenticate


from rest_framework import serializers, status


from .models import PetalUser
from unidecode import unidecode
import codecs

from api.serializers import NodeSerializer
from api.utils import generate_job, collect_request_data


def generate_username(first_name, last_name):
    profile_count = User.objects.filter(first_name__iexact=first_name).filter(
        last_name__iexact=last_name).count()
    username = "%s_%s" % (first_name.lower(), last_name.lower())

    if len(username) > 30:
        username = username[:30]
        profile_count = User.objects.filter(username__iexact=username).count()

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
        username = codecs.encode(username, "utf-8")
    except TypeError:
        # Handles cases where the username is already in unicode format
        username = username
    return username


class PetalUserSerializer(NodeSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(max_length=128, required=True,
                                     write_only=True, min_length=8,
                                     style={'input_type': 'password'})
    # email = serializers.EmailField(required = True, write_only = True,
    #                                validators = [PetalUniqueValidator(
    #                                    queryset = User.objects.all(),
    #                                    message = "That email is already taken.")],)
    date_of_birth = serializers.DateTimeField(required=True, write_only=True)
    occupation_name = serializers.CharField(required=False, allow_null=True,
                                            max_length=240)
    employer_name = serializers.CharField(required=False, allow_null=True,
                                          max_length=240)
    is_verified = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)

    def create(self, data):
        request, _, _, _, _ = collect_request_data(self.context)
        username = generate_username(data['first_name'],
                                     data['last_name'])
        birthdate = data.pop('date_of_birth', None)

        user = User.objects.create_user(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'].lower().strip(),
            password=data['password'], username=username)
        user.save()
        petaluser = PetalUser(email=user.email.lower().strip(),
                              first_name=user.first_name.title(),
                              last_name=user.last_name.title(),
                              username=user.username,
                              date_of_birth=birthdate,
                              occupation=data.get('occupation', None),
                              employer=data.get('employer', None))
        petaluser.save()

        if not request.user.is_authenticated():
            user = authenticate(username=user.username,
                                password=data['password'])
            login(request, user)
        cache.delete(petaluser.username)
        return petaluser

    def update(self, instance, data):
        request, _, _, _, _ = collect_request_data(self.context)
        update_time = request.data.get('update_time', False)
        first_name = data.get('first_name', instance.first_name)
        last_name = data.get('last_name', instance.last_name)

        user_object = User.objects.get(username=instance.username)
        if first_name != user_object.first_name:
            instance.first_name = first_name
            user_object.first_name = first_name
        if last_name != user_object.last_name:
            instance.last_name = last_name
            user_object.last_name = last_name
        if user_object.check_password(data.get('password', "")) is True:
            user_object.set_password(data.get(
                'new_password', data.get('password', "")))
        user_object.save()

        if update_time:
            instance.last_counted_vote_node = instance.vote_from_last_refresh

        instance.save()
        instance.update_quest()
        cache.delete(instance.username)
        return super(PetalUserSerializer, self).update(instance, data)

    def get_id(self, object):
        return object.username























