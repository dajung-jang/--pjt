"""
전처리 ② pandas로 댓글 정제하기

학습 목표
  1. 댓글 리스트를 DataFrame 으로 바꿔 열 단위로 한 번에 처리한다
  2. 정규표현식으로 특수문자와 의미 없는 댓글을 정리한다
  3. IQR 로 "너무 짧거나 긴" 기준을 데이터에서 계산한다

전체 흐름
  수집 => 부적절 제거 => [결측치 => 특수문자 => 의미 없는 댓글 => 길이 이상치] => 증강

입력 : data/comments_filtered.json (01_filter_bad_comments.py 의 결과)
출력 : data/comments_clean.json

진행 방법
  - 미리 준비된 함수(이전 실습 함수, 동작 과정 시각화)는 완성되어 있습니다. 읽어 보기만 하세요
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제합니다
  - 함수 정의 STEP 은 해제해도 출력이 없습니다. 마지막 STEP(실행)까지 해제해야 동작합니다
  - LLM 응답은 실행할 때마다 조금씩 달라질 수 있습니다
"""

import json
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / 'data'


# ------------------------------------------------------------
# 이전 실습에서 만든 함수 (수정 없이 그대로 사용)
# ------------------------------------------------------------


def load_json(file_path):
    """JSON 파일을 읽어 파이썬 객체(딕셔너리·리스트)로 돌려준다"""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def save_json(data, file_path):
    """data 를 JSON 파일로 저장한다"""
    file_path.parent.mkdir(exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'[저장] {file_path.name}')


# ------------------------------------------------------------
# 동작 과정 시각화 (완성 코드, 수정 없이 그대로 사용)
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
# [STEP 1] DataFrame 으로 바꾸고 결측치 제거하기
# ------------------------------------------------------------
# 왜 DataFrame 으로 바꿀까?
#   - 리스트는 for 문으로 댓글을 "하나씩" 처리해야 합니다
#   - pandas DataFrame 은 열(column) 전체에 같은 처리를 "한 번에" 적용할 수 있습니다
#   - 엑셀 표처럼 원본 열(comment)과 정리한 열(clean)을 나란히 두고 비교하기도 쉽습니다
#
# 결측치(비어 있는 값) 처리
#   - dropna(subset=['comment']) : comment 열이 None(값 없음)인 행 제거
#   - .str.strip()               : 각 댓글의 앞뒤 공백·줄바꿈 제거
#   - df[df['comment'] != '']    : 조건이 True 인 행만 남기기 (빈 문자열 제거)
#     => '   ' 처럼 공백뿐인 댓글은 strip 후 '' 가 되어 여기서 걸러집니다

def to_dataframe(comments):
    """댓글 리스트를 DataFrame 으로 바꾸고, 비어 있는 댓글을 제거한다"""
    df = pd.DataFrame(comments, columns=['comment'])

    df = df.dropna(subset=['comment'])  # None 값 제거
    df['comment'] = df['comment'].astype(str).str.strip()  # 앞뒤 공백 제거
    df = df[df['comment'] != '']  # 공백만 있던 댓글(이제 빈 문자열) 제거

    print(f'[결측치] {len(comments)}개 -> {len(df)}개')
    return df


# ------------------------------------------------------------
# [STEP 2] 특수문자 제거·공백 정리하기
# ------------------------------------------------------------
# 정규표현식 : 글자의 "패턴"으로 찾고 바꾸는 방법 (부록 참고)
#   [^가-힣a-zA-Z0-9\s]
#     - [ ... ]  : 괄호 안의 문자 중 하나
#     - [^ ... ] : 괄호 안의 문자가 "아닌" 것
#     - 가-힣    : 완성형 한글 (ㅋ, ㅜ 같은 자음·모음은 포함되지 않음!)
#     - \s       : 공백, 탭, 줄바꿈
#   re.sub(패턴, '', x) : x 에서 패턴에 맞는 부분을 '' 로 바꿈 = 삭제
#
# df['comment'].apply(함수) : comment 열의 값마다 함수를 적용한 결과를 새 열로
# .str.replace(r'\s+', ' ', regex=True) : 줄바꿈·연속 공백을 공백 한 칸으로
#
# 원본(comment)은 그대로 두고 새 열(clean)에 저장하는 이유
#   - 무엇이 어떻게 바뀌었는지 비교할 수 있게 하기 위해서입니다
#
# 확인 포인트 (바뀐 댓글 출력을 보며)
#   - '3%에서 동결입니다.' 는 무엇으로 바뀌었나요? 의미가 그대로인가요?
#   - 'ㅋㅋ' 는 왜 사라졌나요?

def remove_special_chars(df):
    """한글·영문·숫자·공백만 남기고, 연속된 공백을 한 칸으로 정리한다"""
    df['clean'] = df['comment'].apply(lambda x: re.sub(r'[^가-힣a-zA-Z0-9\s]', '', x))

    df['clean'] = df['clean'].str.replace(r'\s+', ' ', regex=True).str.strip()

    print('[특수문자 정리]')
    show_changes(df, 'comment', 'clean')
    return df


