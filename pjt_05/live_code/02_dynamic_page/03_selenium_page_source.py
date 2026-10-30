"""
동적 페이지 크롤링 ③ page_source로 "그려진 뒤의 HTML" 가져오기

학습 목표
  1. Selenium이 가져온 HTML(page_source)과 requests가 가져온 HTML의 차이를 확인한다
  2. 같은 BeautifulSoup 코드가 이번에는 인용문을 찾는 것을 확인한다

역할 분담
  Selenium      : 브라우저로 페이지를 열어 자바스크립트까지 실행 => 완성된 HTML 확보
  BeautifulSoup : 완성된 HTML에서 원하는 요소 검색 (01_quotes_static.py 와 같은 방법)

  requests      : HTML 받기     (JS 실행 X)  -> 0개
  Selenium      : HTML 받기 + JS 실행        -> 10개
  => "HTML을 어떻게 받느냐"만 바뀌고, 찾는 코드는 그대로입니다

진행 방법
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제한 뒤 실행합니다
"""

from bs4 import BeautifulSoup
from selenium import webdriver

URL = 'http://quotes.toscrape.com/js/'


# ------------------------------------------------------------
# [STEP 1] 브라우저로 열고 page_source 가져오기
# ------------------------------------------------------------
# driver.page_source
#   - "지금 브라우저 화면"의 HTML 전체를 문자열로 돌려줍니다
#   - 자바스크립트가 실행된 뒤의 HTML이라 인용문(div.quote)이 들어 있습니다
#
# driver.quit()
#   - 브라우저와 드라이버 프로그램을 함께 종료합니다
#   - 필요한 HTML은 이미 html_doc 변수에 담았으므로 브라우저는 더 이상 필요 없습니다
#   - quit() 을 빼먹으면 실행할 때마다 크롬 창과 드라이버가 계속 쌓여 컴퓨터가 느려집니다
#
# 확인 포인트
#   - 01_quotes_js_requests_fail.py 에서 출력한 HTML 길이와 비교하면 어떤가요?

driver = webdriver.Chrome()
driver.get(URL)
html_doc = driver.page_source
print('HTML 길이:', len(html_doc), '글자')
driver.quit()


# ------------------------------------------------------------
# [STEP 2] 정적 페이지와 같은 코드로 인용문 찾기
# ------------------------------------------------------------
# 아래 코드는 01_quotes_static.py 의 STEP 7과 같은 방식입니다
#   1. div.quote (인용문 상자)를 모두 찾고
#   2. 상자 안에서 span.text (인용문), small.author (저자)를 꺼냅니다
#
# 확인 포인트
#   - requests 로는 0개였던 인용문이 몇 개 나오나요?
#   - 01_quotes_static.py 의 결과와 비교해 보세요

soup = BeautifulSoup(html_doc, 'html.parser')
quotes = soup.select('div.quote')
print('찾은 인용문:', len(quotes), '개')
for idx, quote in enumerate(quotes, 1):
    text = quote.select_one('span.text').text
    author = quote.select_one('small.author').text
    print(f'{idx:02d}. {author} : {text[:40]}')
