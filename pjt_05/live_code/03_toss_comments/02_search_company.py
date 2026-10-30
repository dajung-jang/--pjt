"""
댓글 수집 ② 회사명 검색하기

학습 목표
  1. 화면을 가리는 팝업을 먼저 닫는다
  2. 키보드 단축키('/')와 입력창에 글자를 보내 검색한다

전체 흐름
  01 메인 접속 => [02 회사명 검색] => 03 종목 코드 추출 => 04 커뮤니티 이동 => 05 댓글 수집·저장

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


# ------------------------------------------------------------
# [STEP 1] 첫 진입 팝업 닫기
# ------------------------------------------------------------
# 왜 필요할까?
#   - 토스증권에 처음 들어가면 이벤트 안내 팝업이 뜨는 경우가 있습니다
#   - 팝업이 화면의 "포커스(지금 입력을 받는 대상)"를 가져가면,
#     다음 단계의 검색 단축키('/')가 팝업에 입력되어 검색창이 열리지 않습니다
#
# find_element  vs  find_elements
#   - find_element  : 하나만 찾음. 없으면 에러 (BeautifulSoup 의 select_one 과 비슷)
#   - find_elements : 모두 찾아 리스트로. 없으면 빈 리스트 [] (select 와 비슷)
#   - 팝업은 "있을 수도, 없을 수도" 있으므로 에러가 나지 않는 find_elements 를 씁니다
#
# XPath : //button[@aria-label='닫기']
#   - "aria-label 속성이 '닫기'인 모든 button" 이라는 뜻입니다
#   - aria-label : 화면 낭독기(시각 장애인용)가 읽어 주는 버튼 이름
#     => 디자인이 바뀌어도 "닫기"라는 역할은 잘 바뀌지 않아 안정적인 기준입니다
#
# driver.execute_script('arguments[0].click();', close_btn)
#   - 일부 닫기 버튼은 왼쪽 메뉴에 가려져 있어 일반 click() 이 실패합니다
#   - 자바스크립트로 버튼을 "직접" 클릭해서 가려진 문제를 피합니다

def close_popups(driver):
    """첫 진입 시 뜨는 안내 팝업의 닫기 버튼을 모두 누른다"""
    time.sleep(1)

    for close_btn in driver.find_elements(By.XPATH, "//button[@aria-label='닫기']"):
        try:
            if close_btn.is_displayed():
                driver.execute_script('arguments[0].click();', close_btn)
                time.sleep(0.5)
        except Exception:
            pass


# ------------------------------------------------------------
# [STEP 2] '/' 단축키로 검색하기
# ------------------------------------------------------------
# 사람이 하는 순서 그대로 코드로 옮깁니다
#   1. 키보드 '/' 를 누른다 => 검색 모달이 열린다
#   2. 검색 입력창에 회사명을 입력한다
#   3. Enter 를 누른다 => 종목 페이지로 이동한다
#
# document.activeElement.blur(); document.body.focus();
#   - 지금 포커스를 가진 요소에서 포커스를 빼고, 페이지 전체(body)에 포커스를 줍니다
#   - 단축키는 페이지 전체에 포커스가 있을 때만 동작하기 때문입니다
#
# ActionChains(driver).send_keys('/').perform()
#   - 특정 입력창이 아니라 "페이지 전체"에 키보드 입력을 보냅니다
#   - .perform() 을 호출해야 실제로 실행됩니다
#
# search_input.send_keys(...)
#   - 찾은 입력창에 글자를 입력합니다
#   - Keys.ENTER 처럼 특수 키도 보낼 수 있습니다 (Keys.END, Keys.ESCAPE 등)

def search_company(driver, company_name):
    """'/' 단축키로 검색창을 열고 회사명을 검색한다"""
    close_popups(driver)

    driver.execute_script('document.activeElement.blur(); document.body.focus();')
    ActionChains(driver).send_keys('/').perform()

    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@placeholder='검색어를 입력해주세요']")
        )
    )
    search_input.send_keys(company_name)
    search_input.send_keys(Keys.ENTER)
    print(f'[검색] {company_name}')


# ------------------------------------------------------------
# [STEP 3] 실행하기
# ------------------------------------------------------------
# time.sleep(3) 은 "화면을 눈으로 확인하기 위한" 대기입니다 (데이터 수집에는 필요 없음)
#
# 확인 포인트
#   - 검색 후 이동한 주소는 어떤 모양인가요? 다음 실습에서 이 주소를 사용합니다
#   - COMPANY 를 다른 회사명(예: '카카오')으로 바꿔 실행해 보세요

if __name__ == '__main__':
    driver = get_driver()
    try:
        open_main(driver)
        search_company(driver, COMPANY)
        time.sleep(3)  # 검색 결과 화면을 눈으로 확인하기 위한 대기
        print('이동한 주소:', driver.current_url)
    finally:
        driver.quit()
