from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from api.utils import generate_job
from content.utils import get_ordering, DatabaseQuerySet
from search.tasks import update_query_object

from .serializers import SpeciesSerializer, article_count
from .neo_models import Question