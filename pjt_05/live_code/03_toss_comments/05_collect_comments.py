"""
댓글 수집 ⑤ 스크롤하며 댓글 모으고 파일로 저장하기

학습 목표
  1. 클래스 이름이 아닌 "역할" 기준으로 안 깨지는 선택자를 고른다
  2. 내부 스크롤 영역을 스크롤하며 댓글을 원하는 개수만큼 모은다
  3. 수집 결과를 JSON 파일로 저장해 다음 단계(전처리)에 넘긴다

전체 흐름
  01 메인 접속 => 02 회사명 검색 => 03 종목 코드 추출 => 04 커뮤니티 이동 => [05 댓글 수집·저장]

결과 파일 : data/comments_raw.json
  - 작성자 닉네임 등 개인을 알아볼 수 있는 정보는 수집하지 않고, 댓글 본문만 저장

진행 방법
  - "이전 실습에서 만든 함수"는 이미 완성되어 있습니다. 읽어 보기만 하세요
  - [STEP 1]부터 순서대로 코드 블록을 선택하고 Ctrl + / 로 주석을 해제합니다
  - 함수 정의 STEP 은 해제해도 출력이 없습니다. 마지막 STEP(실행)까지 해제해야 동작합니다
  - 실행하면 크롬 창이 열립니다. 코드가 끝날 때까지 창을 직접 조작하지 마세요
"""

import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / 'data'

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


def open_community(driver, stock_code):
    """종목 코드로 커뮤니티 페이지 주소를 만들어 바로 이동한다"""
    community_url = f'https://www.tossinvest.com/stocks/{stock_code}/community'
    driver.get(community_url)

    # 댓글 영역(#stock-content)이 나타날 때까지 대기
    # 시간이 초과해도 프로그램을 멈추지 않고 안내만 출력
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#stock-content'))
        )
        print('[커뮤니티] 댓글 영역 로딩 완료')
    except TimeoutException:
        print('[커뮤니티] 10초 안에 댓글 영역을 찾지 못했습니다. 화면을 확인하세요.')


def save_json(data, file_path):
    """data 를 JSON 파일로 저장한다 (02_dynamic_page 와 같은 함수)"""
    file_path.parent.mkdir(exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'[저장] {file_path.name}')


# ------------------------------------------------------------
# [STEP 1] 안 깨지는 선택자로 보이는 댓글 읽기
# ------------------------------------------------------------
# 안 깨지는 선택자 고르기
#   개발자 도구에서 댓글을 클릭하면 이런 모양이 보입니다
#     <span class="tc3tm85" style="--fold-after-lines: 3">삼전 가즈아</span>
#
#   | 선택자 후보                          | 문제                                          |
#   | span.tc3tm85                         | 클래스 이름은 사이트를 새로 배포할 때마다 자동으로 바뀜 |
#   | span[style*='--fold-after-lines']    | "본문을 N줄까지만 보여주고 접기"라는 역할 => 본문에만 있음 |
#
#   => 화면에 보이는 "모양(클래스)"이 아니라 요소의 "역할(속성)"을 기준으로 골라야
#      디자인이 바뀌어도 코드가 잘 깨지지 않습니다
#
# [속성*='값'] : 속성 값에 '값'이 "포함"된 요소 (CSS 속성 선택자, 부록 참고)
#
# read_visible_comments(driver, comments)
#   - 화면에 보이는 댓글을 읽어 comments 리스트에 "추가"합니다
#   - 스크롤하면 이미 읽은 댓글도 다시 보이므로, 이미 있는 댓글은 건너뜁니다 (not in)
#   - 리스트는 함수 안에서 append 하면 바깥의 리스트도 함께 바뀝니다 (return 불필요)

COMMENT_SELECTOR = "span[style*='--fold-after-lines']"

def read_visible_comments(driver, comments):
    """지금 화면에 보이는 댓글을 comments 리스트에 추가한다 (중복 제외)"""
    for span in driver.find_elements(By.CSS_SELECTOR, COMMENT_SELECTOR):
        text = span.text.strip()
        if text and text not in comments:
            comments.append(text)


# ------------------------------------------------------------
# [STEP 2] 내부 스크롤 영역 찾기
# ------------------------------------------------------------
# 왜 필요할까?
#   - 댓글은 처음에 일부만 보이고, 아래로 스크롤해야 다음 댓글이 불러와집니다
#   - 그런데 이 페이지의 댓글 목록은 "페이지 전체"가 아니라,
#     화면 안의 "작은 스크롤 상자" 안에서 스크롤됩니다
#   - 그래서 페이지 전체를 스크롤하는 방법(window.scrollTo)으로는 새 댓글이 나오지 않습니다
#   => 이 스크롤 상자를 직접 찾아서 스크롤해야 합니다
#
# div[data-id^='base-ui-'][data-id$='-viewport']
#   - [속성^='값'] : 값으로 "시작"      => data-id 가 'base-ui-' 로 시작
#   - [속성$='값'] : 값으로 "끝남"      => data-id 가 '-viewport' 로 끝남
#   - 두 조건을 붙여 쓰면 AND           => 둘 다 만족하는 div
#   - 가운데 숫자(base-ui-r1-viewport 의 r1)는 바뀔 수 있어서 앞뒤만 고정했습니다
#
# 못 찾으면 None 을 돌려줍니다 => 스크롤 없이 화면에 보이는 댓글만 수집합니다

