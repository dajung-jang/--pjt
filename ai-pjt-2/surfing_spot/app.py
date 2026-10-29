"""Surf Lab — 서핑 스팟 RAG 지식 서비스 (UI)

실행:
    streamlit run app.py

step7_skeleton.py 를 이어 쓴 파일입니다. 지금 단계(1번)에서 바뀐 것:
    - 항목 목록을 data/surf_items.json (277건) 에서 읽는다.
    - 화면 문구를 서핑 도메인으로 바꾸고, 안전 안내 문구를 항상 보여 준다.

아직 가짜인 것 (뒤 단계에서 진짜로 바뀐다)
    - collect_documents()  → 3~5번 단계: 검색어 추출, 위키 수집, 색인
    - 프롬프트             → prompts.py 로 분리 (7번 단계)
    - 대화 기록            → 항목별로 분리 (9번 단계)
"""

import re

import streamlit as st
import logging
from dotenv import load_dotenv

from collector import collect_documents
from config import APP_TITLE, DISCLAIMER, DOMAIN, META_COLLECTION
from finder import find_items
from graph import build_graph, run_rag
from guide import LEVELS, WIND_OPTIONS, guide_question, run_guide
from items import item_label, load_items
from llm import get_llm
from vectorstore import count_indexed, index_documents, sync_docs_index, sync_meta_index

load_dotenv()
logger = logging.getLogger(__name__)

# 답변 본문의 [근거 3], [근거 3, 5] 표기를 찾는다.
CITE_PATTERN = re.compile(r"\[근거\s*([\d,\s]+)\]")


@st.cache_data
def get_items() -> dict[str, dict]:
    """selectbox 에 보일 이름 → 항목 전체 정보. 파일은 한 번만 읽는다."""
    return {item_label(item): item for item in load_items()}


@st.cache_resource
def get_model():
    try:
        return get_llm()
    except RuntimeError as error:  # 키가 없을 때의 안내 문구만 보여 준다
        st.error(str(error))
        st.stop()


@st.cache_resource
def get_rag_app():
    """LangGraph 파이프라인(retrieve → generate)을 한 번만 만든다."""
    return build_graph(llm=get_model())

@st.cache_resource
def ensure_meta_index(total: int) -> str:
    """항목 메타 색인이 비어 있으면 앱을 시작할 때 한 번 자동으로 채운다. 실패하면 이유 문구만 돌려준다."""
    try:
        sync_meta_index(list(get_items().values()))
        return ""
    except Exception:
        return "항목 색인을 만들지 못했습니다. GMS_KEY 와 네트워크를 확인한 뒤 `python build_index.py` 를 실행하세요."


@st.cache_data(show_spinner=False)
def find_item_labels(condition: str) -> list[str]:
    """조건에 맞는 항목 이름 목록. 같은 조건은 다시 계산하지 않는다. 실패하면 예외가 나가고 캐시되지 않는다."""
    return [item_label(item) for item in find_items(condition, llm=get_model())]


def pick_item(name: str) -> None:
    """조건 검색 결과의 버튼을 누르면 해당 항목을 선택한다. (콜백이라 selectbox 가 만들어지기 전에 실행된다)"""
    st.session_state["item"] = name

def prepare_docs(item: dict, question: str, status) -> str:
    """질문에 필요한 문서를 수집하고 색인한다. 상태창에 진행 문구를 띄우고, 결과 요약 문구를 돌려준다. (F2012)

    수집이 실패해도 멈추지 않는다. 이미 색인된 자료로 이어서 답한다. (NF2004)
    """
    try:
        result = collect_documents(item, question, model=get_model(), progress=lambda m: status.update(label=m))
        index_documents(result["new_documents"])  # 새로 받은 문서만 청킹해서 색인
        sync_docs_index()  # 색인이 비었거나 어긋났으면 저장된 문서로 복구한다
        return f"새 문서 {len(result['new_documents'])}건 · 이미 있던 문서 {len(set(result['reused_titles']))}건"
    except Exception:
        return "문서 수집에 실패해 이미 있는 자료로 답합니다"

def cited_sources(answer: str, sources: list[dict]) -> list[tuple[int, dict]]:
    """답변이 실제로 인용한 근거만 (번호, 문서)로 돌려준다. 인용이 없으면 빈 목록. (F2008)"""
    numbers = {
        int(n) for group in CITE_PATTERN.findall(answer)
        for n in group.split(",") if n.strip().isdigit()
    }
    return [(i, s) for i, s in enumerate(sources, start=1) if i in numbers]


def render_sources(answer: str, sources: list[dict]) -> None:
    """답변 아래 근거 목록. 인용한 것만 보여 주고, 인용이 없으면 안내한다."""
    used = cited_sources(answer, sources)
    if not used:
        st.caption("ⓘ 답변에 인용된 근거가 없습니다.")
        return
    with st.expander(f"답변에 사용한 근거 {len(used)}건"):
        for number, source in used:
            kind = "항목 메타데이터" if source.get("type") == "meta" else source.get("source") or "외부 문서"
            link = f" · [원문]({source['url']})" if source.get("url") else f" · {source.get('source', '')}"
            st.markdown(f"**[근거 {number}]** `{kind}` {source['title']}{link}")


