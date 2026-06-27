"""
iherb의 일반 스포츠 상품(Sports Products) 페이지 데이터를 수집하는 스크래핑 스크립트입니다.
sports_product_scraping_prompt.md에 정의된 AJAX 요청 형식에 맞추어 
curl_cffi 라이브러리로 Cloudflare 보안을 우회하여 1페이지부터 10페이지까지 데이터를 HTML 형식으로 가져옵니다.
이후 BeautifulSoup을 통해 제품 ID, 제품명, 브랜드명, 정가, 할인가, 평점, 평점 수, 품절 여부 및 상품 URL을 추출한 후 
각 페이지마다 개별 CSV 파일 및 SQLite DB 파일(.db)로 저장합니다.
"""
import os
import re
import time
import json
import sqlite3
from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_iherb_sports_product_page(page):
    # 대상 AJAX URL
    url = "https://kr.iherb.com/c/sports"
    
    # 쿼리 파라미터 (지정된 페이지 수집 및 AJAX 응답 활성화)
    params = {
        "p": str(page),
        "isAjax": "true"
    }
    
    # 요청 헤더 (Cloudflare 및 봇 감지 우회를 위한 브라우저 헤더 정보)
    headers = {
        "priority": "u=1, i",
        "referer": "https://kr.iherb.com/c/sports",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    
    print(f"[{page} 페이지] 데이터 수집 요청 중...")
    
    try:
        # curl_cffi를 활용해 Chrome 브라우저 TLS 지문 모방 요청 전송 (Cloudflare 우회)
        response = requests.get(url, params=params, headers=headers, impersonate="chrome")
        
        if response.status_code != 200:
            print(f"오류 발생: HTTP 상태 코드 {response.status_code}")
            return False
            
        # HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")
        product_elements = soup.select(".product.ga-product")
        
        if not product_elements:
            print(f"[{page} 페이지] 상품 요소를 찾을 수 없습니다. (마지막 페이지 도달 가능성)")
            return False
            
        products_data = []
        
        for el in product_elements:
            try:
                # 제품 고유 ID 추출
                prod_id = el.get("id", "").replace("pid_", "") or el.get("data-product-id")
                
                # 품절 여부
                is_out_of_stock = el.get("data-is-out-of-stock", "false").lower() == "true"
                
                # 링크 및 기본 메타 정보
                link_el = el.select_one("a.product-link")
                url_path = link_el.get("href") if link_el else ""
                brand_name = link_el.get("data-ga-brand-name") if link_el else ""
                discount_val = link_el.get("data-ga-discount-price") if link_el else ""
                display_name = link_el.get("title") if link_el else ""
                
                # 장바구니 데이터를 파싱하여 정가 및 할인가 보정
                list_price = ""
                discount_price = ""
                cart_btn = el.select_one("button.btn-add-to-cart")
                if cart_btn and cart_btn.get("data-cart-info"):
                    try:
                        cart_info = json.loads(cart_btn.get("data-cart-info"))
                        if 'lineItems' in cart_info and len(cart_info['lineItems']) > 0:
                            item_info = cart_info['lineItems'][0]
                            list_price = item_info.get("listPrice", "")
                            discount_price = item_info.get("discountPrice", "")
                    except Exception:
                        pass
                
                # 평점 및 평점수 파싱 (title 속성 활용)
                rating = ""
                rating_count = ""
                rating_link = el.select_one(".rating a.stars")
                if rating_link and rating_link.get("title"):
                    title_text = rating_link.get("title")
                    rating_match = re.search(r"([\d.]+)/5", title_text)
                    count_match = re.search(r"-\s*([\d,]+)", title_text)
                    
                    rating = rating_match.group(1) if rating_match else ""
                    rating_count = count_match.group(1).replace(",", "") if count_match else ""
                
                product_item = {
                    "제품ID": prod_id,
                    "제품명": display_name,
                    "브랜드명": brand_name,
                    "정가": list_price,
                    "할인가": discount_price,
                    "할인가수치": discount_val,
                    "평점": rating,
                    "평점수": rating_count,
                    "품절여부": is_out_of_stock,
                    "상품URL": url_path
                }
                products_data.append(product_item)
                
            except Exception as e:
                print(f"상품 요소 파싱 중 오류 발생: {e}")
                continue
                
        if not products_data:
            return False
            
        # DataFrame 생성
        df = pd.DataFrame(products_data)
        
        # 저장 폴더 및 파일 경로 설정 (페이지별 저장)
        output_dir = os.path.join("iherb", "data")
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. CSV 파일로 저장 (한글 인코딩 처리 utf-8-sig)
        csv_path = os.path.join(output_dir, f"sports_products_page_{page}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        # 2. SQLite DB 파일로 저장
        db_path = os.path.join(output_dir, f"sports_products_page_{page}.db")
        conn = sqlite3.connect(db_path)
        try:
            # DB용 영문 컬럼명 매핑
            db_df = df.rename(columns={
                "제품ID": "productId",
                "제품명": "displayName",
                "브랜드명": "brandName",
                "정가": "listPrice",
                "할인가": "discountPrice",
                "할인가수치": "discountPriceValue",
                "평점": "rating",
                "평점수": "ratingCount",
                "품절여부": "isOutOfStock",
                "상품URL": "url"
            })
            # sqlite db에 products 테이블로 저장 (기존 데이터가 있다면 교체)
            db_df.to_sql("products", conn, if_exists="replace", index=False)
        finally:
            conn.close()
        
        print(f"[{page} 페이지] 수집 및 저장 완료 (CSV: {csv_path}, DB: {db_path})")
        return True
        
    except Exception as e:
        print(f"[{page} 페이지] 데이터 수집 중 예외 발생: {e}")
        return False

def scrape_iherb_sports_products_bulk(start_page=1, end_page=10):
    print(f"iherb 스포츠 상품 대량 수집 시작 ({start_page}페이지 ~ {end_page}페이지)...")
    success_count = 0
    
    for page in range(start_page, end_page + 1):
        success = scrape_iherb_sports_product_page(page)
        if success:
            success_count += 1
        else:
            print(f"[{page} 페이지] 수집 실패 또는 데이터 없음으로 중단합니다.")
            break
        # 서버 과부하 및 차단 방지를 위한 대기 시간 부여
        time.sleep(1.0)
        
    print(f"대량 수집 완료! 총 {success_count}개 페이지가 CSV 및 SQLite DB로 저장되었습니다.")

if __name__ == "__main__":
    scrape_iherb_sports_products_bulk(start_page=1, end_page=10)
