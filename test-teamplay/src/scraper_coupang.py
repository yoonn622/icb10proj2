"""
쿠팡에서 상품 카테고리 정보와 전체 리뷰 데이터를 실시간 크롬 브라우저 제어(CDP)를 통해 
수집하고 SQLite 데이터베이스에 저장하는 최종 스크립트입니다.
"""

import os
import sys
import time
import re
import sqlite3
import subprocess
import json
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 윈도우 한글 인코딩 에러 방지
if sys.platform == "win32":
    reconfig = getattr(sys.stdout, 'reconfigure', None)
    if reconfig is not None:
        try:
            reconfig(encoding='utf-8')
        except:
            pass

def clean_broken_korean(text):
    """
    latin-1 혹은 오인코딩된 한글 문자열(예: 'í—¬ìŠ¤/ê±´ê°•ì‹ í’ˆ')을 
    정상적인 UTF-8 한글로 디코딩하여 반환합니다.
    """
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

def setup_sqlite_db(db_path):
    """
    SQLite 데이터베이스 테이블 구조를 초기화합니다.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 상품 테이블 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        price INTEGER,
        rating REAL,
        rating_count INTEGER,
        product_url TEXT
    )
    """)
    
    # 2. 리뷰 테이블 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        review_id TEXT PRIMARY KEY,
        product_id TEXT,
        user_name TEXT,
        rating INTEGER,
        review_date TEXT,
        product_name TEXT,
        headline TEXT,
        comment TEXT,
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)
    
    conn.commit()
    return conn

