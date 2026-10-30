"""
정적 페이지 크롤링: requests + BeautifulSoup

학습 목표
  1. requests로 웹 페이지의 HTML 문자열을 받아온다
  2. BeautifulSoup으로 HTML을 태그 구조로 바꿔 원하는 요소를 찾는다
  3. find / find_all 과 select_one / select 의 차이를 결과로 비교한다

실습 사이트 : http://quotes.toscrape.com/tag/love/
  - 크롤링 연습용으로 공개된 사이트 (마음껏 요청해도 되는 곳)
  - 서버가 "완성된 HTML"을 그대로 보내주는 정적 페이지
  - 브라우저에서 이 주소를 열고 마우스 오른쪽 => "페이지 소스 보기"를 눌러 보세요
    화면에 보이는 인용문이 소스 안에 글자 그대로 들어 있습니다

진행 방법
  - [STEP 1]부터 순서대로 진행합니다
  - 각 STEP의 주석 처리된 코드 블록을 마우스로 선택하고 Ctrl + / 를 누르면 주석이 해제됩니다
  - STEP 하나를 해제할 때마다 실행해서, "확인 포인트"의 질문에 답해 보세요
  - 뒤 STEP은 앞 STEP에서 만든 변수(html_doc, soup)를 사용하므로 순서를 건너뛰면 NameError가 납니다
"""

import requests
from bs4 import BeautifulSoup

URL = 'http://quotes.toscrape.com/tag/love/'


# ------------------------------------------------------------
# [STEP 1] requests로 사이트 접속하기
# ------------------------------------------------------------
# requests.get(URL)
#   - 브라우저 주소창에 URL을 입력하고 Enter를 누르는 것과 같은 요청입니다
#   - 다만 브라우저처럼 화면을 그리지 않고, 서버가 보낸 "응답"만 받아 옵니다
#   - timeout=10 : 10초 안에 응답이 없으면 무한정 기다리지 않고 에러를 냅니다
#
# response (응답 객체)
#   - 그냥 print하면 <Response [200]>처럼 상태 코드만 짧게 보입니다
#   - 상태 코드 : 200 = 성공 / 404 = 페이지 없음 / 403 = 접근 거부 / 500 = 서버 오류
#   - response.text : 서버가 보낸 HTML을 "문자열(str)" 하나로 담고 있습니다
#
# 확인 포인트
#   - 상태 코드가 200인가요?
#   - 출력된 HTML 앞부분이 "페이지 소스 보기"에서 본 내용과 같은가요?

response = requests.get(URL, timeout=10)
print(response)
print('상태 코드:', response.status_code)
html_doc = response.text
print('HTML 길이:', len(html_doc), '글자')
print(html_doc[:500])  # 전체는 너무 길어서 앞부분 500글자만 미리보기


# ------------------------------------------------------------
# [STEP 2] BeautifulSoup으로 HTML 파싱하기
# ------------------------------------------------------------
# 왜 필요할까?
#   - html_doc 은 13,000글자가 넘는 긴 "문자열"입니다
#   - 문자열에서 "인용문만" 찾으려면 글자를 하나하나 비교해야 해서 매우 불편합니다
#
# BeautifulSoup(문자열, 'html.parser')
#   - HTML 문자열을 태그들이 부모-자식으로 연결된 "트리 구조"로 바꿔 줍니다
#   - 책을 통째로 읽는 대신, "목차"가 생겨서 원하는 장(태그)으로 바로 갈 수 있게 되는 것
#   - 'html.parser' : 파이썬에 기본으로 들어 있는 HTML 해석기 (따로 설치 불필요)
#   - BeautifulSoup은 웹에 접속하지 않습니다. 이미 받아 온 HTML을 "분석"만 합니다
#
# 확인 포인트
#   - html_doc 과 soup 의 type 은 각각 무엇인가요?
#   - soup.title 과 soup.title.text 의 출력은 어떻게 다른가요?

soup = BeautifulSoup(html_doc, 'html.parser')
print(type(html_doc))  # <class 'str'> : 그냥 문자열
print(type(soup))  # <class 'bs4.BeautifulSoup'> : 검색 가능한 객체
print(soup.title)  # <title> 태그 전체 (태그 + 글자)
print(soup.title.text)  # <title> 태그 안의 글자만


# ------------------------------------------------------------
# [STEP 3] find() : 조건에 맞는 "첫 번째" 요소 하나
# ------------------------------------------------------------
# soup.find('태그명')
#   - 위에서부터 찾아 내려가다가 "처음 만난" 태그 하나만 돌려줍니다
#   - 페이지에 <a> 태그가 50개가 넘어도 결과는 1개입니다
#
# soup.find('div', class_='header-box')
#   - class 로 찾을 때는 class_ (뒤에 밑줄)를 씁니다
#   - 파이썬에서 class 는 "클래스를 만드는 예약어"라서 이름으로 그대로 쓸 수 없기 때문입니다
#
# .text vs .get_text(' ', strip=True)
#   - .text 는 HTML 들여쓰기에 쓰인 줄바꿈·공백까지 그대로 가져옵니다
#     그래서 출력에 \n 이 잔뜩 섞여 나옵니다 (repr() 로 출력하면 눈에 보입니다)
#   - .get_text(' ', strip=True) 는 조각마다 앞뒤 공백을 지우고 ' ' 한 칸으로 이어 붙입니다
#
# 확인 포인트
#   - 첫 번째 a 태그는 화면의 어디에 있는 글자인가요?
#   - header-box 를 .text 로 출력한 결과와 get_text 로 출력한 결과는 어떻게 다른가요?

