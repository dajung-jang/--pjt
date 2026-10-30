"""
동적 페이지 크롤링 ② Selenium으로 브라우저 띄우기

학습 목표
  1. 코드로 크롬 브라우저를 실행하고 원하는 주소로 이동한다
  2. 코드가 끝나면 브라우저가 닫히는 이유와, 창을 유지하는 옵션(detach)을 이해한다

Selenium 이란?
  - 코드로 "실제 브라우저"를 조작하는 도구입니다 (클릭, 입력, 스크롤까지 가능)
  - 원래는 웹 서비스를 자동으로 테스트하려고 만들어졌고, 크롤링에도 널리 쓰입니다
  - 브라우저가 자바스크립트를 실행해 주므로, 동적 페이지의 데이터도 가져올 수 있습니다
  - 대신 브라우저를 실제로 띄우기 때문에 requests 보다 느리고 무겁습니다

동작 원리
  파이썬 코드 --(명령)--> ChromeDriver --(조작)--> 크롬 브라우저
  - ChromeDriver : 크롬을 코드로 조작할 수 있게 해 주는 중간 프로그램
  - Selenium 4.6 이상은 설치된 크롬 버전에 맞는 드라이버를 자동으로 준비해 줍니다
    (예전처럼 드라이버를 직접 내려받고 경로를 적을 필요가 없습니다)

진행 방법
  - [STEP 1]을 해제하고 실행 => 창이 열렸다가 닫히는 것을 확인
  - [STEP 2]까지 해제하고 실행 => 창 2개 중 어느 창이 남는지 확인
"""

from selenium import webdriver

URL = 'http://quotes.toscrape.com/js/'


# ------------------------------------------------------------
# [STEP 1] 브라우저 실행 후 이동하기
# ------------------------------------------------------------
# webdriver.Chrome()
#   - 새 크롬 창을 실행합니다
#   - 평소 쓰던 크롬과는 별개의 "깨끗한" 창입니다 (로그인, 방문 기록 없음)
# driver.get(URL)
#   - 주소창에 URL을 입력하고 Enter를 누르는 것과 같습니다
#   - 페이지 로딩이 끝날 때까지 기다린 뒤 다음 줄로 넘어갑니다
# driver.title / driver.current_url
#   - 현재 열려 있는 페이지의 제목과 주소
#
# 확인 포인트
#   - 크롬 창이 열리고 인용문 페이지로 이동하나요?
#   - 코드가 끝나자마자 창이 닫히나요? 파이썬 프로그램이 끝나면서 driver 도 함께 정리되기 때문입니다

driver = webdriver.Chrome()
driver.get(URL)
print('페이지 제목:', driver.title)
print('현재 주소:', driver.current_url)


# ------------------------------------------------------------
# [STEP 2] 옵션으로 창 유지하기 (detach)
# ------------------------------------------------------------
# ChromeOptions
#   - 크롬을 "어떤 상태로" 실행할지 미리 정해 두는 설정 묶음입니다
#   - 옵션을 다 담은 뒤 webdriver.Chrome(options=...) 으로 전달합니다
#
# add_experimental_option('detach', True)
#   - 파이썬 코드가 끝나도 브라우저 창을 닫지 않습니다
#   - 실습 중에 결과 화면을 눈으로 확인하기 위한 설정입니다
#   - 실제 자동화 코드에서는 사용하지 않고, 작업이 끝나면 driver.quit() 으로 닫습니다
#
# 확인 포인트
#   - 창 2개가 열린 뒤, 어느 창이 남아 있나요?
#   - 남은 창 상단의 "Chrome이 자동화된 테스트 소프트웨어에 의해 제어되고 있습니다" 안내를 확인하세요
#     사이트 입장에서도 "사람이 아닌 프로그램"이 접속했다는 것을 알 수 있다는 뜻입니다

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('detach', True)
kept_driver = webdriver.Chrome(options=chrome_options)
kept_driver.get(URL)
print('detach 창 제목:', kept_driver.title)
