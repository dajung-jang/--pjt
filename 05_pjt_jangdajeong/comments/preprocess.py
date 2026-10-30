import re
import statistics

MIN_LEN = 5
MAX_LEN = 76


def iqr_bounds(lengths):
    """댓글 길이의 IQR 기준 하한/상한 (저장용 정보)"""
    if len(lengths) < 2:
        return None, None
    q1, _, q3 = statistics.quantiles(lengths, n=4)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def basic_clean(comments):
    """결측치 제거 → 의미없는 패턴/특수문자 제거 → 공백 정리 → 길이 필터"""
    result = []
    for c in comments:
        if not c:
            continue
        text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ]+', '', c)         # ㅋㅋㅋ, ㅎㅎ, ㅠㅠ 등
        text = re.sub(r'[^\w\s가-힣]', ' ', text)      # 특수문자
        text = re.sub(r'\s+', ' ', text).strip()       # 불필요한 공백
        if MIN_LEN <= len(text) <= MAX_LEN:
            result.append(text)
    return result