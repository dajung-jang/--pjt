"""
댓글 수집 ④ 커뮤니티 페이지로 이동하기

학습 목표
  1. 종목 코드로 주소를 직접 만들어, 클릭 없이 원하는 페이지로 이동한다
  2. 기다리는 요소를 못 찾았을 때 프로그램이 멈추지 않게 처리한다

전체 흐름
  01 메인 접속 => 02 회사명 검색 => 03 종목 코드 추출 => [04 커뮤니티 이동] => 05 댓글 수집·저장

진행 방법
  - "이전 실습에서 만든 함수"는 이미 완성되어 있습니다. 읽어 보기만 하세요
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제합니다
  - 함수 정의 STEP 은 해제해도 출력이 없습니다. 마지막 STEP(실행)까지 해제해야 동작합니다
  - 실행하면 크롬 창이 열립니다. 코드가 끝날 때까지 창을 직접 조작하지 마세요
"""

import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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


def get_stock_code(driver):
    """검색 후 이동한 종목 페이지 주소에서 종목 코드를 꺼낸다"""
    # 검색이 끝나면 .../stocks/종목코드/order 로 이동 -> 주소가 바뀔 때까지 대기
    WebDriverWait(driver, 15).until(EC.url_contains('/order'))

    # 예) https://www.tossinvest.com/stocks/A005930/order
    #     split('/') -> [..., 'stocks', 'A005930', 'order']
    #     'stocks' 바로 다음 칸이 종목 코드
    parts = driver.current_url.split('/')
    stock_code = parts[parts.index('stocks') + 1]
    print(f'[종목 코드] {stock_code} ({driver.current_url})')
    return stock_code


# ------------------------------------------------------------
# [STEP 1] 커뮤니티 페이지 접속하기
# ------------------------------------------------------------
# f-string 으로 주소 만들기
#   stock_code = 'A005930' 이면
#   f'https://www.tossinvest.com/stocks/{stock_code}/community'
#   => 'https://www.tossinvest.com/stocks/A005930/community'
#
# try / except TimeoutException
#   - WebDriverWait 는 시간이 초과하면 TimeoutException 에러를 냅니다
#   - 에러가 나면 프로그램이 멈추므로, except 로 받아서 안내 메시지만 출력합니다
#   - "왜 못 찾았는지"를 화면에서 직접 확인할 수 있게 하기 위해서입니다
#
# #stock-content
#   - 종목 페이지의 본문(댓글 목록이 들어가는 영역)의 id 입니다
#   - 개발자 도구(F12) => Elements 탭에서 직접 찾아 보세요

def open_community(driver, stock_code):
    """종목 코드로 커뮤니티 페이지 주소를 만들어 바로 이동한다"""
    community_url = f'https://www.tossinvest.com/stocks/{stock_code}/community'
    driver.get(community_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#stock-content'))
        )
        print('[커뮤니티] 댓글 영역 로딩 완료')
    except TimeoutException:
        print('[커뮤니티] 10초 안에 댓글 영역을 찾지 못했습니다. 화면을 확인하세요.')


# ------------------------------------------------------------
# [STEP 2] 실행하기
# ------------------------------------------------------------
# 확인 포인트
#   - 크롬 창이 닫히기 전 5초 동안, 개발자 도구(F12)로 댓글 하나를 클릭해 보세요
#     댓글 글자를 감싼 <span> 태그에 어떤 속성들이 있나요? (다음 실습에서 사용)

if __name__ == '__main__':
    driver = get_driver()
    try:
        open_main(driver)
        search_company(driver, COMPANY)
        stock_code = get_stock_code(driver)
        open_community(driver, stock_code)
        time.sleep(5)  # 커뮤니티 화면을 눈으로 확인하기 위한 대기
    finally:
        driver.quit()
