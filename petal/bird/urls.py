from django.urls import path
from . import views

urlpatterns = [
    path('', views.birdhome, name = 'index'),
    path('results/', views.birdresults, name = 'bird-results'),
]


# urlpatterns = [
#     path('', views.birdhome, name = 'index'),
#     path('results/', views.search_result_view, name = 'bird-results'),
# ]
