"""
augment.py : 데이터 증강 모듈

05_augment 에서 만든 함수를 한 파일에 모았습니다.

    from augment import augment_comments, merge_with_source
    augmented = augment_comments(cleaned)
    records = merge_with_source(cleaned, augmented)
"""

from llm import parse_json_array, run_llm


# ------------------------------------------------------------
# 05_augment/01_augment_comments.py 에서 만든 함수
# ------------------------------------------------------------
def build_augment_prompt(comments):
    """각 문장을 의미는 유지하고 표현만 바꿔 달라는 프롬프트를 만든다"""
    numbered = '\n'.join(f'{i}. {c}' for i, c in enumerate(comments))
    return f"""다음 {len(comments)}개 문장을 각각 의미는 유지하면서 다른 표현으로 바꿔줘.
- 입력과 같은 순서, 같은 개수({len(comments)}개)로
- ["문장1", "문장2"] 형식의 JSON 배열만 보내고, 번호·설명·코드블럭은 쓰지 마

문장 목록:
{numbered}"""


def augment_comments(comments):
    """LLM 으로 문장을 증강하고, 개수가 맞을 때만 결과를 돌려준다"""
    print(f'[증강] LLM 호출 중... (입력 {len(comments)}개)')
    augmented = parse_json_array(run_llm(build_augment_prompt(comments)))

    if augmented is None:
        return []

    # 개수가 다르면 원본과 짝을 맞출 수 없음 -> 사용하지 않음
    if len(augmented) != len(comments):
        print(
            f'[검증 실패] 입력 {len(comments)}개, 응답 {len(augmented)}개 -> 증강 결과 사용 안 함'
        )
        return []

    return [str(a).strip() for a in augmented]


def merge_with_source(originals, augmented):
    """원본과 증강 문장을 하나로 합치되, 어디서 왔는지(source)를 표시한다"""
    records = [{'text': t, 'source': 'original'} for t in originals]
    for i, t in enumerate(augmented):
        # origin_index : 몇 번째 원본 문장에서 만들어졌는지
        records.append({'text': t, 'source': 'augmented', 'origin_index': i})
    return records


if __name__ == '__main__':
    sample = ['오늘 22만만 지켜라', '23만 뚫자']
    print(merge_with_source(sample, augment_comments(sample)))
