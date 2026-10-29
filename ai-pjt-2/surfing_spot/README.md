# Surf Lab — 서핑 스팟 RAG 지식 서비스

SSAFY AI 코어 프로젝트 2회차. 서핑 스팟(해수욕장)을 고르고 질문하면, 색인된 문서만 근거로 답하고
그 근거의 종류·제목·원문 출처를 함께 보여주는 RAG 서비스입니다.
서핑과 해수욕은 안전과 직결되므로 화면에 면책 안내를 항상 표시합니다.

- 항목 메타데이터 277건(공공데이터포털) + 한국어 위키백과 문서를 두 개의 Chroma 컬렉션으로 나누어 색인합니다.
- 질문하면 필요한 위키 문서를 그때그때 수집·색인하고(캐시 있음), LangGraph(retrieve → generate)로 답합니다.
- 실시간 날씨·파고 API는 쓰지 않습니다. "오늘 조건"은 사용자가 직접 입력합니다.

## 개발 환경 및 사용 기술

| 구분 | 내용 |
|---|---|
| 언어 / 환경 | Python 3.12, venv |
| UI | Streamlit 1.62.0 |
| RAG 프레임워크 | LangChain 1.3.14, LangGraph 1.2.10 (retrieve → generate 두 노드), langchain-text-splitters 1.1.2 |
| Vector DB | ChromaDB 1.5.9 (langchain-chroma 1.1.0), 컬렉션 2개(`surf_meta`, `surf_docs`) |
| LLM / 임베딩 | SSAFY GMS(OpenAI 호환) — 채팅 `gpt-5.4-nano`, 임베딩 `text-embedding-3-small` (1536차원) |
| 외부 문서 | 한국어 위키백과 MediaWiki API (requests) |
| 데이터 | 공공데이터포털 해양수산부_해수욕장정보목록 CSV → JSON |
| 설정 / 키 | `config.py`, `.env` (python-dotenv) |

전체 의존성과 버전은 `requirements.txt` 에 있습니다.

## 실행 방법

```bash
# 1. 키 설정 (.env 는 git 과 제출물에 포함하지 않는다)
cp .env.example .env        # GMS_KEY, WIKI_CONTACT(영문 이메일 또는 URL) 를 채운다

# 2. 설치
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 색인 (아래 '데이터 준비 및 색인 절차' 참고)
python build_index.py

# 4. 실행
streamlit run app.py
```

앱을 켜기 전에 색인이 비어 있어도 첫 실행 때 항목 색인은 자동으로 채워집니다.
저장된 위키 문서(`data/cache/docs/`)가 있으면 문서 색인도 질문할 때 자동 복구됩니다.

## 기능

### 필수 기능 (F2001 ~ F2012)

| 번호 | 기능 | 구현 위치 |
|---|---|---|
| F2001 | 항목 277건 로드, 항목 1건을 하나의 색인 텍스트로 구성 | `items.py` |
| F2002 | 항목 텍스트를 `surf_meta` 컬렉션에 색인 (id = 항목 id, 재실행해도 중복 없음) | `vectorstore.py`, `build_index.py` |
| F2003 | 프롬프트 1: 질문에서 위키 검색어 추출 (항목 자체 검색어는 항상 포함) | `collector.py`, `prompts.py` |
| F2004 | 프롬프트 2: 후보 문서 선별 → 본문·원문 URL 수집, 검색어 캐시 | `collector.py`, `wiki_client.py` |
| F2005 | 문서 청킹(크기·중복은 설정) → `surf_docs` 컬렉션 색인 | `vectorstore.py`, `build_docs_index.py` |
| F2006 | 선택 항목 메타 청크 1건 + 문서 청크 Top-k 병합, 중복 제거 | `retriever.py` |
| F2007 | LangGraph retrieve / generate 두 노드, 프롬프트 3으로 근거만 사용해 답변 | `graph.py`, `prompts.py` |
| F2008 | 답변에서 인용된 근거만 표시, 인용이 없으면 안내 | `app.py`, `citations.py` |
| F2009 | 항목 선택 + 채팅, 대화 기록은 항목별로 분리 | `app.py` |
| F2010 | 서핑 특화: 오늘 조건(파도 높이·바람 방향·숙련도)으로 보는 입수 판단 가이드 | `guide.py`, `prompts.py` |
| F2011 | 자연어 조건 → 메타 색인 후보 검색 → 프롬프트 5로 조건에 맞는 항목만 선별 | `finder.py`, `retriever.py` |
| F2012 | 진행 상태 표시, 색인 없음·키 누락·검색 실패 안내, 면책 문구 | `app.py` |

### 심화 기능 (F2013 ~ F2016)

