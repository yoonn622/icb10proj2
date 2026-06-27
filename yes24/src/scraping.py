"""
YES24 베스트셀러 도서 정보를 수집하는 스크래핑 스크립트입니다.
지정된 카테고리의 베스트셀러 목록 페이지를 여러 페이지에 걸쳐 요청하여 총 1000권의 도서명, 저자, 출판사, 가격, 평점 등의 정보를 추출하고 CSV 파일로 저장합니다.
"""
import json
import re
import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_yes24_bestsellers(target_count=1000):
    # 대상 URL
    url = "https://www.yes24.com/product/category/BestSellerContents"
    
    # 쿼리 파라미터 (pageNumber는 루프 내에서 변경됨)
    params = {
        "categoryNumber": "001001003",
        "sumGb": "06",
        "sex": "A",
        "age": "255",
        "goodsTp": "0",
        "addOptionTp": "0",
        "excludeTp": "2",
        "pageSize": "24",
        "goodsStatGb": "06",
        "eBookTp": "0",
        "bestType": "YES24_BESTSELLER",
        "type": "",
        "saleYear": "0",
        "saleMonth": "0",
        "weekNo": "0",
        "saleDts": "",
        "viewMode": "",
        "freeYn": ""
    }
    
    # 요청 헤더 (차단 방지용 User-Agent 설정)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.yes24.com/"
    }
    
    books_data = []
    page = 1
    
    print(f"YES24 베스트셀러 데이터 {target_count}권 수집을 시작합니다...")
    
    while len(books_data) < target_count:
        params["pageNumber"] = str(page)
        print(f"[{page} 페이지] 수집 중... (현재 수집된 도서 수: {len(books_data)}/{target_count}권)")
        
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"오류 발생: HTTP 상태 코드 {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 책 리스트 아이템 찾기
            book_elements = soup.select("li[data-goods-no]")
            
            # 페이지에 책 목록이 없으면 더 이상 데이터가 없는 것으로 판단하고 중단
            if not book_elements:
                print("더 이상 수집할 도서가 없습니다. 수집을 종료합니다.")
                break
            
            for el in book_elements:
                if len(books_data) >= target_count:
                    break
                    
                try:
                    # 1. 순위 파싱
                    rank_el = el.select_one("em.ico.rank")
                    rank = rank_el.text.strip() if rank_el else ""
                    
                    # 2. JSON 데이터 파싱 (ORD_GOODS_OPT input)
                    json_input = el.select_one("input[name='ORD_GOODS_OPT']")
                    goods_info = {}
                    if json_input and json_input.get("value"):
                        try:
                            goods_info = json.loads(json_input.get("value"))
                        except json.JSONDecodeError:
                            pass
                    
                    # JSON에서 기본 정보 추출
                    goods_no = goods_info.get("goods_no", el.get("data-goods-no"))
                    title = goods_info.get("goods_name", "")
                    category = goods_info.get("goodsSortNm", "")
                    author = goods_info.get("goodsAuth", "")
                    # 저자 이름 정리 (예: "<조태호> 저" -> "조태호")
                    if author:
                        author = re.sub(r"[<>]", "", author).replace(" 저", "").strip()
                    
                    shop_price = goods_info.get("shopPrice", 0)
                    sale_price = goods_info.get("salePrice", 0)
                    
                    # 3. HTML 구조에서 추가 정보 추출
                    # 이미지 URL
                    img_el = el.select_one("img.lazy")
                    image_url = ""
                    if img_el:
                        image_url = img_el.get("data-original") or img_el.get("src") or ""
                    
                    # 출판사
                    pub_el = el.select_one(".info_pub a")
                    if not pub_el:
                        pub_el = el.select_one(".info_pub")
                    publisher = pub_el.text.strip() if pub_el else ""
                    
                    # 출판일
                    date_el = el.select_one(".info_date")
                    pub_date = date_el.text.strip() if date_el else ""
                    
                    # 판매지수
                    sale_num_el = el.select_one(".saleNum")
                    sale_index = 0
                    if sale_num_el:
                        # '판매지수 70,965' 형태에서 숫자만 추출
                        sale_num_match = re.search(r"판매지수\s*([\d,]+)", sale_num_el.text)
                        if sale_num_match:
                            sale_index = int(sale_num_match.group(1).replace(",", ""))
                    
                    # 평점
                    rating_el = el.select_one(".rating_grade .yes_b")
                    rating = float(rating_el.text.strip()) if rating_el else 0.0
                    
                    # 리뷰 개수
                    review_el = el.select_one(".rating_rvCount .txC_blue")
                    review_count = 0
                    if review_el:
                        review_count = int(review_el.text.replace(",", "").strip())
                    
                    # 딕셔너리로 저장
                    book_item = {
                        "순위": rank,
                        "상품번호": goods_no,
                        "도서명": title,
                        "카테고리": category,
                        "저자": author,
                        "출판사": publisher,
                        "출판일": pub_date,
                        "정가": int(shop_price) if shop_price else 0,
                        "판매가": int(sale_price) if sale_price else 0,
                        "판매지수": sale_index,
                        "평점": rating,
                        "리뷰수": review_count,
                        "이미지URL": image_url
                    }
                    
                    books_data.append(book_item)
                    
                except Exception as e:
                    print(f"도서 파싱 중 오류 발생: {e}")
                    continue
            
            # 페이지 증가 및 대기 (차단 방지)
            page += 1
            time.sleep(0.5)
            
        except Exception as e:
            print(f"페이지 요청 중 오류 발생: {e}")
            break
            
    # DataFrame 생성 및 CSV 저장
    if books_data:
        df = pd.DataFrame(books_data)
        
        # 저장 경로 생성
        output_dir = os.path.join("yes24", "data")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "yes24_bestsellers.csv")
        
        # 한글 깨짐 방지를 위해 utf-8-sig 인코딩 사용
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"수집 완료! 데이터가 성공적으로 저장되었습니다: {output_path}")
        print(f"총 수집된 도서 수: {len(df)}권")
        print(df.head(5)) # 데이터 프레임의 상위 5개 미리보기 출력
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    scrape_yes24_bestsellers(target_count=1000)
