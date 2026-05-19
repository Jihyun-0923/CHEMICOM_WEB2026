from django.db.models import Q
from django.shortcuts import render
from .models import Compound, Element


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def result(request):
    query = request.GET.get('query', '').strip()

    compound = None
    element = None
    related_elements = []
    risk_level = 1
    risk_class = 'risk-low'
    risk_percent = 0
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

    if compound:
        related_elements = compound.elements.all()
        risk_level = max(1, min(compound.risk_level, 5))
        risk_class = 'risk-low' if risk_level <= 1 else 'risk-mid' if risk_level <= 3 else 'risk-high'
        risk_percent = risk_level * 20

    return render(request, 'result.html', {
        'query': query,
        'compound': compound,
        'element': element,
        'related_elements': related_elements,
        'risk_level': risk_level,
        'risk_class': risk_class,
        'risk_percent': risk_percent,
        'message': message,
    })
