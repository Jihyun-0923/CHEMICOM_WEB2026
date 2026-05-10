from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def result(request):
    query = request.GET.get('query')

    return render(request, 'result.html', {
        'query': query
    })

# Create your views here.
