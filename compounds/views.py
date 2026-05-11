from django.shortcuts import render
from .models import Compound


def home(request):
    return render(request, 'home.html')


def result(request):
    query = request.GET.get('query', '').strip()

    compound = None
    message = ''

    if query:
        compound = Compound.objects.filter(formula__iexact=query).first()

        if not compound:
            message = '검색 결과가 없습니다.'
    else:
        message = '화학식을 입력해주세요.'

    return render(request, 'result.html', {
        'query': query,
        'compound': compound,
        'message': message,
    })
# Create your views here.
