from django.utils.text import slugify
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
# from django.contrib.auth.decorators import login_required
from django.views.generic import View

from neomodel import DoesNotExist, db

from species.models import Species

from .serializers import SpeciesSerializer


def species_redirect_page(request, species_uuid):
    """
    This is the view that displays a single species with all articles
    :param species_uuid:
    :param request:
    :return:
    """

    return redirect(
        "species_detail_page", species_uuid=species_uuid,
        slug=slugify(Species.get(object_uuid=species_uuid).name),
        permanent=True)


# @login_required()
def solution_edit_page(request, solution_uuid=None):
    """
    This is in the questions views for right now due to ease of url structuring.
    We can move it to solutions.views but that will require some changing for
    the single page setup.
    """
    query = 'MATCH (a:Solution {object_uuid: "%s"}) ' \
            'RETURN CASE ' \
            'WHEN a.owner_username = "%s" THEN TRUE ' \
            'ELSE FALSE END' % (solution_uuid, request.user.username)
    res, _ = db.cypher_query(query)
    if res.one is False:
        return redirect('401_Error')
    return render(request, 'solutions/edit.html',
                  {"object_uuid": solution_uuid})


class SpeciesView():
    template_name = 'questions/save.html'

    def get(self, request, species_uuid=None, slug=None):
        if species_uuid is not None:
            try:
                species = Species.get(species_uuid)
            except (DoesNotExist, Species.DoesNotExist):
                return redirect('404_Error')
            # if question.owner_username != request.user.username \
            #         and self.template_name == "questions/edit.html":
            #     return redirect('401_Error')
            return render(request, self.template_name, {
                'sort_by': 'uuid',
                'species': SpeciesSerializer(
                    species, context={"request": request}).data,
            })
        else:
            return render(request, self.template_name, {
                'species_placeholder': render_to_string(
                    'species/placeholder.html')
            })
