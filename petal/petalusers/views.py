from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.conf import settings
from django.views.generic import View
from rest_framework.response import Response
from rest_framework import status
from neomodel import DoesNotExist, db
from neo4j import CypherError

class PersonalProfileView():
    template_name = 'profile_page.html'

    def get(self, request):
        try:
            query = 'MATCH (q:Quest {owner_username:"%s"}) RETURN q' % (
                request.user.username)
            result, _ = db.cypher_query(query)

        except (DoesNotExist, Quest.DoesNotExist, IndexError):
            quest = None
        return render(request, self.template_name, {
            'page_profile': PlebSerializerNeo(
                Pleb.get(username=request.user.username),
                context={'expand': True, 'request': request}).data,
            'page_user': User.objects.get(username=request.user.username),
            'quest': quest
        })


class ProfileView(View):
    template_name = 'profile_page.html'

    def get(self, request, pleb_username=None):
        if pleb_username is None:
            pleb_username = request.user.username
        try:
            page_user_pleb = Pleb.get(username=pleb_username)
        except (Pleb.DoesNotExist, DoesNotExist):
            return redirect('404_Error')
        except (CypherException, ClientError):
            return redirect("500_Error")
        page_user = User.objects.get(username=page_user_pleb.username)
        if page_user.username == request.user.username:
            is_owner = True
        else:
            is_owner = False

        return render(request, self.template_name, {
            'page_profile': PlebSerializerNeo(
                page_user_pleb,
                context={'expand': True, 'request': request}).data,
            'page_user': page_user,
            'is_owner': is_owner
        })