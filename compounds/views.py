from django.db.models import Q
from django.shortcuts import render
from .models import Compound, Element


def home(request):
    return render(request, 'home.html')


def result(request):
    query = request.GET.get('query', '').strip()

    compound = None
    element = None
    message = ''

    if query:
        compound = (
            Compound.objects
            .filter(Q(formula__iexact=query) | Q(name__icontains=query))
            .first()
        )

        if not compound:
            element = (
                Element.objects
                .filter(Q(symbol__iexact=query) | Q(name__icontains=query))
                .first()
            )

        if not compound and not element:
            message = '검색 결과가 없습니다.'
    else:
        message = '화합물명, 화학식, 원소명 또는 원소 기호를 입력해주세요.'

    return render(request, 'result.html', {
        'query': query,
        'compound': compound,
        'element': element,
        'message': message,
    })