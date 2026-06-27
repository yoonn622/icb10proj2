"""
iHerb 특가 상품 데이터 수집 스크립트 (다중 페이지 버전)
파일 목적: iHerb Supplements Specials API를 루프 호출하여 전체의 약 1/3 분량인 45페이지의 상품 데이터를 수집하고 CSV로 저장합니다.
작성일: 2026-06-17
"""

import os
import time
import requests
import pandas as pd

def scrape_iherb_specials_multi_pages(target_pages=45):
    # iHerb 보충제(Supplements) 특가 상품 API URL
    url = "https://catalog.app.iherb.com/category/supplements/specials"
    
    # 브라우저 요청을 모방하기 위한 HTTP 헤더 정보 설정
    headers = {
        "referer": "https://kr.iherb.com/",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }
    
    all_extracted_data = []
    
    print(f"iHerb 특가 상품 데이터 수집을 시작합니다. 목표 페이지 수: {target_pages}페이지")
    
    for page in range(1, target_pages + 1):
        # 쿼리 파라미터 구성 (페이지 루프 적용)
        params = {
            "isMobile": "false",
            "page": page,
            "pageSize": 18
        }
        
        print(f"[{page}/{target_pages}] API 요청 중...")
        try:
            # GET 요청 전송
            response = requests.get(url, headers=headers, params=params)
            
            # 서버 트래픽 부하 및 차단(WAF) 방지를 위한 딜레이 설정
            time.sleep(0.5)
            
            # 페이지 미존재 시 루프 종료
            if response.status_code == 404:
                print(f" -> {page}페이지가 존재하지 않습니다. 수집을 종료합니다.")
                break
                
            response.raise_for_status()
            
            # JSON 데이터 가공
            data = response.json()
            products = data.get("products", [])
            
            if not products:
                print(f" -> {page}페이지에 상품 데이터가 비어 있습니다. 수집을 완료합니다.")
                break
                
            print(f" -> {len(products)}개의 상품 데이터를 획득했습니다.")
            
            # 핵심 상품 필드 추출
            for prod in products:
                item = {
                    "productId": prod.get("productId"),
                    "displayName": prod.get("displayName"),
                    "url": prod.get("url"),
                    "partNumber": prod.get("partNumber"),
                    "listPrice": prod.get("listPrice"),
                    "discountPrice": prod.get("discountPrice"),
                    "rating": prod.get("rating"),
                    "ratingCount": prod.get("ratingCount"),
                    "brandName": prod.get("brandName"),
                    "brandCode": prod.get("brandCode"),
                    "isOutOfStock": prod.get("isOutOfStock"),
                    "salesDiscountPercentage": prod.get("salesDiscountPercentage")
                }
                all_extracted_data.append(item)
                
        except requests.exceptions.RequestException as e:
            print(f" -> {page}페이지 수집 중 에러가 발생했습니다: {e}")
            print("수집을 중단하고 현재까지 획득한 데이터만 저장을 시도합니다.")
            break
            
    if not all_extracted_data:
        print("수집 완료된 상품 데이터가 없습니다. 작업을 종료합니다.")
        return
        
    # pandas DataFrame 변환
    df = pd.DataFrame(all_extracted_data)
    
    # 저장 경로 및 디렉토리 설정 (상대 경로 준수)
    output_dir = os.path.join("test-teamplay", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "iherb_specials_1_3.csv")
    
    # CSV 저장 (utf-8-sig 인코딩)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"성공: 총 {len(all_extracted_data)}개의 상품 정보를 CSV 파일로 저장하였습니다: {output_path}")

if __name__ == "__main__":
    scrape_iherb_specials_multi_pages()
