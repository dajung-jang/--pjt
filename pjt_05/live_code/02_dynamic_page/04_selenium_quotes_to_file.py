"""
동적 페이지 크롤링 ④ 함수로 정리하고 파일로 저장하기

학습 목표
  1. 브라우저 실행 / 데이터 추출 / 파일 저장을 각각 함수로 나눈다
  2. 함수로 나누면 페이지가 늘어나도 같은 코드를 반복해서 쓸 수 있음을 확인한다
  3. 수집 결과를 JSON 파일로 저장한다

왜 함수로 나눌까?
  03_selenium_page_source.py 는 위에서 아래로 한 번만 실행되는 코드였습니다
  2페이지도 수집하려면 같은 코드를 복사해야 합니다
  => "한 페이지 수집"을 함수로 만들어 두면 주소만 바꿔 여러 번 호출할 수 있습니다

전체 흐름
  get_driver()  =>  get_quotes(driver, url) x 2페이지  =>  save_json(quotes, 파일 경로)

진행 방법
  - STEP 1~3 은 "함수 정의"라서 해제하고 실행해도 아무것도 출력되지 않습니다 (정상)
  - STEP 4 까지 해제해야 함수가 실제로 호출되어 결과가 나옵니다
  - 실행이 끝나면 data/quotes_js.json 파일을 열어 저장된 내용을 확인합니다
    (data 폴더는 01_static_page, 02_dynamic_page 폴더와 같은 위치에 생깁니다)
"""

import json
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / 'data'

# {} 자리에 페이지 번호를 넣어 주소를 만듭니다
# BASE_URL.format(2) => 'http://quotes.toscrape.com/js/page/2/'
BASE_URL = 'http://quotes.toscrape.com/js/page/{}/'


# ------------------------------------------------------------
# [STEP 1] 브라우저 실행 함수
# ------------------------------------------------------------
# 브라우저 옵션 설정과 실행을 한 함수에 모아 둡니다
# 옵션을 바꾸고 싶을 때 이 함수 하나만 고치면 됩니다
#
# excludeSwitches ['enable-logging']
#   - 크롬이 콘솔(터미널)에 출력하는 내부 로그를 숨깁니다
#   - 우리가 print 한 결과만 보이게 해서 읽기 쉽게 만듭니다
# --headless (참고, 주석 상태)
#   - 창을 띄우지 않고 백그라운드로 실행합니다
#   - 화면 확인이 필요 없는 자동화(예: 웹 서비스 안에서 실행)에서 사용합니다

def get_driver():
    """옵션을 적용한 크롬 브라우저를 실행해 돌려준다"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # chrome_options.add_argument('--headless')
    return webdriver.Chrome(options=chrome_options)


# ------------------------------------------------------------
# [STEP 2] 한 페이지에서 인용문을 모아 돌려주는 함수
# ------------------------------------------------------------
# 입력 : driver (열려 있는 브라우저), url (수집할 페이지 주소)
# 출력 : [{'text': 인용문, 'author': 저자}, ...] 형태의 리스트
#
# 브라우저를 함수 안에서 새로 열지 않고 "매개변수로 받는" 이유
#   - 페이지마다 브라우저를 새로 열고 닫으면 느립니다
#   - 브라우저 하나를 열어 두고 주소만 바꿔 가며 재사용합니다

def get_quotes(driver, url):
    """url 페이지를 열고 인용문·저자를 딕셔너리 리스트로 돌려준다"""
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    quotes = []
    for quote in soup.select('div.quote'):
        quotes.append(
            {
                'text': quote.select_one('span.text').text,
                'author': quote.select_one('small.author').text,
            }
        )
    print(f'[수집] {url} -> {len(quotes)}개')
    return quotes


# ------------------------------------------------------------
# [STEP 3] 리스트를 JSON 파일로 저장하는 함수
# ------------------------------------------------------------
# JSON : 리스트·딕셔너리 구조를 그대로 글자로 저장하는 형식
#   - 나중에 json.load() 로 읽으면 다시 파이썬 리스트로 돌아옵니다
#   - 다음 실습(댓글 수집 => 전처리)에서도 같은 방식으로 단계 사이에 데이터를 넘깁니다
#
# file_path.parent.mkdir(exist_ok=True)
#   - 저장할 폴더(data)가 없으면 만들고, 이미 있으면 그냥 넘어갑니다
# ensure_ascii=False
#   - 한글·특수문자(’ 등)를 \u2019 같은 코드로 바꾸지 않고 글자 그대로 저장합니다
# indent=2
#   - 한 줄로 몰아 쓰지 않고 줄바꿈·들여쓰기를 넣어 사람이 읽기 좋게 저장합니다

def save_json(data, file_path):
    """data(리스트·딕셔너리)를 JSON 파일로 저장한다"""
    file_path.parent.mkdir(exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'[저장] {file_path.name} ({len(data)}개)')


# ------------------------------------------------------------
# [STEP 4] 함수 조립해서 실행하기
# ------------------------------------------------------------
# if __name__ == '__main__':
#   - 이 파일을 "직접 실행"할 때만 아래 코드가 동작합니다
#   - 다른 파일에서 import 하면 함수만 가져가고, 크롤링은 실행되지 않습니다
#   - 관통 프로젝트에서 웹 서비스가 이 함수들을 가져다 쓸 때 필요한 구조입니다
#
# all_quotes.extend(리스트)
#   - append 는 리스트를 "통째로 하나" 넣고, extend 는 리스트의 "항목들을" 이어 붙입니다
#   - 1페이지 10개 + 2페이지 10개 => 20개짜리 리스트 하나
#
# 확인 포인트
#   - 두 페이지에서 각각 몇 개, 모두 몇 개를 저장했나요?
#   - data/quotes_js.json 파일을 열어 한글·따옴표가 글자 그대로 저장되었는지 확인하세요

if __name__ == '__main__':
    driver = get_driver()
    all_quotes = []
    for page in range(1, 3):  # 1, 2 페이지
        all_quotes.extend(get_quotes(driver, BASE_URL.format(page)))
    driver.quit()
    save_json(all_quotes, DATA_DIR / 'quotes_js.json')
    for idx, item in enumerate(all_quotes[:3], 1):  # 앞의 3개만 미리보기
        print(f'{idx:02d}. {item["author"]} : {item["text"][:40]}')
