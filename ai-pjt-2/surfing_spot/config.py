"""프로젝트 설정 모음.

값을 바꿔 가며 비교할 것(청크 크기, Top-k 등)은 코드 안이 아니라 여기서만 바꾼다.
(요구사항 F2005, F2006, 기획 2.5절)

키 값(GMS_KEY, WIKI_CONTACT)은 여기에 쓰지 않는다. .env 파일에 두고 환경변수로 읽는다. (NF2003)
"""
from pathlib import Path

# ── 경로 ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ITEMS_PATH = DATA_DIR / "surf_items.json"          # 항목 메타데이터 (277건)
WIKI_DOCS_PATH = DATA_DIR / "wiki_docs.json"       # 위키 후보 문서 목록
QUERY_CACHE_PATH = DATA_DIR / "cache" / "queries.json"   # 이미 수집한 검색어 기록 (NF2002)
CHROMA_DIR = BASE_DIR / "chroma_db"                # 벡터 DB 저장 폴더 (자동 생성)

# ── 서비스 ──────────────────────────────────────────────────────────
DOMAIN = "서핑 스팟"
APP_TITLE = "Surf Lab"
# 안전과 직결된 도메인이라 화면에 항상 표시한다. (F2012)
DISCLAIMER = (
    "서핑과 해수욕은 안전과 직결됩니다. 이 서비스의 답변은 전문가나 안전요원의 판단을 대신하지 않으며, "
    "입수 전에 현장의 기상 상황과 안내를 반드시 확인하세요."
)

# ── LLM (GMS) ───────────────────────────────────────────────────────
GMS_BASE_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/"
LLM_MODEL = "gpt-5.4-nano"
EMBEDDING_MODEL = "text-embedding-3-small"   # GMS에서 동작 확인함 (벡터 길이 1536)

# ── 검색어 추출 (F2003) ─────────────────────────────────────────────
MAX_QUERIES = 3                     # 프롬프트 1이 뽑을 검색어 최대 개수 (항목 자체의 검색어는 따로 항상 추가)

# ── 위키 수집 (F2004) ───────────────────────────────────────────────
SEARCH_LIMIT = 5                    # 검색어 하나당 위키 후보 수
MAX_ITEM_DOCS = 2                   # 항목 자체를 다룬 문서를 최대 몇 건까지 가져올지
MAX_SELECT_DOCS = 3                 # 프롬프트 2가 한 질문에서 고를 문서 최대 수
MIN_DOC_CHARS = 300                 # 선별된 문서가 이보다 짧으면 제외한다 (항목 자체 문서는 예외)
DOCS_DIR = DATA_DIR / "cache" / "docs"   # 수집한 문서 본문을 저장하는 폴더. 색인(5번)은 여기서 읽는다.

# ── 컬렉션 ──────────────────────────────────────────────────────────
META_COLLECTION = "surf_meta"       # 항목 메타데이터. 항목당 1청크, id 는 항목 id
DOCS_COLLECTION = "surf_docs"       # 위키 문서 청크. id 는 "항목ID:문서ID:순번"
COMMON_ITEM_ID = "common"           # 모든 항목이 함께 쓰는 개념 문서(서핑, 파도, 이안류 등)의 item_id

# ── 청킹 (F2005) ────────────────────────────────────────────────────
CHUNK_SIZE = 1000                   # 한 청크 글자 수
CHUNK_OVERLAP = 200                 # 앞뒤 청크와 겹치는 글자 수
MIN_CHUNK_CHARS = 50                 # 소제목(== ... ==)을 뺀 본문이 이보다 짧은 청크는 색인하지 않는다 (제목만 있는 청크, 참고문헌 목록 등)

# ── 검색 (F2006, F2014) ─────────────────────────────────────────────
TOP_K_DOCS = 5                      # 문서 청크 근거 수. 선택한 항목의 메타 청크 1건은 따로 항상 포함한다.
USE_MMR = False                     
MMR_FETCH_K = 30                    # MMR 일 때 먼저 넉넉히 가져올 후보 수

# ── 위키 호출 예절 (NF2006) ─────────────────────────────────────────
WIKI_SLEEP_SEC = 0.5                # 호출 사이에 쉬는 시간

# ── 조건 기반 항목 탐색 (F2011) ────────────────────────────────────
CONDITION_CANDIDATES = 10           # 의미 유사도 검색과 키워드 검색이 각각 가져올 후보 수
CONDITION_POOL = 20                 # 두 후보를 합친 뒤 프롬프트 5에 넘길 최대 후보 수
CONDITION_MAX_RESULTS = 8           # 프롬프트 5가 후보 중 골라 보여 줄 최대 항목 수