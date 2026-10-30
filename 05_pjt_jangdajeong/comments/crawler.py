"""
crawler.py : 토스증권 커뮤니티 댓글 수집 모듈
views.py 에서는 crawl_comments() 하나만 사용한다.
"""

import re
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

MAIN_URL = 'https://www.tossinvest.com/'
LIMIT = 20

# 클래스 이름은 배포 때마다 바뀌므로 "역할"을 나타내는 속성을 기준으로 선택
COMMENT_SELECTOR = "span[style*='--fold-after-lines']"


class CompanyNotFound(Exception):
    pass


class NoComments(Exception):
    pass


def get_driver(headless=False):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)


def open_main(driver):
    driver.get(MAIN_URL)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#ts-lnb'))
    )
    print('[접속] 토스증권 메인 페이지 로딩 완료')


def close_popups(driver):
    time.sleep(1)
    for close_btn in driver.find_elements(By.XPATH, "//button[@aria-label='닫기']"):
        try:
            if close_btn.is_displayed():
                driver.execute_script('arguments[0].click();', close_btn)
                time.sleep(0.5)
        except Exception:
            pass


def search_company(driver, company_name):
    """'/' 단축키로 검색창을 열고 회사명을 검색한다 (F603)"""
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


def get_stock_code(driver):
    """검색 후 이동한 종목 페이지 주소에서 종목 코드를 꺼낸다"""
    WebDriverWait(driver, 15).until(EC.url_matches(r'/stocks/[A-Za-z0-9]+'))
    stock_code = re.search(r'/stocks/([A-Za-z0-9]+)', driver.current_url).group(1)
    print(f'[종목 코드] {stock_code} ({driver.current_url})')
    return stock_code


def get_stock_name(driver, stock_code, fallback):
    """종목 페이지에서 실제 종목명을 읽는다 (실패하면 입력값 사용)"""
    code6 = stock_code.lstrip('A')  # A005930 -> 005930
    xpath = f"//*[not(*)][contains(normalize-space(text()), '{code6}')]"

    # 종목번호 요소가 그려질 때까지 대기
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except TimeoutException:
        pass

    try:
        for leaf in driver.find_elements(By.XPATH, xpath):
            parent_text = leaf.find_element(By.XPATH, '..').text
            for line in parent_text.replace(code6, '').split('\n'):
                line = line.strip()
                if not line:
                    continue
                # 가격(217,750원), 등락률(-6.14%), 숫자만 있는 줄은 제외
                if re.search(r'[\d,]+\s*원|%', line) or re.fullmatch(r'[\d,.\s+\-]+', line):
                    continue
                return line
    except Exception:
        pass

    title = driver.title.strip()
    for sep in (' · ', ' - ', ' | ', ' – '):
        if sep in title:
            return title.split(sep)[0].strip()
    return fallback


def open_community(driver, stock_code):
    driver.get(f'https://www.tossinvest.com/stocks/{stock_code}/community')
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#stock-content'))
        )
        print('[커뮤니티] 댓글 영역 로딩 완료')
    except TimeoutException:
        print('[커뮤니티] 10초 안에 댓글 영역을 찾지 못했습니다.')


def read_visible_comments(driver, comments):
    for span in driver.find_elements(By.CSS_SELECTOR, COMMENT_SELECTOR):
        try:
            text = span.text.strip()
        except StaleElementReferenceException:
            continue  # 그 사이 사라진 요소는 건너뜀
        if text and text not in comments:
            comments.append(text)


def find_scroll_container(driver):
    try:
        return driver.find_element(
            By.CSS_SELECTOR, "div[data-id^='base-ui-'][data-id$='-viewport']"
        )
    except Exception:
        return None


def collect_comments(driver, limit=LIMIT, max_scroll=30):
    """스크롤을 반복하며 댓글을 최대 limit 개까지 모은다 (F604)"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, COMMENT_SELECTOR))
        )
    except TimeoutException:
        print('[수집] 댓글을 찾지 못했습니다.')
        return []

    comments = []
    prev_count = -1
    stagnant_rounds = 0

    for scroll in range(max_scroll):
        read_visible_comments(driver, comments)
        print(f'[수집] 스크롤 {scroll + 1}회 -> 누적 {len(comments)}개')

        # 스크롤 상자는 매 회차마다 새로 찾는다 (다시 그려지면 이전 참조가 무효가 됨)
        scroll_container = find_scroll_container(driver)
        if len(comments) >= limit or scroll_container is None:
            break

        if len(comments) == prev_count:
            stagnant_rounds += 1
            if stagnant_rounds >= 5:
                break
        else:
            stagnant_rounds = 0
        prev_count = len(comments)

        # 1) JS로 스크롤 상자를 맨 아래로 (클릭이 가로막혀도 동작)
        try:
            driver.execute_script(
                'arguments[0].scrollTop = arguments[0].scrollHeight;', scroll_container
            )
        except Exception as e:
            print(f'[수집] JS 스크롤 실패 ({type(e).__name__})')

        # 2) 보조: 클릭 후 End 키 (실패해도 무시)
        try:
            scroll_container.click()
            scroll_container.send_keys(Keys.END)
        except Exception as e:
            print(f'[수집] 키 스크롤 실패 ({type(e).__name__})')

        time.sleep(1.5)

    return comments[:limit]


def crawl_comments(company_name, headless=False):
    """(실제종목명, 댓글 리스트) 반환.
    회사를 못 찾으면 CompanyNotFound, 댓글이 없으면 NoComments 발생"""
    driver = get_driver(headless)
    try:
        try:
            open_main(driver)
            search_company(driver, company_name)
            stock_code = get_stock_code(driver)
        except Exception as e:
            print(f'[수집 실패] {company_name} : {type(e).__name__} {e}')
            raise CompanyNotFound(company_name)

        stock_name = get_stock_name(driver, stock_code, fallback=company_name)
        print(f'[종목명] {stock_name}')

        open_community(driver, stock_code)
        comments = collect_comments(driver)
        if not comments:
            raise NoComments()
        return stock_name, comments
    finally:
        driver.quit()