def find_scroll_container(driver):
    """댓글 목록을 감싼 내부 스크롤 영역을 찾는다 (없으면 None)"""
    try:
        return driver.find_element(
            By.CSS_SELECTOR, "div[data-id^='base-ui-'][data-id$='-viewport']"
        )
    except Exception:
        return None


# ------------------------------------------------------------
# [STEP 3] 스크롤하며 댓글 모으기
# ------------------------------------------------------------
# 동작 순서
#   ① 첫 댓글이 나타날 때까지 기다린다 (못 찾으면 빈 리스트 반환)
#   ② 스크롤 상자를 찾는다
#   ③ 반복: 보이는 댓글 읽기 => 그만둘지 확인 => 스크롤 => 1.5초 대기
#
# 반복을 멈추는 조건 3가지 (무한 반복 방지)
#   - 목표 개수(limit) 만큼 모았을 때
#   - 스크롤 상자를 못 찾았을 때 (스크롤 불가)
#   - 스크롤했는데 댓글 개수가 5번 연속 그대로일 때 (더 불러올 댓글이 없음)
#   - 그리고 for 문 자체가 최대 max_scroll 번까지만 돕니다
#
# prev_count / stagnant_rounds
#   - prev_count      : 직전 반복에서의 댓글 개수 (처음에는 비교 대상이 없어 -1)
#   - stagnant_rounds : "개수가 그대로"였던 횟수. 늘어나면 0으로 초기화
#
# scroll_container.click() => send_keys(Keys.END)
#   - 스크롤 상자를 클릭해 포커스를 준 뒤, 키보드 End 키로 상자의 맨 아래로 이동합니다
#   - 맨 아래에 닿으면 사이트가 다음 댓글을 불러옵니다
#   - time.sleep(1.5) : 새 댓글을 불러오는 데 걸리는 시간 (여기서는 기다릴 "요소"가 없어 sleep 사용)
#
# comments[:limit] : 마지막 스크롤에서 limit 보다 많이 모일 수 있어 정확히 잘라서 돌려줍니다

def collect_comments(driver, limit=20, max_scroll=30):
    """스크롤을 반복하며 댓글을 최대 limit 개까지 모아 돌려준다"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, COMMENT_SELECTOR))
        )
    except TimeoutException:
        print('[수집] 댓글을 찾지 못했습니다. 선택자가 바뀌었는지 확인하세요.')
        return []

    scroll_container = find_scroll_container(driver)
    comments = []
    prev_count = -1  # 직전 반복의 댓글 개수
    stagnant_rounds = 0  # 댓글 개수가 그대로인 횟수

    for scroll in range(max_scroll):
        read_visible_comments(driver, comments)
        print(f'[수집] 스크롤 {scroll + 1}회 -> 누적 {len(comments)}개')

        if len(comments) >= limit or scroll_container is None:
            break

        if len(comments) == prev_count:
            stagnant_rounds += 1
            if stagnant_rounds >= 5:
                break
        else:
            stagnant_rounds = 0
        prev_count = len(comments)

        scroll_container.click()
        scroll_container.send_keys(Keys.END)
        time.sleep(1.5)  # 새 댓글을 불러올 시간

    return comments[:limit]


# ------------------------------------------------------------
# [STEP 4] 실행하고 파일로 저장하기
# ------------------------------------------------------------
# 수집이 끝나면 브라우저는 필요 없으므로 finally 에서 바로 종료하고,
# 그다음 파일 저장과 출력을 합니다
#
# 저장 형식 : 댓글만이 아니라 "언제, 어느 회사"의 댓글인지 함께 저장합니다
#   - 커뮤니티 댓글은 실시간으로 바뀝니다. 지금 수집한 20개는 1시간 뒤와 다릅니다
#   - collected_at 이 있으면 나중에 "이 결과가 언제 데이터였는지" 알 수 있습니다
#   - datetime.now().isoformat(timespec='seconds') => '2026-10-22T10:30:00' 형태
#
# 확인 포인트
#   - 스크롤 몇 회 만에 20개가 모였나요?
#   - data/comments_raw.json 을 열어 보세요. 수집한 댓글에 어떤 "정리가 필요한" 부분이 보이나요?
#     (특수문자, 이모티콘, 너무 짧은 글, 부적절한 표현 등 => 다음 전처리 단계의 대상)

if __name__ == '__main__':
    driver = get_driver()
    try:
        open_main(driver)
        search_company(driver, COMPANY)
        stock_code = get_stock_code(driver)
        open_community(driver, stock_code)
        comments = collect_comments(driver, limit=20)
    finally:
        driver.quit()

    result = {
        'company': COMPANY,
        'collected_at': datetime.now().isoformat(timespec='seconds'),
        'count': len(comments),
        'comments': comments,
    }
    save_json(result, DATA_DIR / 'comments_raw.json')

    print(f'\n=== {COMPANY} 커뮤니티 댓글 ({len(comments)}개) ===')
    for idx, comment in enumerate(comments, 1):
        print(f'{idx:02d}. {comment}')
