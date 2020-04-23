from django.shortcuts import render

# Create your views here.


def search_result_view(request):
    return render(request, 'search.html')