from django.http import HttpResponse
from django.views.generic import View
from django.template import loader


class PetalHomeView(View):

    def get(self, request, *args, **kwargs):
        template = loader.get_template('petal_main/index.html')
        context = dict(title = 'PeTaL')
        return HttpResponse(template.render(context, request))