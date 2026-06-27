"""
iherb의 스포츠 특가 상품(Sports Specials) 페이지 데이터를 전체 수집하는 스크래핑 스크립트입니다.
iherb API를 사용하여 스포츠 특가 상품의 모든 페이지 정보를 순회하며 가져와 
제품 ID, 제품명, 브랜드명, 정가, 할인가, 평점, 평점 수, 품절 여부 및 상품 URL을 추출하고 CSV 파일로 저장합니다.
"""
import os
import time
import requests
import pandas as pd

def scrape_iherb_sports_specials():
    # 대상 API URL
    url = "https://catalog.app.iherb.com/category/sports/specials"
    
    # 쿼리 파라미터 기본 설정
    params = {
        "isMobile": "false",
        "pageSize": "18"
    }
    
    # 요청 헤더 (iherb API 요청용 필수 헤더)
    headers = {
        "origin": "https://kr.iherb.com",
        "priority": "u=1, i",
        "referer": "https://kr.iherb.com/",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }
    
    products_data = []
    collected_ids = set()
    page = 1
    
    print("iherb 스포츠 특가 상품 전체 데이터 수집을 시작합니다 (1페이지부터 마지막 페이지까지)...")
    
    while True:
        params["page"] = str(page)
        print(f"[{page} 페이지] 요청 중... (현재 수집된 고유 상품 수: {len(products_data)}개)")
        
        try:
            # API 요청
            response = requests.get(url, params=params, headers=headers)
            
            # 상태 코드 확인
            if response.status_code != 200:
                print(f"오류 발생: HTTP 상태 코드 {response.status_code}")
                break
                
            data = response.json()
            products = data.get("products", [])
            
            # 더 이상 상품 데이터가 없으면 수집 종료
            if not products:
                print("더 이상 수집할 상품 데이터가 없습니다. 수집을 종료합니다.")
                break
                
            new_added_in_page = 0
            for prod in products:
                prod_id = prod.get("productId")
                if prod_id in collected_ids:
                    continue
                
                # 필요한 필드만 추출하여 매핑
                product_item = {
                    "제품ID": prod_id,
                    "제품명": prod.get("displayName"),
                    "브랜드명": prod.get("brandName"),
                    "정가": prod.get("listPrice"),
                    "할인가": prod.get("discountPrice"),
                    "할인가수치": prod.get("discountPriceValue"),
                    "평점": prod.get("rating"),
                    "평점수": prod.get("ratingCount"),
                    "품절여부": prod.get("isOutOfStock"),
                    "상품URL": prod.get("url")
                }
                products_data.append(product_item)
                collected_ids.add(prod_id)
                new_added_in_page += 1
                
            print(f"[{page} 페이지] 파싱 완료: {len(products)}개 중 신규 상품 {new_added_in_page}개 추가됨")
            
            # 이번 페이지에서 새로 추가된 상품이 하나도 없다면 종료
            if new_added_in_page == 0:
                print("새롭게 추가된 상품이 없으므로 수집을 완료합니다.")
                break
                
            # 페이지 증가 및 대기 (차단 방지)
            page += 1
            time.sleep(1.0)
            
        except Exception as e:
            print(f"데이터 수집 중 예외 발생: {e}")
            break
            
    # DataFrame 생성 및 저장
    if products_data:
        df = pd.DataFrame(products_data)
        
        # 저장 경로 설정 (상대경로 iherb/data 사용)
        output_dir = os.path.join("iherb", "data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "sports_specials.csv")
        
        # CSV 파일로 저장 (한글 깨짐 방지 utf-8-sig 인코딩 사용)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        print(f"수집 및 저장 완료: {output_path}")
        print(f"최종 수집된 고유 상품 수: {len(df)}개")
        print("\n[수집된 데이터 미리보기]")
        print(df.head(5))
    else:
        print("수집된 상품 데이터가 없어 저장하지 않았습니다.")

if __name__ == "__main__":
    scrape_iherb_sports_specials()