st.set_page_config(page_title=APP_TITLE, page_icon="🏄")
st.title(f"🏄 {APP_TITLE}")
st.caption("근거를 찾아 답하고 출처를 함께 보여 주는 서핑 지식 서비스 — 개발 중 ")
st.warning(DISCLAIMER, icon="⚠️")

items = get_items()

# 대화 기록은 항목(해변)마다 따로 둔다. {항목 id: [메시지, ...]} (F2009)
if "chats" not in st.session_state:
    st.session_state.chats = {}

index_problem = ensure_meta_index(len(items))

with st.sidebar:
    st.header("조건으로 찾기")  # F2011
    condition = st.text_input("원하는 조건", key="condition", placeholder="예: 강원도 양양 서핑 스팟")
    if condition.strip():
        try:
            with st.spinner(""):
                matches = find_item_labels(condition.strip())
        except Exception:  # 키 누락, 네트워크 오류 등. 추적 정보는 내보내지 않는다. (NF2004)
            logger.exception("조건 검색에 실패했습니다")  # 화면에는 내보내지 않고 터미널 로그에만 남긴다 (NF2004)
            matches = None
            st.error("조건 검색에 실패했습니다. 잠시 뒤 다시 시도해 주세요.")
        if matches is not None and not matches:
            st.caption("조건에 맞는 항목을 찾지 못했습니다.")
        for name in matches or []:
            st.button(name, key=f"pick_{name}", on_click=pick_item, args=(name,), width="stretch")
    st.divider()
    st.header(f"{DOMAIN} 선택")

    label = st.selectbox(
        f"질문할 {DOMAIN}", list(items), index=None, key="item", placeholder=f"{DOMAIN}을(를) 고르세요"
    )
    indexed = count_indexed(META_COLLECTION)
    st.caption(f"항목 메타데이터: {len(items)}건")
    st.caption(f"메타데이터 색인: {indexed}건")
    if indexed == 0:  # 색인이 없을 때의 안내 (F2012)
        st.warning(index_problem or "색인이 없습니다. 터미널에서 `python build_index.py` 를 먼저 실행하세요.")
    if st.button("이 항목 대화 지우기", width="stretch", disabled=not label):
        st.session_state.chats[items[label]["id"]] = []
    talked = [name for name, it in items.items() if st.session_state.chats.get(it["id"])]
    if talked:  # 대화한 항목 목록
        st.caption("대화한 항목: " + ", ".join(talked))

if not label:
    st.info(f"왼쪽에서 질문할 {DOMAIN}을(를) 먼저 고르세요.")
    st.stop()

item = items[label]
st.subheader(label)
if item.get("size"):
    st.caption(f"{item['type']} · {item['size']}")

messages = st.session_state.chats.setdefault(item["id"], [])  # 이 항목의 대화만 꺼낸다

# ── 서핑 특화: 오늘 조건으로 보는 입수 판단 가이드 (F2010) ────────────
if "guides" not in st.session_state:
    st.session_state.guides = {}

with st.expander("🌊 오늘 조건으로 입수 판단 가이드"):
    st.caption("실시간 정보를 불러오지 않습니다. 지금 현장에서 직접 보고 들은 조건을 입력하세요.")
    with st.form(f"guide_form_{item['id']}"):
        wave = st.number_input("파도 높이 (m, 눈으로 본 대략값)", min_value=0.0, max_value=6.0, value=0.5, step=0.1)
        wind = st.selectbox("바람 방향", WIND_OPTIONS)
        level = st.selectbox("내 숙련도", LEVELS)
        blocked = st.checkbox("입수 통제나 경보(깃발, 방송)가 있다")
        submitted = st.form_submit_button("가이드 만들기", width="stretch")
    if submitted:
        conditions = {"wave": wave, "wind": wind, "level": level, "blocked": blocked}
        with st.status("가이드를 준비하고 있습니다...", expanded=False) as guide_status:
            if not blocked:
                guide_summary = prepare_docs(item, guide_question(conditions), guide_status)
            else:
                guide_summary = "입수 통제 중이라 조건 분석 없이 안내합니다"
            guide_status.update(label=guide_summary, state="complete")
        st.session_state.guides[item["id"]] = run_guide(item, conditions, llm=get_model())
    saved = st.session_state.guides.get(item["id"])
    if saved:
        if not saved["answer"]:
            st.error("가이드를 만들지 못했습니다. 키와 네트워크를 확인해 주세요.")
        elif not saved["evidence"]:
            st.error(saved["answer"])
        else:
            st.markdown(saved["answer"])
            render_sources(saved["answer"], saved["evidence"])

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message["content"], message.get("sources", []))

question = st.chat_input(f"이 {DOMAIN}에 대해 궁금한 점을 물어보세요")

if question:
    messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        history = messages[:-1]  # 방금 한 질문은 빼고, 직전 대화만 넘긴다
        with st.status("관련 문서를 찾고 있습니다...", expanded=False) as status:
            summary = prepare_docs(item, question, status)
            status.update(label=summary, state="complete")

        with st.spinner("답변을 만드는 중..."):
            state = run_rag(item, question, history, app=get_rag_app())
        answer, sources = state["answer"], state["evidence"]

        if answer:
            st.markdown(answer)
            render_sources(answer, sources)  # 근거 목록
        else:
            st.error("답변을 만들지 못했습니다. 키와 네트워크를 확인해 주세요.")

    if answer:
        messages.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )