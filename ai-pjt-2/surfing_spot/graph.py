"""LangGraph 파이프라인: retrieve → generate. (F2006, F2007)

    START → retrieve(근거 검색) → generate(프롬프트 3으로 답변) → END

문서 수집·색인(프롬프트 1·2)은 시간이 걸리고 진행 표시가 필요해서 이 그래프 앞에서 화면(app.py)이 처리한다.
이 그래프는 '이미 색인된 자료로 답하는' 부분만 맡는다.
"""
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from citations import strip_empty_citations
from items import item_label
from llm import get_llm
from prompts import build_answer_messages
from retriever import retrieve


class RagState(TypedDict, total=False):
    item: dict        # 선택한 항목
    question: str
    history: list     # 같은 항목에서 직전에 오간 대화 [{"role", "content"}]
    evidence: list    # retrieve 결과 (번호 붙은 근거)
    answer: str       # generate 결과. 실패하면 빈 문자열


def build_graph(llm=None, retrieve_fn: Callable = retrieve):
    """그래프를 만든다. llm 과 retrieve_fn 은 시험할 때 가짜로 바꿔 끼울 수 있다."""

    def retrieve_node(state: RagState) -> dict:
        return {"evidence": retrieve_fn(state["item"], state["question"])}

    def generate_node(state: RagState) -> dict:
        messages = build_answer_messages(
            item_label(state["item"]), state["question"], state["evidence"], state.get("history")
        )
        try:
            return {"answer": strip_empty_citations((llm or get_llm()).invoke(messages).content)}
        except Exception:  # 키 누락, 네트워크 오류 등. 추적 정보는 화면에 내보내지 않는다. (NF2004)
            return {"answer": ""}

    graph = StateGraph(RagState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def run_rag(item: dict, question: str, history: list | None = None, app=None) -> RagState:
    """질문 하나를 처리한다. 돌려주는 값의 evidence 와 answer 를 화면이 쓴다."""
    return (app or build_graph()).invoke({"item": item, "question": question, "history": history or []})