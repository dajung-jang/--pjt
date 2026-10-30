"""
댓글 수집 ③ 주소에서 종목 코드 꺼내기

학습 목표
  1. 페이지 이동을 "주소 변화"로 기다린다
  2. 주소 문자열을 나눠 필요한 값(종목 코드)만 꺼낸다

전체 흐름
  01 메인 접속 => 02 회사명 검색 => [03 종목 코드 추출] => 04 커뮤니티 이동 => 05 댓글 수집·저장

진행 방법
  - "이전 실습에서 만든 함수"는 이미 완성되어 있습니다. 읽어 보기만 하세요
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제합니다
  - 함수 정의 STEP 은 해제해도 출력이 없습니다. 마지막 STEP(실행)까지 해제해야 동작합니다
  - 실행하면 크롬 창이 열립니다. 코드가 끝날 때까지 창을 직접 조작하지 마세요
"""

import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

MAIN_URL = 'https://www.tossinvest.com/'
COMPANY = '삼성전자'


# ------------------------------------------------------------
# 이전 실습에서 만든 함수 (수정 없이 그대로 사용)
# ------------------------------------------------------------


def get_driver():
    """옵션을 적용한 크롬 브라우저를 실행해 돌려준다 (02_dynamic_page 와 같은 함수)"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=chrome_options)


def open_main(driver):
    """토스증권 메인 페이지에 접속하고, 화면이 그려질 때까지 기다린다"""
    driver.get(MAIN_URL)

    # 왼쪽 메뉴(#ts-lnb)는 자바스크립트가 화면을 그린 뒤에 나타나는 요소
    # 최대 10초 동안 반복 확인 -> 나타나는 순간 바로 다음 줄로 진행
    # 10초가 지나도 없으면 TimeoutException 발생
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#ts-lnb'))
    )
    print('[접속] 토스증권 메인 페이지 로딩 완료')


def close_popups(driver):
    """첫 진입 시 뜨는 안내 팝업의 닫기 버튼을 모두 누른다"""
    # 팝업은 페이지가 그려진 뒤 조금 늦게 뜨는 경우가 있어 잠깐 대기
    time.sleep(1)

    # XPath: //태그[@속성='값'] -> aria-label 이 '닫기'인 모든 button
    for close_btn in driver.find_elements(By.XPATH, "//button[@aria-label='닫기']"):
        try:
            if close_btn.is_displayed():
                # 일부 닫기 버튼은 다른 요소(왼쪽 메뉴)에 가려져 일반 click() 이 실패함
                # -> 자바스크립트로 버튼을 직접 클릭
                driver.execute_script('arguments[0].click();', close_btn)
                time.sleep(0.5)
        except Exception:
            # 닫기에 실패해도 진행에는 큰 문제가 없으므로 넘어감
            pass


def search_company(driver, company_name):
    """'/' 단축키로 검색창을 열고 회사명을 검색한다"""
    close_popups(driver)

    # 단축키는 페이지 전체(body)에 포커스가 있어야 동작
    driver.execute_script('document.activeElement.blur(); document.body.focus();')
    ActionChains(driver).send_keys('/').perform()

    # 검색 모달 안의 입력창이 나타날 때까지 대기
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@placeholder='검색어를 입력해주세요']")
        )
    )
    search_input.send_keys(company_name)
    search_input.send_keys(Keys.ENTER)
    print(f'[검색] {company_name}')


# ------------------------------------------------------------
# [STEP 1] 주소에서 종목 코드 추출하기
# ------------------------------------------------------------
# 왜 종목 코드가 필요할까?
#   - 커뮤니티 페이지 주소는 https://www.tossinvest.com/stocks/종목코드/community 입니다
#   - 종목 코드만 알면 메뉴를 클릭하지 않고 주소를 "직접 만들어" 이동할 수 있습니다
#   - 클릭은 버튼 위치·모양이 바뀌면 깨지지만, 주소 규칙은 훨씬 잘 바뀌지 않습니다
#
# EC.url_contains('/order')
#   - "현재 주소에 '/order' 가 들어 있는가" 라는 조건입니다
#   - 요소가 아니라 "주소 변화"를 기다리는 것도 가능합니다
#
# 주소에서 종목 코드 꺼내기
#   'https://www.tossinvest.com/stocks/A005930/order'.split('/')
#   => ['https:', '', 'www.tossinvest.com', 'stocks', 'A005930', 'order']
#   parts.index('stocks')     => 3       ('stocks' 가 몇 번째 칸인지)
#   parts[3 + 1]              => 'A005930'

def get_stock_code(driver):
    """검색 후 이동한 종목 페이지 주소에서 종목 코드를 꺼낸다"""
    WebDriverWait(driver, 15).until(EC.url_contains('/order'))

    parts = driver.current_url.split('/')
    stock_code = parts[parts.index('stocks') + 1]
    print(f'[종목 코드] {stock_code} ({driver.current_url})')
    return stock_code


# ------------------------------------------------------------
# [STEP 2] 실행하기
# ------------------------------------------------------------
# 확인 포인트
#   - 삼성전자의 종목 코드는 무엇인가요?
#   - COMPANY 를 바꾸면 종목 코드도 바뀌나요?

if __name__ == '__main__':
    driver = get_driver()
    try:
        open_main(driver)
        search_company(driver, COMPANY)
        stock_code = get_stock_code(driver)
    finally:
        driver.quit()
