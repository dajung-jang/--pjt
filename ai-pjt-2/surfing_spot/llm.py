"""LLM 클라이언트 (GMS). 프롬프트 1·2·3 이 모두 이 모델을 쓴다.

Streamlit 에 묶이지 않게 따로 둔다. 그래야 터미널 스크립트(collector.py 등)에서도 같은 모델을 쓸 수 있다.
화면(app.py)에서는 이 함수를 st.cache_resource 로 감싸서 한 번만 만든다.
"""
import os

from langchain_openai import ChatOpenAI

from config import GMS_BASE_URL, LLM_MODEL


def get_llm() -> ChatOpenAI:
    """키가 없으면 안내 문구와 함께 RuntimeError 를 낸다. (키 값 자체는 출력하지 않는다. NF2003)"""
    key = os.environ.get("GMS_KEY")
    if not key:
        raise RuntimeError("GMS_KEY가 없습니다. .env를 확인하세요.")
    return ChatOpenAI(model=LLM_MODEL, api_key=key, base_url=GMS_BASE_URL)