| 번호 | 상태 |
|---|---|
| F2014 MMR | 설정(`USE_MMR`, `MMR_FETCH_K`)으로 켤 수 있게 구현. 비교 결과는 `docs/03_검증결과.md` 에 기록 |
| F2015 RAG 전후 비교 | 선택하지 않음 |
| F2016 PDF 결합 | 선택하지 않음 |
| F2013 프론트엔드 직접 구현 | 선택하지 않음 |

## 데이터 준비 및 색인 절차

항목 데이터와 위키 후보 문서 목록은 저장소에 포함되어 있습니다(`data/surf_items.json`, `data/wiki_docs.json`).
원본 CSV에서 다시 만들려면 `python import_beaches_csv.py` 를 실행합니다.

| 순서 | 명령 | 하는 일 |
|---|---|---|
| 1 | `python items.py` | 항목 수·필수 필드 검증, 색인 텍스트 1건 출력 |
| 2 | `python build_index.py` | 항목 메타데이터를 `surf_meta` 에 색인 (두 번 실행해도 건수 동일) |
| 3 | `python collector.py --common` | 공통 개념 문서(서핑, 파도, 이안류 등)를 수집해 `data/cache/docs/` 에 저장 |
| 4 | `python build_docs_index.py "이안류 대처"` | 저장된 문서를 청킹해 `surf_docs` 에 색인, 비슷한 청크 3건 확인 |
| 5 | `python retriever.py 죽도 "질문"` | 근거 목록(번호·유형·범위) 확인 |
| 6 | `python show_graph.py` | LangGraph 노드·연결 출력 |

질문하면 앱이 `collector.py` → 색인 → 검색 → 답변 순서로 자동 처리하므로 3~4번은 사전 점검용입니다.
`data/cache/`(수집한 위키 문서와 검색어 기록)는 저장소에 포함되어 있어서, 위키를 다시 부르지 않아도 첫 질문 때 문서 색인이 자동으로 복구됩니다.
색인을 처음부터 다시 만들려면 `chroma_db/` 와 `data/cache/` 를 함께 지웁니다. (한쪽만 지우면 캐시와 색인이 어긋납니다)

## 설정 (`config.py`)

청크 크기(`CHUNK_SIZE`), 중복 길이(`CHUNK_OVERLAP`), 문서 근거 수(`TOP_K_DOCS`),
검색 방식(`USE_MMR`, `MMR_FETCH_K`), 수집 한도, 호출 간격을 이 파일에서만 바꿉니다.
값을 바꾸고 `python build_docs_index.py` 를 다시 실행하면 청크 수가 달라집니다.

## 폴더 구조

```
app.py                 UI (Streamlit)
config.py              설정
items.py               항목 로드·검증·색인 텍스트           ← 도메인(서핑)에 묶인 부분
import_beaches_csv.py  원본 CSV → 항목 JSON                  ← 도메인(서핑)에 묶인 부분
check_wiki_coverage.py 위키 문서 존재 여부 점검 스크립트
wiki_client.py         위키백과 호출 (User-Agent, 재시도, 호출 간격)
prompts.py             프롬프트 5개
collector.py           검색어 추출·문서 선별·수집·캐시
vectorstore.py         컬렉션 열기, 항목·문서 색인, 색인 복구
build_index.py         항목 색인 스크립트
build_docs_index.py    문서 색인 스크립트
retriever.py           근거 검색·병합·중복 제거, 후보 항목 검색
graph.py               LangGraph (retrieve / generate)
citations.py           답변 후처리 (근거 없는 문장의 번호 제거)
finder.py              조건 기반 항목 탐색 (F2011)
guide.py               입수 판단 가이드 (F2010)
llm.py                 LLM 클라이언트
show_graph.py          그래프 구조 출력
data/                  항목 JSON, 원본 CSV, 위키 후보 문서 목록, 수집 캐시
docs/                  요구사항 정의서, RAG 설계문서, 검증 결과
```

## 데이터 · 문서의 출처와 이용 조건

| 데이터 | 출처 | 이용 조건 |
|---|---|---|
| 항목 메타데이터 277건 | 공공데이터포털 해양수산부_해수욕장정보목록 (수정일 2025-07-31) https://www.data.go.kr/data/15056087/fileData.do | 이용허락범위 제한 없음, 무료 |
| 외부 문서 | 한국어 위키백과 (MediaWiki API, `data/cache/docs/` 에 본문과 원문 URL 저장) | CC BY-SA 4.0. 화면의 근거 목록에 문서 제목과 원문 링크를 표시해 출처를 밝힘 |

서핑 스팟 4곳(죽도, 인구, 송정, 중문색달)은 직접 표시한 항목이며, 난이도·특징·주의사항은 출처가 없어 비워 두었습니다.
비어 있는 속성은 추측으로 채우지 않습니다.

## 안전 안내

서핑과 해수욕은 안전과 직결됩니다. 이 서비스의 답변은 전문가나 안전요원의 판단을 대신하지 않으며,
입수 전에 현장의 기상 상황과 안내를 반드시 확인해야 합니다.