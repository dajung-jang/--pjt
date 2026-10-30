"""
참고 : CSS 선택자 한눈에 보기

실습에서 사용한 선택자를 실제 페이지와 비슷한 작은 HTML로 확인합니다.
인터넷 연결 없이 실행됩니다.

  - BeautifulSoup 의 select() / select_one()
  - Selenium 의 find_elements(By.CSS_SELECTOR, ...)
  => 두 곳 모두 같은 CSS 선택자 문법을 사용합니다
"""

from bs4 import BeautifulSoup

html = """
<div id="stock-content">
  <div data-id="base-ui-r1-viewport">
    <article data-section-name="커뮤니티__게시글">
      <span class="tc3tm85" style="--fold-after-lines: 3">삼전 가즈아</span>
      <button aria-label="좋아요">♥</button>
    </article>
    <article data-section-name="커뮤니티__게시글">
      <span class="x9ab12" style="--fold-after-lines: 3">오늘은 관망</span>
      <button aria-label="좋아요" class="active">♥</button>
    </article>
  </div>
</div>
"""
soup = BeautifulSoup(html, 'html.parser')


def show(selector):
    """선택자로 찾은 요소의 개수와 글자를 출력한다"""
    found = soup.select(selector)
    texts = [el.get_text(strip=True) for el in found]
    print(f'{selector:<55} -> {len(found)}개 {texts}')


# ------------------------------------------------------------
# 1. 기본 선택자
# ------------------------------------------------------------
print('[기본 선택자]')
show('span')  # 태그 이름
show('.tc3tm85')  # class
show('#stock-content')  # id
show('#stock-content span')  # A 안의 B (깊이 상관없음) -> 2개
show('#stock-content > span')  # A 바로 아래(자식) B -> 0개 (span 은 article 안에 있음)
show('article > span')  # article 바로 아래 span -> 2개

# ------------------------------------------------------------
# 2. 속성 선택자
# ------------------------------------------------------------
print('\n[속성 선택자]')
show('button[aria-label]')  # 속성이 있음
show("article[data-section-name='커뮤니티__게시글']")  # 값이 정확히 같음
show("span[style*='--fold-after-lines']")  # 값에 포함 (contains)
show("div[data-id^='base-ui-']")  # 값으로 시작
show("div[data-id$='-viewport']")  # 값으로 끝남
show("div[data-id^='base-ui-'][data-id$='-viewport']")  # 두 조건 모두 (AND)

# ------------------------------------------------------------
# 3. 클래스 이름 vs 역할(속성) : 사이트가 새로 배포되어 클래스 이름이 바뀌었다면?
# ------------------------------------------------------------
print('\n[배포 후 클래스 이름이 바뀐 상황]')
soup = BeautifulSoup(
    html.replace('tc3tm85', 'zz81kq0').replace('x9ab12', 'p0q2rr'), 'html.parser'
)
show('.tc3tm85')  # 0개 : 클래스 이름 기준은 깨짐
show("span[style*='--fold-after-lines']")  # 2개 : 역할 기준은 그대로 동작

# ------------------------------------------------------------
# 참고 : XPath 는 CSS 선택자가 아닙니다 (Selenium 의 By.XPATH 로만 사용)
#   //button[@aria-label='닫기']                  aria-label 이 '닫기'인 button
#   //input[@placeholder='검색어를 입력해주세요']  placeholder 가 일치하는 input
# ------------------------------------------------------------
