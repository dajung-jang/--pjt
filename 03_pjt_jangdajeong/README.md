# 03-pjt : 반응형 웹 페이지 구성

> AI 기반 도서 분석과 창작 지원 통합 솔루션 서비스 **ThRead** 의 메인 페이지 / 도서 상세 페이지를
> HTML, CSS, Bootstrap 5.3 으로 구현한 프로젝트입니다.

## 1. 프로젝트 구조

```
├── 01-navbar.html              # F301, F302  Navbar & Hero
├── 02-bestseller.html          # F303        Bestseller (Carousel)
├── 03-ai_recommendation.html   # F304        AI 추천 (Grid System)
├── 04-genre_list.html          # F305        장르별 도서 목록 (Flexbox)
├── 04-genre_list_grid.html     # F310 (심화) 장르별 도서 목록 (CSS Grid)
├── 05-popular_thread.html      # F306        인기 쓰레드 (Card + Pagination)
├── 06-main.html                # F307, F308, F309(심화), F310(심화)  메인 페이지 결합
├── 07-book_detail.html         # F311 (심화) "채식주의자" 도서 상세 페이지
├── assets/                     # 이미지, 폰트 (book_detail/book_cover.jpg 추가)
└── screenshots/                # 실행 브라우저 화면 캡쳐
```

## 2. 요구사항 구현 내용

