"""
댓글 수집 ① 토스증권 메인 페이지 접속하기

학습 목표
  1. 실제 서비스(토스증권)에 Selenium으로 접속한다
  2. time.sleep() 대신 WebDriverWait 로 "필요한 만큼만" 기다린다

전체 흐름 (파일마다 한 단계씩 추가)
  [01 메인 접속] => 02 회사명 검색 => 03 종목 코드 추출 => 04 커뮤니티 이동 => 05 댓글 수집·저장

실습 사이트 : https://www.tossinvest.com/
  - robots.txt 확인 : https://www.tossinvest.com/robots.txt

진행 방법
  - "이전 실습에서 만든 함수"는 이미 완성되어 있습니다. 읽어 보기만 하세요
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제합니다
  - 함수 정의 STEP 은 해제해도 출력이 없습니다. 마지막 STEP(실행)까지 해제해야 동작합니다
  - 실행하면 크롬 창이 열립니다. 코드가 끝날 때까지 창을 직접 조작하지 마세요
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
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


# ------------------------------------------------------------
# [STEP 1] 조건을 만족할 때까지 기다리며 접속하기
# ------------------------------------------------------------
# 동적 페이지는 driver.get() 이 끝나도 화면이 "다 그려졌다"는 보장이 없습니다
# 데이터를 찾기 전에 "기다리기"가 필요합니다
#
#   | 방법                 | 동작                              | 문제점                         |
#   | time.sleep(3)        | 무조건 3초 기다림                 | 1초면 될 때도 3초, 5초 걸리면 실패 |
#   | WebDriverWait(...)   | 조건이 맞는 "순간"까지 기다림 (최대 N초) | -                              |
#
# WebDriverWait(driver, 10).until(조건)
#   - 최대 10초 동안 0.5초마다 "조건"을 다시 확인합니다
#   - 조건이 맞는 순간 바로 다음 줄로 넘어갑니다
#   - 10초가 지나도 조건이 맞지 않으면 TimeoutException 에러가 납니다
#
# EC.presence_of_element_located((By.CSS_SELECTOR, '#ts-lnb'))
#   - "id 가 ts-lnb 인 요소가 HTML 안에 존재하는가" 라는 조건입니다
#   - #ts-lnb 는 화면 왼쪽 메뉴 영역입니다. 자바스크립트가 화면을 그려야 나타납니다
#   - By.CSS_SELECTOR 자리에 By.ID, By.XPATH, By.TAG_NAME 등도 쓸 수 있습니다

def open_main(driver):
    """토스증권 메인 페이지에 접속하고, 화면이 그려질 때까지 기다린다"""
    driver.get(MAIN_URL)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#ts-lnb'))
    )
    print('[접속] 토스증권 메인 페이지 로딩 완료')


# ------------------------------------------------------------
# [STEP 2] 실행하기
# ------------------------------------------------------------
# try / finally
#   - try 안에서 에러가 나도, finally 는 "반드시" 실행됩니다
#   - driver.quit() 을 finally 에 두면 중간에 실패해도 크롬 창이 남지 않습니다
#     (실패할 때마다 크롬 창과 드라이버가 쌓여 컴퓨터가 느려지는 것을 막음)
#
# 확인 포인트
#   - "[접속] ... 로딩 완료" 가 바로 출력되나요, 몇 초 뒤에 출력되나요?
#   - '#ts-lnb' 를 '#no-such-id' 로 바꿔 실행해 보세요. 10초 뒤 어떤 에러가 나나요?

if __name__ == '__main__':
    driver = get_driver()
    try:
        open_main(driver)
        print('페이지 제목:', driver.title)
    finally:
        driver.quit()
