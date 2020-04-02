from django.urls import path
from .views import PetalHomeView

urlpatterns = [
    path('', PetalHomeView.as_view(), name = 'petalhome'),
]