"""
동적 페이지 크롤링 ① requests로는 왜 안 될까?

학습 목표
  1. 정적 페이지에서 쓰던 코드를 동적 페이지에 그대로 실행해 결과를 비교한다
  2. 받아 온 HTML에 데이터 대신 무엇이 들어 있는지 확인한다

실습 사이트 : http://quotes.toscrape.com/js/
  - 01_quotes_static.py 와 같은 사이트의 "자바스크립트 버전"입니다
  - 브라우저로 열면 인용문이 똑같이 보입니다
  - 그런데 "페이지 소스 보기"를 열면 div.quote 대신 <script> 안에 데이터가 들어 있습니다

정적 페이지 vs 동적 페이지
  정적 : 서버가 완성된 HTML을 보냄             => requests로 받은 HTML에 데이터가 있음
  동적 : 서버가 "HTML + 그리는 코드(JS)"를 보냄 => 브라우저가 JS를 실행해야 데이터가 화면에 생김

진행 방법
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제한 뒤 실행합니다
"""

import requests
from bs4 import BeautifulSoup

URL = 'http://quotes.toscrape.com/js/'


# ------------------------------------------------------------
# [STEP 1] 정적 페이지와 같은 코드로 요청하기
# ------------------------------------------------------------
# 01_quotes_static.py 에서 인용문 10개를 찾았던 코드와 "주소만" 다릅니다
#   - requests.get()        : HTML 받아 오기
#   - BeautifulSoup()       : 검색 가능한 구조로 바꾸기
#   - select('div.quote')   : 인용문 상자 모두 찾기
#
# 확인 포인트
#   - 상태 코드는 200(성공)인데, 찾은 인용문은 몇 개인가요?
#   - 요청은 성공했는데 데이터가 없다면, 문제는 "요청"일까요 "받아 온 내용"일까요?

response = requests.get(URL, timeout=10)
html_doc = response.text
soup = BeautifulSoup(html_doc, 'html.parser')
print('상태 코드:', response.status_code)
print('HTML 길이:', len(html_doc), '글자')
quotes = soup.select('div.quote')
print('찾은 인용문:', len(quotes), '개')


# ------------------------------------------------------------
# [STEP 2] 인용문 대신 무엇이 들어 있을까?
# ------------------------------------------------------------
# <script> 태그 = HTML 안에 들어 있는 자바스크립트 코드
#   - <script src="파일주소"> : 외부 JS 파일을 불러오는 스크립트
#   - <script> 코드 </script>  : HTML 안에 코드가 직접 적힌 스크립트 (src 속성 없음)
#
# find_all('script', src=False) : src 속성이 "없는" script 만 찾기
#
# 브라우저는 이 코드를 실행해서 div.quote 를 화면에 만들어 냅니다
# requests 는 HTML을 "받기만" 하고 자바스크립트를 실행하지 않습니다
# => 그래서 인용문은 코드 안의 "글자"로만 존재하고, div.quote 는 0개입니다
#
# 확인 포인트
#   - 출력된 코드 안에 인용문 문장이 보이나요?
#   - 이 코드를 실행해 줄 "브라우저"가 필요하다는 것이 다음 실습(Selenium)의 출발점입니다

for script in soup.find_all('script', src=False):
    code = script.get_text(strip=True)
    if code:
        print('----- <script> 앞부분 -----')
        print(code[:300])
        break
else:
    print('HTML 안에 직접 적힌 <script>를 찾지 못했습니다.')
