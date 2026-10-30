import json
import os
import re

import requests

# ★ SSAFY GMS 안내 문서의 URL/키/모델명으로 확인해서 맞춰주세요
GMS_URL = os.environ.get(
    'GMS_URL', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions'
)
GMS_KEY = os.environ.get('GMS_KEY', '')
MODEL = os.environ.get('GMS_MODEL', 'gpt-4o-mini')


def _chat(prompt):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GMS_KEY}',
    }
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': prompt}]}
    res = requests.post(GMS_URL, headers=headers, json=body, timeout=60)
    res.raise_for_status()
    return res.json()['choices'][0]['message']['content']


def _parse_array(text):
    match = re.search(r'\[.*\]', text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def find_inappropriate(comments):
    """부적절한 댓글의 인덱스(0부터) 리스트 반환. 실패 시 빈 리스트"""
    if not comments:
        return []
    numbered = '\n'.join(f'{i}: {c}' for i, c in enumerate(comments))
    prompt = (
        '다음 댓글 목록에서 부적절한 댓글(욕설, 혐오, 비방, 선정성, 과도한 비난 등)의 '
        '번호(0부터 시작)만 JSON 배열로 알려줘. 없으면 [] 로만 답해.\n\n' + numbered
    )
    try:
        arr = _parse_array(_chat(prompt))
        return [i for i in (arr or []) if isinstance(i, int)]
    except Exception:
        return []


def augment(comments):
    """각 댓글의 의미를 유지하며 확장한 문장 리스트 반환 (개수 동일)"""
    if not comments:
        return []
    numbered = '\n'.join(f'{i}: {c}' for i, c in enumerate(comments))
    prompt = (
        f'다음 댓글 {len(comments)}개 각각을 의미는 유지하되 자연스럽게 확장·재작성해줘. '
        f'반드시 길이가 {len(comments)}인 JSON 문자열 배열로만 답하고, 순서를 유지해.\n\n'
        + numbered
    )
    try:
        arr = _parse_array(_chat(prompt))
        if arr and len(arr) == len(comments):
            return [str(x) for x in arr]
    except Exception:
        pass
    return list(comments)  # 실패 시 원문으로 대체


def summarize(comments):
    if not comments:
        return ''
    joined = '\n'.join(f'- {c}' for c in comments)
    prompt = f'다음 주식 커뮤니티 댓글들의 주요 내용을 3~4문장으로 요약해줘.\n\n{joined}'
    try:
        return _chat(prompt).strip()
    except Exception:
        return '요약을 생성하지 못했습니다.'