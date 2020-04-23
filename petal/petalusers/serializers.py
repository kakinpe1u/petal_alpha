from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.core.cache import cache
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login, authenticate
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework.reverse import reverse
from rest_framework import serializers, status

from django.template.loader import get_template
from django.template import Context
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.http import int_to_base36, base36_to_int
from neomodel import DoesNotExist
from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from datetime import date
from .models import PetalUser
import codecs
from api.serializers import PetalSerializer
from api.utils import generate_job, collect_request_data

class EmailAuthTokenGenerator(object):
    """
    This object is created for user email verification
    """

    def make_token(self, user, petaluser):
        if petaluser is None:
            return None
        return self._make_timestamp_token(user, self._num_days(self._today()),
                                          petaluser)

    def check_token(self, user, token, petaluser):
        if token is None:
            return False
        try:
            timestamp_base36, hash_key = token.split("-")
        except ValueError:
            return False

        try:
            timestamp = base36_to_int(timestamp_base36)
        except ValueError:
            return False

        if not constant_time_compare(self._make_timestamp_token(
                user, timestamp, petaluser), token):
            return False

        if (self._num_days(self._today()) - timestamp) > \
                settings.EMAIL_VERIFICATION_TIMEOUT_DAYS:
            return False

        return True

    def _make_timestamp_token(self, user, timestamp, petaluser):
        timestamp_base36 = int_to_base36(timestamp)

        key_salt = "petal.registration.models.EmailAuthTokenGenerator"
        hash_val = "%s%s%s%s%s" % (user.username, user.first_name,
                                   user.last_name, user.email,
                                   petaluser.email_verified)

        created_hash = salted_hmac(key_salt, hash_val).hexdigest()[::2]
        return "%s-%s" % (timestamp_base36, created_hash)

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        return date.today()

class EmailVerificationSerializer(serializers.Serializer):
    def create(self, validated_data):
        request = self.context.get('request')
        profile = self.context.get('profile')
        user = self.context.get('user')
        if request is None:
            raise ValidationError("Verification email must be "
                                  "requested from application")
        if user is None:
            user = request.user
        if profile is None:
            profile = PetalUser.get(
                username=user.username, cache_buster=True)
        token_gen = EmailAuthTokenGenerator()
        message_data = {
            'message_type': 'email',
            'subject': 'Sagebrew Email Verification',
            'body': get_template('email_templates/verification.html').render(
                Context({
                    'first_name': user.first_name,
                    'verification_url': "%s%s%s" % (
                        settings.EMAIL_VERIFICATION_URL,
                        token_gen.make_token(user, profile), '/')
                })),
            'template': "personal",
            'from_user': {
                'type': "admin",
                'id': settings.INTERCOM_ADMIN_ID_DEVON
            },
            'to_user': {
                'type': "user",
                'user_id': user.username
            }
        }
        return {}

class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data.get('email'))
        except User.DoesNotExist:
            raise ValidationError("Sorry we couldn't find that address")
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        current_site = get_current_site(self.context.get('request'))
        site_name = current_site.name
        context = {
            'email': validated_data['email'],
            'site_name': site_name,
            'first_name': user.first_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': default_token_generator.make_token(user)
        }
        # message_data = {
        #     'message_type': 'email',
        #     'subject': 'Petal Reset Password Request',
        #     'body': get_template('email_templates/password_reset.html').render(
        #         Context(context)),
        #     'template': "personal",
        #     'from_user': {
        #         'type': "admin",
        #         'id': settings.INTERCOM_ADMIN_ID_DEVON
        #     },
        #     'to_user': {
        #         'type': "user",
        #         'user_id': user.username
        #     }
        # }
        # serializer = IntercomMessageSerializer(data=message_data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        return {"detail": "Reset email successfully sent",
                "status": status.HTTP_200_OK,
                "email": validated_data['email']}

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

class UserSerializer(PetalSerializer):
    username = serializers.CharField(max_length=30, read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True, write_only=True,
                                   validators=[UniqueValidator(
                                       queryset=User.objects.all(),
                                       message="Sorry looks like that email is "
                                               "already taken.")],)
    password = serializers.CharField(max_length=128, required=True,
                                     write_only=True,
                                     style={'input_type': 'password'})
    new_password = serializers.CharField(max_length=128, required=False,
                                         write_only=True,
                                         style={'input_type': 'password'})
    birthday = serializers.DateTimeField(write_only=True)
    href = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    def create(self, validated_data):
        # DEPRECATED use profile create instead
        pass

    def update(self, instance, validated_data):
        # DEPRECATED use profile update instead
        pass

    def get_id(self, obj):
        return obj.username

    def get_profile(self, obj):
        request, _, _, _, _ = collect_request_data(self.context)
        return reverse('profile-detail', kwargs={'username': obj.username},
                       request=request)

    def get_href(self, obj):
        request, expand, _, _, _ = collect_request_data(self.context)
        return reverse(
            'user-detail', kwargs={'username': obj.username}, request=request)

class PetalUserSerializer(PetalSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(max_length=128, required=True,
                                     write_only=True, min_length=8,
                                     style={'input_type': 'password'})
    new_password = serializers.CharField(max_length=128, required=False,
                                         write_only=True, min_length=8,
                                         style={'input_type': 'password'})
    email = serializers.EmailField(required = True, write_only = True,
                                   validators = [UniqueValidator(
                                       queryset = User.objects.all(),
                                       message = "That email is already taken.")],)

    date_of_birth = serializers.DateTimeField(required=True, write_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    actions = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

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
        serializer = EmailVerificationSerializer(
            data={}, context={"profile": petaluser, 'request': request,
                              "user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        petaluser.initial_verification_email_sent = True
        petaluser.save()

        cache.delete(petaluser.username)
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























