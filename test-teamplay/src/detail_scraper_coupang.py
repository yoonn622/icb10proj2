"""
쿠팡 상품 상세페이지 수집 스크립트
파일 목적: SQLite 데이터베이스(coupang.db)의 products 테이블에서 상위 10개 상품을 조회한 뒤,
          각 상품의 상세페이지에 CDP 크롬 제어(Playwright)를 통해 실제 브라우저처럼 접근하여
          브랜드, 상품 정보 고시 테이블, 상세설명 딥링크(iframe src), 상세설명 이미지 리스트를 수집하고
          이를 product_details 테이블에 별도로 적재합니다.
          최종적으로 products 테이블과 product_details 테이블을 조인하여 CSV 백업 및 요약본을 제공합니다.
작성일: 2026-06-27
"""

import os
import sys
import time
import sqlite3
import subprocess
import json
import re
from urllib.parse import urljoin
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

def setup_details_table(db_path):
    """
    SQLite 데이터베이스에 product_details 테이블을 초기화합니다.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_details (
        product_id TEXT PRIMARY KEY,
        brand TEXT,
        manufacturer TEXT,
        origin TEXT,
        expiration_date TEXT,
        package_volume TEXT,
        deep_link_url TEXT,
        detail_images TEXT,
        spec_table_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)
    conn.commit()
    return conn

def parse_spec_table(soup):
    """
    상세페이지 HTML 내에서 상품 필수 고시 정보 테이블을 파싱하여 딕셔너리로 반환합니다.
    """
    spec_data = {}
    tables = soup.select("table")
    
    for table in tables:
        classes = table.get("class", [])
        # 배송/반품 등의 정책 테이블 및 관련 없는 테이블은 제외
        if "prod-delivery-return-policy-table" in classes:
            continue
            
        # 건강식품 등의 스펙 테이블은 보통 twc-w-full 또는 prod-delivery-spec-table 등의 클래스를 가짐
        # 혹은 td/th 구조를 띰
        rows = table.select("tr")
        if not rows:
            continue
            
        # 첫 번째 행의 td 구조 체크
        for r in rows:
            tds = [t.text.strip() for t in r.select("td")]
            ths = [t.text.strip() for t in r.select("th")]
            
            # th-td 매핑 구조인 경우
            if ths and tds and len(ths) == len(tds):
                for k, v in zip(ths, tds):
                    if k:
                        spec_data[k] = v
            # td만 존재하고 4개인 구조 [키1, 값1, 키2, 값2] (쿠팡 개편 스펙 테이블 형식)
            elif len(tds) == 4:
                spec_data[tds[0]] = tds[1]
                spec_data[tds[2]] = tds[3]
            # td만 존재하고 2개인 구조 [키1, 값1]
            elif len(tds) == 2:
                spec_data[tds[0]] = tds[1]
                
    return spec_data

def extract_field_by_keywords(spec_dict, keywords, exclude_keywords=None):
    """
    고시 정보 딕셔너리에서 키워드 매칭을 통해 특정 필드(제조국, 제조사 등) 값을 추출합니다.
    """
    for key, val in spec_dict.items():
        # 제외 키워드가 매칭되면 건너뜀
        if exclude_keywords and any(ex in key for ex in exclude_keywords):
            continue
        if any(kw in key for kw in keywords):
            return val
    return ""

def main():
    db_path = os.path.join("test-teamplay", "data", "coupang.db")
    csv_output_path = os.path.join("test-teamplay", "data", "coupang_products_with_details.csv")
    
    if not os.path.exists(db_path):
        print(f"에러: 데이터베이스 파일이 존재하지 않습니다: {db_path}")
        return
        
    # SQLite DB 초기화 및 대상 상품 선정
    db_conn = setup_details_table(db_path)
    db_cursor = db_conn.cursor()
    
    # 수집 대상 상품 조회 (전체 상품 대상)
    db_cursor.execute("""
        SELECT product_id, product_name, product_url 
        FROM products 
        ORDER BY rating_count DESC
    """)
    target_products = db_cursor.fetchall()
    
    if not target_products:
        print("수집 대상 상품이 products 테이블에 존재하지 않습니다.")
        db_conn.close()
        return
        
    print(f"상위 10개 수집 대상 상품 조회 완료. (총 {len(target_products)}개)")
    for i, prod in enumerate(target_products, 1):
        print(f"  {i}. ID: {prod[0]} | 이름: {prod[1][:30]}...")
        
    # 원격 디버깅 크롬 기동
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
        print("에러: 구글 크롬 브라우저를 찾을 수 없습니다.")
        db_conn.close()
        return
        
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
    # 윈도우 환경이라도 화면에 직접 보이게 실행하기 위해 숨김 처리를 비활성화합니다.
    # if sys.platform == "win32":
    #     startupinfo = subprocess.STARTUPINFO()
    #     startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    proc = subprocess.Popen(chrome_cmd, startupinfo=startupinfo)
    time.sleep(4)
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            # webdriver 감지 비활성화
            page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")
            
            # 세션 인식을 위해 먼저 쿠팡 홈 또는 카테고리 홈을 1회 방문하여 Akamai WAF 쿠키가 완성되도록 12초간 대기합니다.
            print("세션 활성화를 위해 쿠팡 카테고리 페이지 방문 중 (12초 대기)...")
            page.goto("https://www.coupang.com/np/categories/305798?traceId=mqp7vpnb", wait_until="load", timeout=30000)
            page.wait_for_timeout(12000)
            
            for idx, (p_id, p_name, p_url) in enumerate(target_products, start=1):
                print(f"\n==================================================")
                print(f"[{idx}/10] 상품 상세페이지 수집 중... ID: {p_id}")
                print(f"이름: {p_name}")
                print(f"URL: {p_url}")
                print(f"==================================================")
                
                # 상세페이지 이동
                try:
                    page.goto(p_url, wait_until="load", timeout=40000)
                    page.wait_for_timeout(3000)
                except Exception as goto_err:
                    print(f" -> 상세페이지 이동 중 에러 발생: {goto_err}")
                    continue
                    
                # 403 차단 여부 체크 및 자동 리트라이 우회
                content = page.content()
                retry_count = 0
                max_retries = 3
                
                while ("Access Denied" in content or "Error 403" in content or "죄송합니다" in content) and retry_count < max_retries:
                    retry_count += 1
                    print(f" -> [WARN] 쿠팡 방화벽 차단 감지됨. 자동 우회 및 리트라이를 시도합니다. ({retry_count}/{max_retries})")
                    
                    # 카테고리 페이지로 이동하여 세션 리프레시 유도
                    print("  -> 세션 리프레시를 위해 카테고리 페이지로 이동...")
                    try:
                        page.goto("https://www.coupang.com/np/categories/305798?traceId=mqp7vpnb", wait_until="load", timeout=30000)
                        page.wait_for_timeout(2000)
                        # 자연스러운 모션을 위해 마우스 이동 및 스크롤 시뮬레이션
                        page.mouse.move(100, 100)
                        page.wait_for_timeout(1000)
                        page.evaluate("window.scrollBy(0, 500)")
                        print("  -> Akamai 챌린지 갱신을 위해 15초 대기 중...")
                        page.wait_for_timeout(15000)
                    except Exception as refresh_err:
                        print(f"  -> 세션 리프레시 중 에러: {refresh_err}")
                        
                    # 다시 상세페이지로 이동
                    print(f"  -> 상품 상세페이지 재진입 시도: {p_url}")
                    try:
                        page.goto(p_url, wait_until="load", timeout=40000)
                        page.wait_for_timeout(3000)
                        content = page.content()
                    except Exception as goto_err:
                        print(f"  -> 상세페이지 재진입 중 에러: {goto_err}")
                        
                # 3회 자동 우회 시도 후에도 여전히 차단 상태일 경우 수동 해결 요청 (화면에 브라우저가 보임)
                if "Access Denied" in content or "Error 403" in content or "죄송합니다" in content:
                    print(" [WARN] 자동 우회 실패. 브라우저 창에서 슬라이더를 밀거나 보안 챌린지를 수동으로 완료해 주세요.")
                    print(" 챌린지를 완료한 후 콘솔 창에서 [Enter] 키를 누르면 계속 진행됩니다.")
                    input(" >> 챌린지 수행 완료 후 Enter를 누르세요...")
                    page.reload(wait_until="load")
                    page.wait_for_timeout(3000)
                    content = page.content()
                    
                # 스크롤 다운을 통해 비동기 데이터 렌더링 활성화
                print(" -> 상세 페이지 스크롤 다운 수행 중...")
                for s in range(1, 5):
                    page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {s} / 4)")
                    page.wait_for_timeout(1000)
                page.wait_for_timeout(2000)
                
                # 최신 HTML 로드
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # 1) 브랜드 파싱
                brand = ""
                for brand_sel in [".prod-brand-share-and-alpha-area a.prod-brand", ".prod-brand", ".brand-link", "a[data-brand-name]", ".prod-brand-name"]:
                    b_tag = soup.select_one(brand_sel)
                    if b_tag:
                        brand = b_tag.text.strip()
                        break
                
                # 2) 필수 고시 정보 테이블 파싱
                spec_dict = parse_spec_table(soup)
                spec_table_json = json.dumps(spec_dict, ensure_ascii=False)
                
                # 고시 정보 내 주요 항목 정밀 파싱
                manufacturer = extract_field_by_keywords(spec_dict, ["제조자", "제조원", "생산자", "수입자"], ["제조국", "원산지"])
                origin = extract_field_by_keywords(spec_dict, ["제조국", "원산지"])
                expiration_date = extract_field_by_keywords(spec_dict, ["유통기한", "소비기한", "품질유지", "제조연월일"])
                package_volume = extract_field_by_keywords(spec_dict, ["용량", "중량", "수량", "내용물"])
                
                # 3) 상세설명 딥링크 (iframe src) 추출 및 상세 이미지 수집
                deep_link_url = ""
                detail_images_list = []
                
                # 쿠팡 상세페이지는 상세설명을 iframe 태그로 로드하는 경우가 흔함
                iframe_tag = soup.select_one("iframe.product-detail-content-iframe, #productDetail iframe")
                if iframe_tag and iframe_tag.get("src"):
                    raw_src = iframe_tag.get("src")
                    # 상대 경로일 경우 절대 경로로 결합
                    deep_link_url = urljoin(p_url, raw_src)
                    print(f" -> 상세 정보 딥링크(iframe src) 검출됨: {deep_link_url}")
                    
                    # 딥링크 iframe 페이지로 브라우저를 직접 이동시켜 이미지 추출 시도
                    try:
                        # 새 탭을 열어 딥링크 직접 접근
                        iframe_page = context.new_page()
                        iframe_page.goto(deep_link_url, wait_until="load", timeout=30000)
                        iframe_page.wait_for_timeout(2000)
                        
                        iframe_content = iframe_page.content()
                        iframe_soup = BeautifulSoup(iframe_content, 'html.parser')
                        
                        # iframe 내부 이미지들 추출
                        for img in iframe_soup.select("img"):
                            src = img.get("src")
                            if isinstance(src, list):
                                src = src[0] if src else ""
                            if src and isinstance(src, str):
                                if src.startswith("//"):
                                    src = "https:" + src
                                if src not in detail_images_list:
                                    detail_images_list.append(src)
                                
                        iframe_page.close()
                    except Exception as iframe_err:
                        print(f"  -> 딥링크 iframe 페이지 접근 실패: {iframe_err}")
                
                # 만약 iframe이 없거나 iframe 내부 이미지 추출이 안 되었다면 메인 페이지 백업 추출
                if not detail_images_list:
                    print(" -> 메인 페이지 DOM에서 상세설명 이미지 직접 추출 중...")
                    # 상세설명 컨테이너 이미지들
                    for img_sel in ["#productDetail img", ".product-detail img", ".prod-image-detail img", ".subType-IMAGE img", ".subType-TEXT img"]:
                        for img in soup.select(img_sel):
                            src = img.get("src")
                            if isinstance(src, list):
                                src = src[0] if src else ""
                            if src and isinstance(src, str):
                                if src.startswith("//"):
                                    src = "https:" + src
                                if src not in detail_images_list:
                                    detail_images_list.append(src)
                
                # 최종 이미지 리스트 JSON 직렬화
                detail_images_json = json.dumps(detail_images_list, ensure_ascii=False)
                
                print(f" -> 수집 완료 요약:")
                print(f"    * 브랜드: {brand if brand else '미검출'}")
                print(f"    * 제조사: {manufacturer if manufacturer else '미검출'}")
                print(f"    * 원산지: {origin if origin else '미검출'}")
                print(f"    * 소비기한: {expiration_date if expiration_date else '미검출'}")
                print(f"    * 내용물용량: {package_volume if package_volume else '미검출'}")
                print(f"    * 딥링크: {deep_link_url if deep_link_url else '미검출'}")
                print(f"    * 수집된 상세이미지 수: {len(detail_images_list)}개")
                
                # 데이터베이스 저장
                db_cursor.execute("""
                INSERT INTO product_details (
                    product_id, brand, manufacturer, origin, expiration_date, 
                    package_volume, deep_link_url, detail_images, spec_table_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(product_id) DO UPDATE SET
                    brand = excluded.brand,
                    manufacturer = excluded.manufacturer,
                    origin = excluded.origin,
                    expiration_date = excluded.expiration_date,
                    package_volume = excluded.package_volume,
                    deep_link_url = excluded.deep_link_url,
                    detail_images = excluded.detail_images,
                    spec_table_json = excluded.spec_table_json,
                    updated_at = CURRENT_TIMESTAMP
                """, (p_id, brand, manufacturer, origin, expiration_date, package_volume, deep_link_url, detail_images_json, spec_table_json))
                db_conn.commit()
                
                # 요청 간 딜레이
                time.sleep(3.0)
                
            browser.close()
            print("\n브라우저 세션이 정상 종료되었습니다.")
            
        except Exception as e:
            print(f"Playwright CDP 제어 오류: {e}")
        finally:
            proc.terminate()
            proc.wait()
            print("디버깅용 크롬 프로세스가 종료되었습니다.")
            
            # 임시 프로필 폴더 삭제 (세션 연속성을 확보하기 위해 삭제하지 않고 보관)
            # try:
            #     time.sleep(2)
            #     if os.path.exists(user_data_dir):
            #         import shutil
            #         shutil.rmtree(user_data_dir)
            #         print("임시 프로필 폴더가 삭제되었습니다.")
            # except Exception as rmtree_err:
            #     print(f"임시 프로필 폴더 삭제 실패: {rmtree_err}")
            pass
                
    # 5) 조인 쿼리 결과 검증 및 CSV 파일로 백업 저장
    print("\n==================================================")
    print("수집 완료 검증: 상품 테이블 & 상세 정보 테이블 조인 실행")
    print("==================================================")
    
    try:
        # SQL JOIN 쿼리 수행
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.price,
            p.rating,
            p.rating_count,
            d.brand,
            d.manufacturer,
            d.origin,
            d.expiration_date,
            d.package_volume,
            d.deep_link_url,
            d.detail_images
        FROM products p
        INNER JOIN product_details d ON p.product_id = d.product_id
        ORDER BY p.rating_count DESC
        """
        df_joined = pd.read_sql_query(query, db_conn)
        
        # CSV 저장
        df_joined.to_csv(csv_output_path, index=False, encoding="utf-8-sig")
        print(f"성공: 조인 데이터셋을 CSV 파일로 저장 완료: {csv_output_path}")
        print(f"조인된 데이터 행(Row) 수: {len(df_joined)}개")
        print("\n--- 조인 결과 상위 3개 요약 미리보기 ---")
        print(df_joined[['product_id', 'product_name', 'brand', 'origin', 'expiration_date']].head(3).to_string(index=False))
        
    except Exception as sql_err:
        print(f"조인 검증 및 CSV 저장 중 오류 발생: {sql_err}")
        
    db_conn.close()
    print("\n모든 작업이 성공적으로 완료되었습니다.")

if __name__ == "__main__":
    main()
