from django.shortcuts import render

from . import crawler, llm, preprocess
from .models import CommentResult


def index(request):
    return render(request, 'comments/index.html')


def company(request):
    name = request.GET.get('company_name', '').strip()

    # F601: 입력값이 없으면 아무 동작 안 함
    if not name:
        return render(request, 'comments/index.html')

    print(name)  # F601: 터미널 출력
    context = {'company_name': name}

    try:
        stock_name, raw = crawler.crawl_comments(name)
    except crawler.CompanyNotFound:
        context['error'] = f'"{name}"에 해당하는 회사를 찾을 수 없습니다.'
        return render(request, 'comments/index.html', context)
    except crawler.NoComments:
        context['error'] = '해당 회사의 댓글 데이터가 존재하지 않습니다.'
        return render(request, 'comments/index.html', context)

    # F605: 전처리 (규칙 기반 → LLM 부적절 댓글 제거)
    cleaned = preprocess.basic_clean(raw)
    # print('[DEBUG] 규칙 전처리 후:', len(cleaned), cleaned)
    bad = set(llm.find_inappropriate(cleaned))
    # print('[DEBUG] LLM이 부적절로 판단한 번호:', bad)
    cleaned = [c for i, c in enumerate(cleaned) if i not in bad]

    # F606: 증강
    augmented = llm.augment(cleaned)

    # F610: 요약
    summary = llm.summarize(raw)

    # F602, F607: 저장
    lower, upper = preprocess.iqr_bounds([len(c) for c in raw])
    CommentResult.objects.create(
        stock_name=stock_name,
        raw_comments=raw,
        cleaned_comments=cleaned,
        augmented_comments=augmented,
        iqr_lower=lower,
        iqr_upper=upper,
    )

    context.update({
        'stock_name': stock_name,
        'raw': raw,
        'cleaned': cleaned,
        'augmented': augmented,
        'final': cleaned + augmented,
        'summary': summary,
        'min_len': preprocess.MIN_LEN,
        'max_len': preprocess.MAX_LEN,
    })
    return render(request, 'comments/index.html', context)