| 번호 | 요구사항 | 구현 방법 |
| ---- | -------- | --------- |
| F301 | Navbar | `navbar-expand-sm` 으로 576px 미만에서 토글 버튼 전환, `position-absolute top-0` + `z-index: 1000` 으로 Hero 위에 고정. 로고 `Th`(#fff) / `Read`(#fe4a51) + GmarketSansTTFMedium, 메뉴는 SBAggro_L + hover 시 #fe4a51 |
| F302 | Hero | `<br class="d-412-break">` 를 기본 `display:none`, 576px 미만에서 `display:block` 으로 전환하여 "AI 기반 도서 분석 및" 뒤 줄바꿈 |
| F303 | Bestseller | Carousel 3개 슬라이드 × 4권 = 12권, `data-bs-ride="carousel"` 자동 전환, Next 컨트롤만 출력. 이미지 150×220 고정 + `object-fit: cover`, 좌측 제목 / 우측 Carousel (`col-md-2` / `col-md-10`) |
| F304 | AI 추천 | 섹션 폭 80% + `margin: 0 auto`, `row align-items-center` + `col-md-7` / `col-md-5` (7:5). "활동 데이터 기반" 은 #fe4a51 / SBAggroOTF_L / 1.3rem |
| F305 | 장르 목록 | Flexbox `flex-wrap` + `flex: 0 0 calc((100% - 3rem) / 4)` 로 4열, `aspect-ratio: 1/1` 로 고정 크기 유지. 이미지는 `width/height: 100%` + `object-fit: cover`, 장르명은 `position:absolute` 로 좌측 하단 오버레이. 576px 미만에서 `flex: 0 0 100%` 1열 |
| F306 | 인기 쓰레드 | Card + `row-cols-1 row-cols-sm-2 row-cols-lg-3` (모바일 1열, 데스크탑 3열). 카드 이미지 높이 200px 고정, `h-100` 카드 + `card-footer` 로 하단 고정, 도서명 #fe4a51. Pagination 은 `.thread .pagination .page-item .page-link` 로 Bootstrap 보다 높은 명시도 지정 → 테두리 제거, 활성 페이지 #fe4a51 |
| F307 | 메인 결합 | `06-main.html` 에 모든 섹션 결합. CSS 변수(`--thread-red`)와 공통 `.section-title`, `.section-inner` 로 디자인 시스템 통일, Footer 추가 |
| F308 | 로그아웃 Modal | 로그아웃 메뉴에 `data-bs-toggle="modal"`. 헤더 `btn-close`, 본문 중앙 정렬 메시지, 취소/로그아웃 버튼 모두 `data-bs-dismiss="modal"`, 기본 backdrop 으로 바깥 클릭 시 닫힘 |
| F309 | 베스트셀러 오버랩 | Bestseller 섹션에 `margin-top: -160px` + `z-index` + 흰 배경 카드 형태로 Hero 에 반만 걸치도록 재배치, Hero 텍스트와 AI 추천 섹션 간격 재조정 (모바일 -80px) |
| F310 | 장르 Grid | `grid-template-columns: repeat(5, 1fr)`, `grid-auto-rows`, `gap`, `grid-template-areas` 로 아이템마다 다른 크기 배치. 태블릿 3열, 모바일 1열 + `grid-row: span` 으로 높이 변화 |
| F311 | 도서 상세 | 메인의 "채식주의자" 클릭 시 이동. `min-height: 100vh` Hero 에 커버 배경 + 좌→우 검정→투명 `linear-gradient` 오버레이. 좌측: 제목, Bootstrap Icons `bi-archive` "담기" 버튼, 소개글, 작가 소개. 우측: `nav-tabs` (대여 가능 도서관 = Google Map iframe / 쓰레드 = 제목·작성자·좋아요 목록 + pagination + 쓰레드 작성 버튼) |

## 3. 학습한 내용

- **Bootstrap Grid / Breakpoint**: `sm(576px)` 기준 breakpoint 를 이용해 Navbar 토글, 카드 열 수, 레이아웃을 별도 미디어 쿼리 없이 클래스만으로 전환할 수 있었다.
- **명시도(Specificity)**: Bootstrap 의 `.page-link` 를 덮어쓰기 위해 부모 클래스를 조합한 선택자(`.thread .pagination .page-item .page-link`)를 사용했다. `!important` 없이 명시도로 해결하는 것이 유지보수에 유리하다.
- **Flexbox vs CSS Grid**: 1차원 나열(F305)은 Flexbox, 아이템마다 행/열을 다르게 차지하는 2차원 배치(F310)는 `grid-template-areas` 가 훨씬 직관적이었다.
- **position 과 z-index**: Navbar(absolute), Hero 오버레이, 오버랩된 Bestseller 섹션의 쌓임 순서를 `position` + `z-index` 로 제어했다.
- **navbar-expand-sm**: 576px 이상에서는 메뉴가 펼쳐지고, 그 미만에서는 토글 버튼으로 바뀐다.
- **d-sm-none을 <br>에 적용**: 576px 이상에서는 줄바꿈이 사라지고, 미만에서만 적용됩니다.
- **object-fit: cover**: 이미지 비율을 유지하면서 지정한 영역을 채우는 방법.

## 4. 어려웠던 부분

- **Navbar를 Hero 위에 띄우기**
Navbar 배경이 투명해야 하고 Hero 이미지 위에 겹쳐 보여야 해서 처음엔 배치가 어색했습니다.
Navbar에 `position-absolute top-0 start-0 w-100`을 주면 문서 흐름에서 빠져 Hero 위에 올라간다는 점,
그리고 Hero 안의 이미지와 오버레이도 `z-index`를 쓰고 있어서 Navbar에 `z-index: 1000`을
따로 지정해야 가려지지 않는다는 점을 이해하는 데 시간이 걸렸습니다.
 
- **Bootstrap 기본 스타일 덮어쓰기**
메뉴 글자색과 hover 색을 `#fe4a51`로 바꾸려 했는데, Bootstrap이 `.nav-link`에 이미 색을 지정하고
있어서 처음엔 적용이 되지 않았습니다. `.navbar-custom .nav-link`처럼 선택자를 더 구체적으로 써서
**명시도(specificity)**를 높여야 덮어쓸 수 있다는 것을 알게 되었습니다.
Pagination에서도 같은 문제가 있어서 `.thread .pagination .page-item.active .page-link`로 작성했습니다.
 
- **반응형 기준 정하기**
처음에는 `col-3`, `col-md-3`처럼 
고정 비율로 작성했는데, 모바일에서 이미지(150px 고정)가
칸 너비를 넘쳐서 겹쳐 보였습니다. 이미지 크기는 명세서가 고정하라고 했기 때문에,
이미지가 아니라 **한 줄에 몇 개를 놓을지**를 화면 폭에 따라 바꿔야 한다는 점을 배웠습니다.
Bestseller는 `col-6 col-lg-3`(모바일 2개, 데스크탑 4개)로 해결했습니다.
 
- **Carousel에서 4권씩 묶기**
`carousel-item` 하나가 한 슬라이드라서, 도서 한 권마다 item을 만들면 1권씩 넘어갑니다.
4권을 한 슬라이드에 보이게 하려면 `carousel-item` 안에 `row`와 `col`을 넣어 4권을 담아야 했습니다.
또 `data-bs-ride="carousel"`이 있어야 자동 전환되고, 버튼의 `data-bs-target`과 Carousel의 `id`가
일치해야 한다는 점도 확인했습니다.
Next 아이콘은 기본이 흰색이라 흰 배경에서 보이지 않아 붉은 원 배경을 직접 지정했습니다.
 
- **아이템 크기 고정과 이미지 채우기**
"아이템은 고정 크기를 유지하고, 이미지는 부모를 항상 채운다"는 두 조건을 함께 만족시키는 것이
까다로웠습니다. 부모(`genre-item`)에 `height`를 고정하고, 이미지에는 `width: 100%; height: 100%;
object-fit: cover`를 주면 비율이 달라도 찌그러지지 않고 채워진다는 것을 알게 되었습니다.
장르명은 부모에 `position: relative`, 글자에 `position: absolute`를 주어 왼쪽 하단에 겹쳤습니다.
 
- **카드 하단 고정**
카드마다 본문 길이가 달라서 하단의 저자/도서 이름 위치가 들쭉날쭉해졌습니다.
카드에 `h-100`을 주어 같은 행의 카드 높이를 맞추고, `card-body`가 남는 공간을 차지하게 해서
`card-footer`가 항상 아래에 위치하도록 했습니다.

## 5. 느낀 점

- 처음에는 클래스를 외워서 쓰는 느낌이었는데, 하나씩 화면 폭을 바꿔 보면서 **왜 그 클래스가
  필요한지** 이해하게 되었습니다. 특히 반응형은 "크기를 줄인다"가 아니라
  "화면 폭에 따라 배치를 바꾼다"는 관점이라는 것을 알게 되었습니다.
- 브라우저 개발자도구(F12)로 폭을 바꿔 가며 확인하는 습관이 중요하다는 것을 느꼈습니다.
  코드만 봤을 때는 맞아 보여도 실제 모바일 폭에서 깨지는 경우가 있었습니다.
- Bootstrap이 편하지만 기본 스타일을 덮어쓰려면 CSS 명시도를 알아야 해서,
  라이브러리만 쓰는 것이 아니라 CSS 기본기도 함께 필요하다는 것을 알았습니다.
- 생성형 AI의 도움을 받아 코드를 작성했지만, 제공된 코드의 의도를 바로 이해하지 못하면
  수정하기 어려웠습니다. 코드를 받은 뒤 각 줄이 왜 필요한지 질문하고 직접 확인하면서
  이해하는 과정이 필요하다고 느꼈습니다.
- 이전 직무에서 홈페이지를 관리해 본 경험이 있어서 화면 구성은 익숙했지만, 반응형과
  컴포넌트 단위로 구현하는 방식은 새로웠고 더 연습하고 싶다는 생각이 들었습니다.