def parse_product_list_from_ldjson(html_content):
    """
    쿠팡 HTML 소스코드에 포함된 application/ld+json 스크립트 태그 내의 
    실제 상품 데이터를 파싱합니다. (안정성 극대화)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products_data = []
    
    # application/ld+json 타입의 script 검색
    script_tags = soup.find_all('script', type='application/ld+json')
    print(f"발견된 ld+json 스크립트 태그 개수: {len(script_tags)}개")
    
    for tag in script_tags:
        try:
            # 주석 기호나 공백 제거 후 json 로드
            json_text = tag.string.strip() if tag.string else ""
            if not json_text:
                continue
                
            data = json.loads(json_text)
            
            # ItemList 구조인지 확인
            if data.get("@type") == "ItemList":
                items = data.get("itemListElement", [])
                print(f"ld+json ItemList 상품 개수: {len(items)}개")
                
                for item in items:
                    prod_info = item.get("item", {})
                    if prod_info.get("@type") == "Product":
                        # 상세 정보 획득
                        product_name = prod_info.get("name", "")
                        # 오인코딩 복원
                        product_name = clean_broken_korean(product_name)
                        
                        offers = prod_info.get("offers", {})
                        price = int(offers.get("price", 0)) if offers else 0
                        
                        agg_rating = prod_info.get("aggregateRating", {})
                        rating = float(agg_rating.get("ratingValue", 0.0)) if agg_rating else 0.0
                        rating_count = int(agg_rating.get("reviewCount", 0)) if agg_rating else 0
                        
                        product_url = prod_info.get("url", "")
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www.coupang.com" + product_url
                            
                        # 상품 ID 추출
                        product_id = ""
                        product_id_match = re.search(r'/products/(\d+)', product_url)
                        if product_id_match:
                            product_id = product_id_match.group(1)
                        else:
                            # URL에 없으면 name 해시나 타 식별자로
                            continue
                            
                        products_data.append({
                            "product_id": product_id,
                            "product_name": product_name,
                            "price": price,
                            "rating": rating,
                            "rating_count": rating_count,
                            "product_url": product_url
                        })
        except Exception as e:
            print(f"ld+json 파싱 오류: {e}")
            
    return products_data

def scrape_coupang():
    """
    CDP 크롬 제어를 사용하여 쿠팡 카테고리 상품 정보를 1~5페이지까지 수집한 뒤, 
    정제 후 DB 및 CSV 파일로 저장합니다. 
    1페이지 수집이 정상적으로 성공하면, 해당 페이지의 모든 상품에 대한 전체 리뷰를 API 호출로 수집해 SQLite DB에 누적 저장합니다.
    """
    db_path = os.path.join("test-teamplay", "data", "coupang.db")
    csv_path = os.path.join("test-teamplay", "data", "coupang_products.csv")
    
    # 1. SQLite DB 연동 및 테이블 설정
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db_conn = setup_sqlite_db(db_path)
    db_cursor = db_conn.cursor()
    
    # 2. 원격 디버깅 모드로 크롬 실행
    port = 9222
    user_data_dir = os.path.abspath(".chrome_coupang_profile")
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
            
    if not chrome_path:
        print("에러: 시스템에 설치된 구글 크롬 브라우저를 찾을 수 없습니다.")
        return
        
    print(f"크롬 브라우저 경로 확인: {chrome_path}")
    print("원격 디버깅용 크롬 프로세스를 기동합니다...")
    chrome_cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    proc = subprocess.Popen(chrome_cmd, startupinfo=startupinfo)
    time.sleep(4)
    
    all_products = []
    first_page_success = False
    first_page_products = []
    
    # 제외 대상 카테고리 필터 키워드
    exclude_categories = ['홈트레이닝', '헬스/요가용품', '건강가전', '건강도서', '건강/의료용품']
    
    print("\n==================================================")
    print("쿠팡 영양제/건강식품 카테고리 상품 수집 시작 (목표: 1~5페이지)")
    print("==================================================")
    
    with sync_playwright() as p:
        try:
            # CDP를 통해 크롬 연결
            browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            # webdriver 감지 비활성화 우회 스크립트 주입
            page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")
            
            # 1페이지부터 5페이지까지 루프 수집
            for current_page in range(1, 6):
                url = f"https://www.coupang.com/np/categories/305798?traceId=mqp7vpnb&page={current_page}"
                print(f"\n[{current_page}/5] 페이지 데이터 수집 중... URL: {url}")
                
                try:
                    response = page.goto(url, wait_until="load", timeout=30000)
                    # Akamai 봇 검증 및 CSR 돔 렌더링을 위해 명시적 대기 및 추가 지연 적용
                    try:
                        page.wait_for_selector(".baby-product", timeout=10000)
                    except Exception as wait_err:
                        print(f" -> [{current_page}페이지] 상품 목록 셀렉터 대기 중 타임아웃/지연 발생: {wait_err}")
                    
                    page.wait_for_timeout(3000)
                    content = page.content()
                    
                    if "Access Denied" in content:
                        print(f" -> [{current_page}페이지] 차단 에러 (Access Denied) 감지됨. 수집을 일시 중단합니다.")
                        break
                        
                    # ld+json 데이터에서 완벽하게 파싱
                    products = parse_product_list_from_ldjson(content)
                    
                    if not products:
                        print(f" -> [{current_page}페이지] ld+json 파싱 결과가 없습니다. 백업 HTML 구조 파싱을 시도합니다.")
                        # 백업 수단
                        soup = BeautifulSoup(content, 'html.parser')
                        items = soup.select('.baby-product-list, .baby-product')
                        print(f"  -> 백업 파싱 대상 <li> 아이템 개수: {len(items)}개")
                        for item in items:
                            try:
                                a_tag = item.select_one('a')
                                if not a_tag:
                                    continue
                                href = a_tag.get('href', '')
                                product_id_match = re.search(r'/products/(\d+)', href)
                                if not product_id_match:
                                    continue
                                product_id = product_id_match.group(1)
                                name_tag = item.select_one('.name')
                                product_name = clean_broken_korean(name_tag.text.strip()) if name_tag else ""
                                price_tag = item.select_one('.price-value')
                                price_str = price_tag.text.strip() if price_tag else "0"
                                price = int(re.sub(r'[^\d]', '', price_str)) if price_str else 0
                                rating_tag = item.select_one('.rating')
                                rating = float(rating_tag.text.strip()) if rating_tag else 0.0
                                rating_count_tag = item.select_one('.rating-total-count')
                                rating_count_str = rating_count_tag.text.strip() if rating_count_tag else "0"
                                rating_count = int(re.sub(r'[^\d]', '', rating_count_str)) if rating_count_str else 0
                                product_url = "https://www.coupang.com" + href.split('?')[0]
                                products.append({
                                    "product_id": product_id,
                                    "product_name": product_name,
                                    "price": price,
                                    "rating": rating,
                                    "rating_count": rating_count,
                                    "product_url": product_url
                                })
                            except:
                                pass
                                
                    if not products:
                        print(f" -> [{current_page}페이지] 파싱된 상품 데이터가 없습니다.")
                        continue
                        
                    print(f" -> 파싱 완료: {len(products)}개 상품 획득.")
                    
                    # 필터링 적용 및 수집 목록 추가
                    filtered_count = 0
                    for prod in products:
                        name = prod["product_name"]
                        
                        is_excluded = False
                        for exc in exclude_categories:
                            if exc in name:
                                is_excluded = True
                                break
                                
                        if is_excluded:
                            filtered_count += 1
                            continue
                            
                        # 중복 수집 배제
                        if prod["product_id"] not in [p["product_id"] for p in all_products]:
                            all_products.append(prod)
                        
                        if current_page == 1:
                            if prod["product_id"] not in [p["product_id"] for p in first_page_products]:
                                first_page_products.append(prod)
                            
                    print(f" -> 필터링 제외: {filtered_count}개 상품 제외됨 (제외 대상 카테고리 매칭).")
                    
                    # 1페이지 성공 여부 마킹
                    if current_page == 1 and len(first_page_products) > 0:
                        first_page_success = True
                        print(" -> 1페이지 정상 수집 완료 확인.")
                        
                except Exception as page_ex:
                    print(f" -> [{current_page}페이지] 수집 중 예외 발생: {page_ex}")
                    break
                    
                time.sleep(2)
                
            # 3. 1페이지가 성공적으로 수집되었다면 전체 리뷰 수집 시작
            if first_page_success and first_page_products:
                print("\n==================================================")
                print("1페이지 수집 성공 확인! 상품 전체 리뷰 수집 기동")
                print("==================================================")
                
                for idx, prod in enumerate(first_page_products, start=1):
                    p_id = prod["product_id"]
                    p_name = prod["product_name"]
                    r_count = prod["rating_count"]
                    
                    print(f"[{idx}/{len(first_page_products)}] 상품 ID: {p_id} ('{p_name}') | 예상 리뷰수: {r_count}개")
                    
                    # SQLite DB에 상품 정보 저장/업데이트
                    db_cursor.execute("""
                    INSERT INTO products (product_id, product_name, price, rating, rating_count, product_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(product_id) DO UPDATE SET
                        product_name = excluded.product_name,
                        price = excluded.price,
                        rating = excluded.rating,
                        rating_count = excluded.rating_count
                    """, (p_id, p_name, prod["price"], prod["rating"], r_count, prod["product_url"]))
                    db_conn.commit()
                    
                    if r_count == 0:
                        print(" -> 리뷰 개수가 0개이므로 리뷰 수집을 건너뜁니다.")
                        continue
                        
                    # 브라우저 컨텍스트의 Referer와 세션 쿠키를 동기화하기 위해 상품 상세페이지로 이동
                    p_url = prod["product_url"]
                    print(f" -> 상품 상세페이지로 브라우저 이동 시도: {p_url}")
                    try:
                        page.goto(p_url, wait_until="load", timeout=30000)
                        # Lazy Loading 활성화를 위해 스크롤을 살짝 내림
                        page.evaluate("window.scrollBy(0, 500)")
                        page.wait_for_timeout(3000)
                    except Exception as goto_err:
                        print(f" -> 상세페이지 이동 실패: {goto_err}")
                        continue
                        
                    # 리뷰 수집 루프 (페이지당 100개씩 대량으로 수집)
                    review_page = 1
                    total_reviews_saved = 0
                    
                    while True:
                        # 주소창 주소가 상세페이지인 상태에서 상대경로로 Fetch 호출하여 403 차단 우회
                        review_url = f"/next-api/review?productId={p_id}&page={review_page}&size=100&sortBy=ORDER_SCORE_ASC"
                        
                        # 브라우저 컨텍스트 내에서 Fetch 호출 (Referer 헤더는 브라우저가 자동 매칭함)
                        js_code = f"""
                        async () => {{
                            try {{
                                const res = await fetch('{review_url}');
                                if (res.status !== 200) {{
                                    return {{ status: res.status, reviews: null }};
                                }}
                                const data = await res.json();
                                return {{ status: res.status, reviews: data.reviews || [] }};
                            }} catch (e) {{
                                return {{ status: 0, reviews: null, error: e.toString() }};
                            }}
                        }}
                        """
                        try:
                            res_data = page.evaluate(js_code)
                            
                            status = res_data.get("status", 0)
                            reviews = res_data.get("reviews")
                            
                            if status != 200:
                                print(f"  -> [리뷰 {review_page}p] API 응답 오류 (상태코드: {status}). 리뷰 수집을 종료합니다.")
                                break
                                
                            if not reviews:
                                print(f"  -> [리뷰 {review_page}p] 가져온 리뷰 목록이 비어있습니다. 수집을 종료합니다.")
                                break
                                
                            print(f"  -> [리뷰 {review_page}p] {len(reviews)}개 리뷰 수집 성공.")
                            
                            # 데이터베이스 저장
                            for rev in reviews:
                                r_id = str(rev.get("id"))
                                r_user = clean_broken_korean(rev.get("userName"))
                                r_rating = rev.get("rating", 0)
                                r_date = rev.get("registeredAt")
                                r_pname = clean_broken_korean(rev.get("productName"))
                                r_headline = clean_broken_korean(rev.get("headline"))
                                r_comment = clean_broken_korean(rev.get("comment"))
                                
                                db_cursor.execute("""
                                INSERT INTO reviews (review_id, product_id, user_name, rating, review_date, product_name, headline, comment)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(review_id) DO UPDATE SET
                                    rating = excluded.rating,
                                    headline = excluded.headline,
                                    comment = excluded.comment
                                """, (r_id, p_id, r_user, r_rating, r_date, r_pname, r_headline, r_comment))
                            
                            db_conn.commit()
                            total_reviews_saved += len(reviews)
                            
                            # 다음 페이지 준비
                            review_page += 1
                            
                            # 과도한 요청 방지용 딜레이
                            time.sleep(1.0)
                            
                        except Exception as rev_ex:
                            print(f"  -> [리뷰 {review_page}p] 수집 처리 중 예외 발생: {rev_ex}")
                            break
                            
                    print(f"  -> 완료: 상품 {p_id} 총 {total_reviews_saved}개 리뷰 DB 저장 완료.")
                    time.sleep(2.0)
                    
            browser.close()
            print("\n브라우저 세션이 정상 종료되었습니다.")
            
        except Exception as e:
            print(f"Playwright CDP 실행 오류: {e}")
        finally:
            proc.terminate()
            proc.wait()
            print("디버깅용 크롬 프로세스가 종료되었습니다.")
            
            try:
                time.sleep(2)
                if os.path.exists(user_data_dir):
                    import shutil
                    shutil.rmtree(user_data_dir)
                    print("임시 프로필 폴더가 삭제되었습니다.")
            except:
                pass
                
    # 4. 수집 완료 데이터 요약 및 CSV 파일 저장
    if all_products:
        df = pd.DataFrame(all_products)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print("\n==================================================")
        print(f"성공: 총 {len(all_products)}개 상품 정보를 CSV 파일로 저장 완료: {csv_path}")
        print(f"성공: 상품 정보 및 리뷰 전체를 SQLite DB에 성공적으로 저장 완료: {db_path}")
        print("==================================================")
    else:
        print("\n수집된 최종 상품 정보가 없습니다.")
        
    db_conn.close()

if __name__ == "__main__":
    scrape_coupang()
