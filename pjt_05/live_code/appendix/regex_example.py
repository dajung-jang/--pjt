"""
참고 : 정규표현식 한눈에 보기

전처리(04_preprocess)에서 사용한 패턴을 작은 예제로 확인합니다.
패턴 연습 도구 : https://regex101.com (왼쪽 FLAVOR 에서 Python 선택)
"""

import re

import pandas as pd

# ------------------------------------------------------------
# 1. raw 문자열 r'...' : 역슬래시(\)를 쓴 그대로 전달
# ------------------------------------------------------------
print('[raw 문자열]')
print('\\d+' == r'\d+')  # True : 일반 문자열은 \ 를 두 번 써야 같아짐

# ------------------------------------------------------------
# 2. re 모듈 주요 함수
# ------------------------------------------------------------
text = '삼전 27-28 최고점!! 오늘-1% ㅋㅋㅋ'
print('\n[re 함수]  text =', repr(text))
print(re.findall(r'\d+', text))  # ['27', '28', '1']   일치하는 것 모두
print(re.search(r'\d+%', text).group())  # '1%'      처음 일치하는 것 하나
print(re.match(r'^\d+$', '1127'))  # Match 객체    처음부터 끝까지 숫자
print(re.match(r'^\d+$', '1월 9일 1127'))  # None
print(re.sub(r'[^가-힣0-9\s]', '', text))  # '삼전 2728 최고점 오늘1 '  패턴 부분 삭제

# ------------------------------------------------------------
# 3. 실습에서 사용한 패턴
# ------------------------------------------------------------
print('\n[실습 패턴]')
patterns = [
    # (패턴, 바꿀 글자, 예시) : 실습과 같은 순서로 적용
    # 한글·영문·숫자·공백이 아닌 문자 삭제
    (r'[^가-힣a-zA-Z0-9\s]', '', '오늘-1% 가즈아!! ^^'),
    # 연속 공백·줄바꿈을 한 칸으로
    (r'\s+', ' ', '줄바꿈\n\n과   공백'),
]
for pattern, repl, sample in patterns:
    result = re.sub(pattern, repl, sample)
    print(f'{pattern:<22} {sample!r} -> {result!r}')

for sample in ['1127', 'lol ok', '23만 뚫자']:
    only_number = bool(re.match(r'^\d+$', sample))  # 처음부터 끝까지 숫자
    only_english = bool(re.match(r'^[A-Za-z\s]+$', sample))  # 처음부터 끝까지 영어·공백
    print(f'{sample!r:<12} 숫자만: {only_number!s:<5}  영어만: {only_english}')

# ------------------------------------------------------------
# 4. 주의 : 가-힣 은 완성된 글자만 포함 (자음·모음 ㅋ, ㅜ 는 빠짐)
# ------------------------------------------------------------
print('\n[가-힣 범위]')
sample = '화욜날 보자ㅜ ㅋㅋ'
print(re.sub(r'[^가-힣\s]', '', sample))  # '화욜날 보자 '       ㅜ, ㅋ 삭제
print(re.sub(r'[^ㄱ-ㅎㅏ-ㅣ가-힣\s]', '', sample))  # 자음·모음까지 남기기

# ------------------------------------------------------------
# 5. pandas 에서 정규식 사용하기
# ------------------------------------------------------------
print('\n[pandas]')
df = pd.DataFrame({'comment': ['23만 뚫자!!', '1127', 'lol', '오늘\n\n관망']})
df['clean'] = df['comment'].str.replace(r'[^가-힣a-zA-Z0-9\s]', '', regex=True)
df['clean'] = df['clean'].str.replace(r'\s+', ' ', regex=True).str.strip()
df['only_number'] = df['clean'].str.match(r'^\d+$')
print(df)
