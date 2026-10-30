"""
llm.py : LLM 호출과 응답 해석 모듈

04_preprocess, 05_augment 에서 함께 쓰던 함수를 한 파일에 모았습니다.
.env 를 읽는 코드도 여기 한 곳에만 둡니다.

    from llm import run_llm, parse_json_array
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent

# .env 파일의 값(GMS_KEY, GMS_BASE_URL, MODEL)을 환경 변수로 불러옴
load_dotenv(BASE_DIR.parent / '.env')


# ------------------------------------------------------------
# 04_preprocess 에서 만든 함수
# ------------------------------------------------------------
def run_llm(prompt):
    """prompt 를 LLM 에 보내고 응답 텍스트를 돌려준다"""
    # GMS 는 OpenAI 와 같은 요청 형식을 제공 -> 주소(base_url)만 GMS 로 지정
    client = OpenAI(api_key=os.getenv('GMS_KEY'), base_url=os.getenv('GMS_BASE_URL'))

    # Responses API : 입력(input)을 보내고, 응답 객체를 돌려받음
    response = client.responses.create(
        model=os.getenv('MODEL'),
        input=prompt,
    )
    # output_text : 응답 중 텍스트 부분만 하나의 문자열로 모아 둔 값
    return response.output_text


def parse_json_array(response):
    """LLM 응답에서 JSON 배열을 꺼낸다. 형식이 틀리면 None"""
    text = response.strip()

    # 지시해도 응답을 ```json ... ``` 코드블럭으로 감싸 오는 경우가 있어 벗겨냄
    if text.startswith('```'):
        text = text.strip('`').removeprefix('json').strip()

    try:
        data = json.loads(text)  # '[0, 2, 5]' -> [0, 2, 5]
    except json.JSONDecodeError:
        print('[파싱 실패] 응답이 JSON 형식이 아닙니다:', response[:100])
        return None

    if not isinstance(data, list):
        print('[파싱 실패] 응답이 리스트가 아닙니다:', response[:100])
        return None
    return data


if __name__ == '__main__':
    print(
        parse_json_array(
            run_llm('1부터 3까지 숫자를 [1, 2, 3] 형식의 배열로만 답해줘.')
        )
    )
