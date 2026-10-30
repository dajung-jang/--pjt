"""
preprocess.py : 댓글 전처리 모듈 (부적절 댓글 제거 + pandas 정제)

04_preprocess 에서 만든 함수를 한 파일에 모았습니다.

    from preprocess import CRITERIA, filter_inappropriate, clean_comments
    kept, removed = filter_inappropriate(comments, CRITERIA['strict'])
    cleaned = clean_comments(kept)
"""

import re

import pandas as pd

from llm import parse_json_array, run_llm


# ------------------------------------------------------------
# 동작 과정 시각화
# ------------------------------------------------------------
def show_changes(df, before_col, after_col):
    """정리 전과 후가 달라진 행만 나란히 출력한다"""
    changed = df[df[before_col] != df[after_col]]
    print(f'  바뀐 댓글 {len(changed)}개')
    for before, after in zip(changed[before_col], changed[after_col]):
        print(f'  - 전 : {before!r}')
        print(f'    후 : {after!r}')


def show_removed(title, removed_texts):
    """제거된 댓글 목록을 출력한다"""
    print(f'  {title} : {len(removed_texts)}개')
    for text in removed_texts:
        print(f'    - {text!r}')


# ------------------------------------------------------------
# 부적절 댓글 제거 (04_preprocess/01_filter_bad_comments.py)
# ------------------------------------------------------------
# 판단 기준 2가지 : 같은 댓글이라도 기준에 따라 LLM 의 판단이 달라짐
CRITERIA = {
    'basic': '욕설, 혐오, 비방, 선정성, 과도한 비난',
    'strict': (
        '욕설, 혐오, 비방, 선정성, 과도한 비난, 조롱·비꼬기, '
        '다른 투자자를 깎아내리는 표현, 근거 없는 단정이나 매수·매도를 부추기는 선동'
    ),
}


def build_filter_prompt(comments, criteria):
    """댓글에 번호를 붙이고, 기준에 해당하는 댓글의 "번호만" 돌려 달라는 프롬프트를 만든다"""
    # 0. 댓글1
    # 1. 댓글2 ... 형태의 문자열 하나로 합침
    numbered = '\n'.join(f'{i}. {c}' for i, c in enumerate(comments))

    # 응답 형식을 [0, 2, 5] 같은 배열로 고정해야 코드에서 바로 처리할 수 있음
    return f"""다음 댓글 목록에서 아래 기준에 해당하는 부적절한 댓글의 번호만 골라줘.
기준 : {criteria}
응답은 반드시 [0, 2, 5] 또는 [] 형식의 배열만 보내고, 설명이나 코드블럭은 쓰지 마.

댓글 목록:
{numbered}"""


def filter_inappropriate(comments, criteria):
    """LLM 이 고른 번호의 댓글을 제거하고 (남은 댓글, 제거된 댓글)을 돌려준다"""
    response = run_llm(build_filter_prompt(comments, criteria))
    print('  [LLM 응답]', response)

    numbers = parse_json_array(response)
    if numbers is None:
        # 응답을 해석할 수 없으면 아무것도 지우지 않음 (잘못 지우는 것보다 안전)
        return list(comments), []

    # 정수이면서 실제 댓글 번호 범위 안인 값만 사용 (중복 제거 후 정렬)
    to_remove = sorted(
        {n for n in numbers if type(n) is int and 0 <= n < len(comments)}
    )

    # 앞에서부터 지우면 뒤쪽 번호가 한 칸씩 밀려 엉뚱한 댓글이 지워짐 -> 뒤에서부터
    kept = list(comments)  # 원본은 그대로 두고 복사본에서 제거
    removed = []
    for i in reversed(to_remove):
        removed.append(kept.pop(i))
    removed.reverse()  # 원래 순서대로 보기 좋게

    return kept, removed