first_a = soup.find('a')  # 첫 번째 <a> 태그
print('첫 번째 a 태그:', first_a)
print('첫 번째 a 태그의 글자:', first_a.text)
header = soup.find('div', class_='header-box')  # class="header-box"인 첫 <div>
print('header-box (.text)    :', repr(header.text))
print('header-box (get_text) :', header.get_text(' ', strip=True))


# ------------------------------------------------------------
# [STEP 4] find_all() : 조건에 맞는 요소 "전체"
# ------------------------------------------------------------
# soup.find_all('태그명')
#   - 조건에 맞는 태그를 "모두" 모아서 돌려줍니다
#   - 결과는 리스트처럼 다룰 수 있습니다 -> len(), for 문, 인덱스[0] 모두 사용 가능
#
# a_tag.get('href')
#   - 태그의 "속성 값"만 꺼냅니다
#   - <a href="/login">Login</a> 에서 .text 는 'Login', .get('href') 는 '/login'
#
# 확인 포인트
#   - find('a') 는 1개, find_all('a') 는 몇 개인가요?
#   - 링크 주소(href)가 https:// 로 시작하지 않고 / 로 시작하는 이유는 무엇일까요?
#     (힌트: 같은 사이트 안에서 이동하는 "상대 주소")

a_tags = soup.find_all('a')
print('a 태그 개수:', len(a_tags))
for a_tag in a_tags[:5]:  # 너무 많으므로 앞의 5개만 확인
    print(a_tag.text, '->', a_tag.get('href'))


# ------------------------------------------------------------
# [STEP 5] select_one() / select() : CSS 선택자로 찾기
# ------------------------------------------------------------
# CSS에서 스타일을 지정할 대상을 고를 때 쓰던 문법(선택자)을 그대로 씁니다
#   'span'    -> 태그 이름이 span 인 요소
#   '.text'   -> class 가 text 인 요소   (앞에 점)
#   '#login'  -> id 가 login 인 요소     (앞에 #)
#
#   | 하나만 찾기      | 전체 찾기       |
#   | find()          | find_all()     |
#   | select_one()    | select()       |
#
# 여러 개 중 특정 순서의 요소는 리스트처럼 인덱스로 고릅니다 (첫 번째 = [0])
#
# 확인 포인트
#   - 이 페이지의 인용문은 모두 몇 개인가요?
#   - texts[1] 은 몇 번째 인용문인가요?

first_text = soup.select_one('.text')
print('첫 번째 인용문:', first_text.text)
texts = soup.select('.text')
print('인용문 개수:', len(texts))
print('두 번째 인용문 (앞 60글자):', texts[1].text[:60])


# ------------------------------------------------------------
# [STEP 6] find vs select : 같은 결과, 다른 표현
# ------------------------------------------------------------
# "div.quote 안에 있는 span.text" 를 찾는 두 가지 방법
#   - find   : 바깥 태그를 찾고 => 그 안에서 다시 find (단계마다 함수 호출)
#   - select : 'div.quote span.text' 처럼 "A 안의 B"를 공백 하나로 표현
#
# 둘 중 정답은 없습니다. 이 수업에서는 이후 실습(Selenium)에서도 같은 문법을 쓰는
# CSS 선택자(select)를 주로 사용합니다
#
# 확인 포인트
#   - 두 방법의 결과가 같은가요?
#   - 태그가 3단계, 4단계로 깊어진다면 어느 쪽이 더 읽기 쉬울까요?

by_find = soup.find('div', class_='quote').find('span', class_='text').text
by_select = soup.select_one('div.quote span.text').text
print('find   :', by_find)
print('select :', by_select)
print('같은 결과인가?', by_find == by_select)


# ------------------------------------------------------------
# [STEP 7] 인용문과 저자를 한 번에 모으기
# ------------------------------------------------------------
# 지금까지는 인용문만, 또는 저자만 따로 찾았습니다
# 실제로 필요한 데이터는 "이 인용문을 누가 말했는가"처럼 짝을 이룬 정보입니다
#
# 방법
#   1. 인용문 하나를 감싸는 상자(div.quote)를 먼저 모두 찾고
#   2. 상자 하나하나 "안에서" 인용문(span.text)과 저자(small.author)를 꺼냅니다
#   3. {'text': ..., 'author': ...} 딕셔너리로 묶어 리스트에 쌓습니다
#   => 상자 단위로 찾기 때문에 인용문과 저자가 서로 어긋나지 않습니다
#
# 확인 포인트
#   - 수집한 인용문 개수를 기억해 두세요. 다음 동적 페이지 실습에서 비교합니다

quotes = []
for quote in soup.select('div.quote'):
    quotes.append(
        {
            'text': quote.select_one('span.text').text,
            'author': quote.select_one('small.author').text,
        }
    )
print(f'수집한 인용문: {len(quotes)}개')
for idx, item in enumerate(quotes, 1):
    print(f'{idx:02d}. {item["author"]} : {item["text"][:40]}')
