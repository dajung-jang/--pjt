"""
참고 : 파이프라인을 LangGraph 로 실행하기

06_pipeline 의 모듈을 그대로 가져와, 각 단계를 "노드"로 연결합니다.
설치 필요 : pip install langgraph  (실습 requirements.txt 에는 포함되어 있지 않음)

    START -> crawl -(댓글 있음?)-> filter_bad -> clean -> augment -> END
                     └─(없음)──> no_data ───────────────────────> END

  지금 코드              | LangGraph
  함수                   | 노드 (node)
  함수 사이에 넘기는 값   | 상태 (State)
  함수 호출 순서         | 엣지 (edge)
  if not comments:       | 조건부 엣지
"""

import sys
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

# 06_pipeline 폴더의 모듈을 import 할 수 있도록 경로 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent / '06_pipeline'))

from augment import augment_comments  # noqa: E402
from crawler import fetch_comments  # noqa: E402
from preprocess import CRITERIA, clean_comments, filter_inappropriate  # noqa: E402


# State : 노드 사이에 주고받는 데이터
class PipelineState(TypedDict):
    company: str
    comments: list
    filtered: list
    cleaned: list
    augmented: list
    message: str


# 노드 : 06_pipeline 의 함수를 감싸고, "바뀐 값만" 돌려줌
def crawl(state):
    return {'comments': fetch_comments(state['company'], limit=20)}


def filter_bad(state):
    kept, _ = filter_inappropriate(state['comments'], CRITERIA['strict'])
    return {'filtered': kept}


def clean(state):
    return {'cleaned': clean_comments(state['filtered'])}


def augment(state):
    return {'augmented': augment_comments(state['cleaned'])}


def no_data(state):
    return {'message': f"{state['company']} 의 댓글을 찾지 못했습니다."}


# 조건부 엣지 : 다음에 실행할 노드 이름을 돌려줌
def has_comments(state):
    return 'filter_bad' if state['comments'] else 'no_data'


builder = StateGraph(PipelineState)
for name, node in [
    ('crawl', crawl),
    ('filter_bad', filter_bad),
    ('clean', clean),
    ('augment', augment),
    ('no_data', no_data),
]:
    builder.add_node(name, node)

builder.add_edge(START, 'crawl')
builder.add_conditional_edges('crawl', has_comments, ['filter_bad', 'no_data'])
builder.add_edge('filter_bad', 'clean')
builder.add_edge('clean', 'augment')
builder.add_edge('augment', END)
builder.add_edge('no_data', END)
graph = builder.compile()


if __name__ == '__main__':
    # stream_mode='updates' : 노드가 하나 끝날 때마다 {노드 이름: 바뀐 값} 을 돌려줌
    for step in graph.stream({'company': '삼성전자'}, stream_mode='updates'):
        for node, update in step.items():
            summary = {
                k: len(v) if isinstance(v, list) else v for k, v in update.items()
            }
            print(f'[{node}] 완료 -> {summary}')
