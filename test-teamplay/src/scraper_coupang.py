"""
쿠팡 카테고리별 상품 정보 수집 스크립트 (개선본)
파일 목적: 쿠팡의 12개 건강식품 하위 카테고리 각각에 대해 1페이지를 방문하여
          상위 10개 상품(총 120개 내외)의 정보를 수집하고 SQLite DB에 저장합니다.
          기존 상품 테이블(products)에 category_name 컬럼을 추가해 카테고리 구분을 지원합니다.
작성일: 2026-06-27
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
    오인코딩된 한글 문자열을 UTF-8 한글로 복원합니다.
    """
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

def setup_sqlite_db(db_path):
    """
    SQLite 데이터베이스 테이블 구조를 초기화하고 마이그레이션합니다.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # products 테이블 생성 (category_name 컬럼 포함)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        price INTEGER,
        rating REAL,
        rating_count INTEGER,
        product_url TEXT,
        category_name TEXT
    )
    """)
    
    # 기존 테이블이 있을 경우 category_name 컬럼 마이그레이션
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN category_name TEXT;")
    except sqlite3.OperationalError:
        pass  # 이미 컬럼이 존재하는 경우
        
    conn.commit()
    return conn

def parse_product_list_from_ldjson(html_content):
    """
    쿠팡 카테고리 페이지 HTML의 ld+json 스크립트에서 상품 데이터를 파싱합니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products_data = []
    
    script_tags = soup.find_all('script', type='application/ld+json')
    
    for tag in script_tags:
        try:
            json_text = tag.string.strip() if tag.string else ""
            if not json_text:
                continue
                
            data = json.loads(json_text)
            if data.get("@type") == "ItemList":
                items = data.get("itemListElement", [])
                for item in items:
                    prod_info = item.get("item", {})
                    if prod_info.get("@type") == "Product":
                        product_name = clean_broken_korean(prod_info.get("name", ""))
                        offers = prod_info.get("offers", {})
                        price = int(offers.get("price", 0)) if offers else 0
                        
                        agg_rating = prod_info.get("aggregateRating", {})
                        rating = float(agg_rating.get("ratingValue", 0.0)) if agg_rating else 0.0
                        rating_count = int(agg_rating.get("reviewCount", 0)) if agg_rating else 0
                        
                        product_url = prod_info.get("url", "")
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www.coupang.com" + product_url
                            
                        product_id = ""
                        product_id_match = re.search(r'/products/(\d+)', product_url)
                        if product_id_match:
                            product_id = product_id_match.group(1)
                        else:
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
    CDP 크롬 제어를 사용하여 12개 건강식품 하위 카테고리 각각의 1페이지에서 상위 10개 상품 정보를 수집합니다.
    """
    db_path = os.path.join("test-teamplay", "data", "coupang.db")
    csv_path = os.path.join("test-teamplay", "data", "coupang_products.csv")
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db_conn = setup_sqlite_db(db_path)
    db_cursor = db_conn.cursor()
    
    # 수집 대상 12개 하위 카테고리 정보
    categories = [
        {"id": "501392", "name": "건강기능식품"},
        {"id": "310632", "name": "비타민/미네랄"},
        {"id": "310655", "name": "건강식품"},
        {"id": "310694", "name": "허브/식물추출물"},
        {"id": "311209", "name": "홍삼/인삼"},
        {"id": "311219", "name": "건강즙/음료"},
        {"id": "501440", "name": "꿀/프로폴리스"},
        {"id": "501446", "name": "건강분말/건강환"},
        {"id": "310722", "name": "헬스보충식품"},
        {"id": "310745", "name": "다이어트/이너뷰티"},
        {"id": "566996", "name": "영양식/선식"},
        {"id": "501398", "name": "어린이 건강식품"}
    ]
    
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
        print("에러: 크롬 브라우저를 찾을 수 없습니다.")
        return
        
    print(f"크롬 브라우저 경로: {chrome_path}")
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
    
    all_collected_products = []
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")
            
            # 카테고리별 루프 수집
            for cat_idx, cat in enumerate(categories, 1):
                cat_id = cat["id"]
                cat_name = cat["name"]
                
                url = f"https://www.coupang.com/np/categories/{cat_id}?page=1"
                print(f"\n[{cat_idx}/{len(categories)}] '{cat_name}' 카테고리 상위 10개 수집 중... URL: {url}")
                
                try:
                    page.goto(url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(3000)
                    
                    content = page.content()
                    
                    if "Access Denied" in content:
                        print(" -> [WARN] WAF 차단 감지. 10초 대기 후 리프레시 시도...")
                        page.wait_for_timeout(10000)
                        page.reload()
                        page.wait_for_timeout(3000)
                        content = page.content()
                        
                    # ld+json 파싱
                    products = parse_product_list_from_ldjson(content)
                    
                    # 백업 파서 작동
                    if not products:
                        print(" -> ld+json 데이터가 없어 백업 HTML 파서를 가동합니다.")
                        soup = BeautifulSoup(content, 'html.parser')
                        items = soup.select('.baby-product-list, .baby-product')
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
                        print(" -> 수집된 상품 정보가 없습니다.")
                        continue
                        
                    # 상위 10개 필터링 및 적재
                    valid_products = []
                    for prod in products:
                        if len(valid_products) >= 10:
                            break
                            
                        # 상품 정보 바인딩
                        p_id = prod["product_id"]
                        p_name = prod["product_name"]
                        p_price = prod["price"]
                        p_rating = prod["rating"]
                        p_rcount = prod["rating_count"]
                        p_url = prod["product_url"]
                        
                        # SQLite 적재
                        db_cursor.execute("""
                        INSERT INTO products (product_id, product_name, price, rating, rating_count, product_url, category_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(product_id) DO UPDATE SET
                            product_name = excluded.product_name,
                            price = excluded.price,
                            rating = excluded.rating,
                            rating_count = excluded.rating_count,
                            category_name = excluded.category_name
                        """, (p_id, p_name, p_price, p_rating, p_rcount, p_url, cat_name))
                        
                        valid_products.append(prod)
                        
                        # 중복 여부 확인 후 리스트업
                        if p_id not in [ap["product_id"] for ap in all_collected_products]:
                            prod["category_name"] = cat_name
                            all_collected_products.append(prod)
                            
                    db_conn.commit()
                    print(f" -> 성공: '{cat_name}' 카테고리 상위 {len(valid_products)}개 상품 데이터 적재 완료.")
                    
                except Exception as cat_err:
                    print(f" -> 카테고리 {cat_name} 수집 중 에러: {cat_err}")
                    
                # 요청 간 딜레이 적용 ( Akamai 탐지 방지 )
                time.sleep(3.0)
                
            browser.close()
            print("\n브라우저 세션이 정상적으로 종료되었습니다.")
            
        except Exception as e:
            print(f"CDP 브라우저 제어 오류: {e}")
        finally:
            proc.terminate()
            proc.wait()
            print("디버깅용 크롬 프로세스가 종료되었습니다.")
            
    # 내보내기 및 파일 요약
    if all_collected_products:
        df = pd.DataFrame(all_collected_products)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n성공: 총 {len(all_collected_products)}개 상품 정보를 CSV에 백업 완료: {csv_path}")
    else:
        print("\n수집된 상품 정보가 존재하지 않습니다.")
        
    db_conn.close()

if __name__ == "__main__":
    scrape_coupang()