# ------------------------------------------------------------
# [STEP 3] 의미 없는 댓글 제거하기
# ------------------------------------------------------------
# 정보가 거의 없는 댓글 : '1127', 'lol', 'none' 같은 댓글은 분석·증강할 가치가 없습니다
#
# 조건 만들기 : 각 조건의 결과는 행마다 True / False 가 담긴 열(Series)입니다
#   str.match(r'^\d+$')       : ^ 처음부터 \d+ 숫자가 1개 이상 $ 끝까지 => 숫자로만 된 댓글
#   str.match(r'^[A-Za-z\s]+$'): 처음부터 끝까지 영어·공백만 있는 댓글
#   str.lower() == 'none'      : 소문자로 바꿔 'none' 과 같은지 (None, NONE 모두 잡힘)
#
# 조건 합치기 : |  (또는)  => 셋 중 하나라도 True 면 True
# 조건 뒤집기 : ~  (반전)  => True <-> False
#   df[~cond_any] : "제거 대상이 아닌" 행만 남기기
#
# 지우기 전에 제거 대상을 먼저 출력하는 습관이 중요합니다
#   - 예상과 다른 댓글이 지워지는지 바로 확인할 수 있습니다
#
# 확인 포인트
#   - 이번 데이터에서 제거된 댓글이 있나요? (없을 수도 있습니다. 수집 시점마다 다름)

def remove_meaningless(df):
    """숫자만 / 영어만 / 'none' 인 댓글을 제거한다"""
    cond_numeric = df['clean'].str.match(r'^\d+$')  # 처음부터 끝까지 숫자
    cond_english = df['clean'].str.match(r'^[A-Za-z\s]+$')  # 처음부터 끝까지 영어·공백
    cond_none = df['clean'].str.lower() == 'none'  # 글자 그대로 'none'

    cond_any = cond_numeric | cond_english | cond_none  # 하나라도 해당하면 제거 대상

    print('[의미 없는 댓글]')
    show_removed('제거 대상', df[cond_any]['clean'].tolist())  # 지우기 전에 먼저 확인
    return df[~cond_any]  # ~ : 조건 반전 -> 해당하지 않는 행만 남김


# ------------------------------------------------------------
# [STEP 4] 길이 이상치 제거하기 (IQR)
# ------------------------------------------------------------
# 왜 필요할까?
#   - 너무 짧은 댓글('던져')은 정보가 없고, 너무 긴 댓글은 광고·도배일 수 있습니다
#   - "몇 글자부터 이상한가"를 감으로 정하지 않고, 수집한 데이터의 분포로 정합니다
#
# IQR (사분위 범위)
#   댓글 길이를 짧은 순서로 세웠을 때
#     |----|=========|=========|----|
#    최소  Q1      중앙값      Q3  최대
#          (25%)              (75%)
#   - IQR = Q3 - Q1 : 가운데 50% 댓글들의 길이 폭
#   - 정상 범위 : Q1 - 1.5 x IQR  ~  Q3 + 1.5 x IQR  (통계에서 널리 쓰는 기준)
#   - 이번 코드는 하한을 최소 5글자로 보정했습니다 : max(5, ...)
#
# quantile(0.25) : 25% 지점의 값 (Q1)
#
# 확인 포인트
#   - 정상 범위는 몇 ~ 몇 글자로 계산되었나요?
#   - 제거된 댓글 중 "길다는 이유만으로" 지워진 좋은 의견이 있나요?
#     (기준을 데이터에서 계산하므로, 데이터가 바뀌면 범위도 바뀝니다)

def remove_length_outliers(df):
    """IQR 로 정상 길이 범위를 계산하고, 범위를 벗어난 댓글을 제거한다"""
    df['length'] = df['clean'].str.len()

    if len(df) < 5:
        print('[길이 이상치] 댓글이 5개 미만이라 3글자 미만만 제거')
        return df[df['length'] >= 3]

    q1 = df['length'].quantile(0.25)  # 짧은 쪽에서 25% 지점
    q3 = df['length'].quantile(0.75)  # 짧은 쪽에서 75% 지점
    iqr = q3 - q1  # 가운데 50% 의 폭
    lower = max(5, q1 - 1.5 * iqr)  # 최소 5글자는 되어야 정상
    upper = q3 + 1.5 * iqr

    cond_outlier = (df['length'] < lower) | (df['length'] > upper)

    print(f'[길이 이상치] Q1={q1}, Q3={q3}, IQR={iqr} -> 정상 범위 {lower} ~ {upper}글자')
    show_removed('제거 대상', df[cond_outlier]['clean'].tolist())
    return df[~cond_outlier]


# ------------------------------------------------------------
# [STEP 5] 4단계 연결해서 실행하기
# ------------------------------------------------------------
# 전처리 4단계를 순서대로 연결합니다
#   부적절 제거(01 파일) => 결측치 => 특수문자 => 의미 없는 댓글 => 길이 이상치
#   각 함수는 DataFrame 을 받아 정리된 DataFrame 을 돌려주므로 차례로 이어 붙일 수 있습니다
#
# df['clean'].tolist() : 정리된 열을 다시 파이썬 리스트로
#
# 확인 포인트
#   - 단계마다 댓글 수가 어떻게 줄었나요? (20 => ? => ? => ?)
#   - data/comments_clean.json 이 다음 단계(증강)의 입력입니다

if __name__ == '__main__':
    filtered = load_json(DATA_DIR / 'comments_filtered.json')
    comments = filtered['comments']

    df = to_dataframe(comments)
    df = remove_special_chars(df)
    df = remove_meaningless(df)
    df = remove_length_outliers(df)

    cleaned = df['clean'].tolist()
    print(f'\n[전처리 결과] {len(comments)}개 -> {len(cleaned)}개')
    for idx, c in enumerate(cleaned, 1):
        print(f'{idx:02d}. {c}')

    save_json(
        {
            'company': filtered['company'],
            'collected_at': filtered['collected_at'],
            'count': len(cleaned),
            'comments': cleaned,
        },
        DATA_DIR / 'comments_clean.json',
    )