# ------------------------------------------------------------
# 정제 (04_preprocess/02_clean_with_pandas.py)
# ------------------------------------------------------------
def to_dataframe(comments):
    """댓글 리스트를 DataFrame 으로 바꾸고, 비어 있는 댓글을 제거한다"""
    df = pd.DataFrame(comments, columns=['comment'])

    df = df.dropna(subset=['comment'])  # None 값 제거
    df['comment'] = df['comment'].astype(str).str.strip()  # 앞뒤 공백 제거
    df = df[df['comment'] != '']  # 공백만 있던 댓글(이제 빈 문자열) 제거

    print(f'[결측치] {len(comments)}개 -> {len(df)}개')
    return df


def remove_special_chars(df):
    """한글·영문·숫자·공백만 남기고, 연속된 공백을 한 칸으로 정리한다"""
    # [^가-힣a-zA-Z0-9\s] : 한글·영문·숫자·공백이 "아닌" 문자 -> '' 로 바꿔 삭제
    df['clean'] = df['comment'].apply(lambda x: re.sub(r'[^가-힣a-zA-Z0-9\s]', '', x))

    # \s+ : 공백·줄바꿈이 1개 이상 연속 -> 공백 한 칸으로
    df['clean'] = df['clean'].str.replace(r'\s+', ' ', regex=True).str.strip()

    print('[특수문자 정리]')
    show_changes(df, 'comment', 'clean')
    return df


def remove_meaningless(df):
    """숫자만 / 영어만 / 'none' 인 댓글을 제거한다"""
    cond_numeric = df['clean'].str.match(r'^\d+$')  # 처음부터 끝까지 숫자
    cond_english = df['clean'].str.match(r'^[A-Za-z\s]+$')  # 처음부터 끝까지 영어·공백
    cond_none = df['clean'].str.lower() == 'none'  # 글자 그대로 'none'

    cond_any = cond_numeric | cond_english | cond_none  # 하나라도 해당하면 제거 대상

    print('[의미 없는 댓글]')
    show_removed('제거 대상', df[cond_any]['clean'].tolist())  # 지우기 전에 먼저 확인
    return df[~cond_any]  # ~ : 조건 반전 -> 해당하지 않는 행만 남김


def remove_length_outliers(df):
    """IQR 로 정상 길이 범위를 계산하고, 범위를 벗어난 댓글을 제거한다"""
    df['length'] = df['clean'].str.len()

    # 댓글이 너무 적으면 통계로 판단하기 어려움 -> 3글자 미만만 제거
    if len(df) < 5:
        print('[길이 이상치] 댓글이 5개 미만이라 3글자 미만만 제거')
        return df[df['length'] >= 3]

    q1 = df['length'].quantile(0.25)  # 짧은 쪽에서 25% 지점
    q3 = df['length'].quantile(0.75)  # 짧은 쪽에서 75% 지점
    iqr = q3 - q1  # 가운데 50% 의 폭
    lower = max(5, q1 - 1.5 * iqr)  # 최소 5글자는 되어야 정상
    upper = q3 + 1.5 * iqr

    cond_outlier = (df['length'] < lower) | (df['length'] > upper)

    print(
        f'[길이 이상치] Q1={q1}, Q3={q3}, IQR={iqr} -> 정상 범위 {lower} ~ {upper}글자'
    )
    show_removed('제거 대상', df[cond_outlier]['clean'].tolist())
    return df[~cond_outlier]


# ------------------------------------------------------------
# 외부에서 사용할 함수 : 댓글 리스트 => 정제된 댓글 리스트
# ------------------------------------------------------------
def clean_comments(comments):
    """정제 4단계를 차례로 적용하고 정제된 댓글 리스트를 돌려준다"""
    df = to_dataframe(comments)
    df = remove_special_chars(df)
    df = remove_meaningless(df)
    df = remove_length_outliers(df)
    return df['clean'].tolist()


if __name__ == '__main__':
    sample = [
        '오늘 22만만 지켜라!!',
        '1127',
        'ㅋㅋㅋ',
        '공포에 사라는 말 아시죠?',
        '23만 뚫자~',
        '던져',
    ]
    print(clean_comments(sample))
