# -*- coding: utf-8 -*-
"""
Klook 검색 API를 활용하여 '대한민국' 액티비티 상품 데이터를 수집하고
SQLite DB 및 CSV 파일로 저장하는 스크립트입니다.
"""

import os
import time
import sqlite3
import csv
from datetime import datetime
from curl_cffi import requests

# 상대 경로 정의
DB_PATH = "klook/data/klook_products.db"
CSV_PATH = "klook/data/klook_products.csv"


def init_db():
    """
    SQLite 데이터베이스 및 테이블을 초기화합니다.
    """
    # 데이터 폴더가 없으면 생성
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # klook_products 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS klook_products (
            vertical_id INTEGER PRIMARY KEY,
            title TEXT,
            sub_title TEXT,
            city_name TEXT,
            category TEXT,
            cover_url TEXT,
            deep_link TEXT,
            sold_out INTEGER,
            location_lat REAL,
            location_lon REAL,
            review_star REAL,
            review_count INTEGER,
            participant_count INTEGER,
            display_price REAL,
            selling_price_format TEXT,
            collected_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] 데이터베이스 및 테이블 초기화 완료")


def save_to_db(products):
    """
    수집한 상품 리스트를 SQLite DB에 저장합니다.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted_count = 0
    for p in products:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO klook_products (
                    vertical_id, title, sub_title, city_name, category,
                    cover_url, deep_link, sold_out, location_lat, location_lon,
                    review_star, review_count, participant_count, display_price,
                    selling_price_format, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p['vertical_id'], p['title'], p['sub_title'], p['city_name'], p['category'],
                p['cover_url'], p['deep_link'], p['sold_out'], p['location_lat'], p['location_lon'],
                p['review_star'], p['review_count'], p['participant_count'], p['display_price'],
                p['selling_price_format'], p['collected_at']
            ))
            inserted_count += 1
        except Exception as e:
            print(f"[DB Error] ID {p['vertical_id']} 저장 중 오류 발생: {e}")
            
    conn.commit()
    conn.close()
    print(f"[DB] 총 {inserted_count}개의 상품 데이터 저장/업데이트 완료")


def save_to_csv(products):
    """
    수집한 상품 리스트를 CSV 파일로 저장합니다.
    """
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    
    if not products:
        print("[CSV] 저장할 상품 데이터가 없습니다.")
        return
        
    keys = products[0].keys()
    
    try:
        with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(products)
        print(f"[CSV] '{CSV_PATH}' 파일 저장 완료 (총 {len(products)}개 행)")
    except Exception as e:
        print(f"[CSV Error] CSV 저장 중 오류 발생: {e}")


def parse_card(card):
    """
    API 응답 카드 객체에서 필요한 필드들을 파싱합니다.
    """
    data = card.get("data", {})
    track_info = card.get("track_info", {})
    
    # 위도, 경도 분리
    location_str = data.get("location")
    lat, lon = None, None
    if location_str and "," in location_str:
        try:
            lat_str, lon_str = location_str.split(",")
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            pass
            
    # 품절 여부
    sold_out = 1 if data.get("sold_out") else 0
    
    # 리뷰 점수 및 횟수
    review_star = track_info.get("review_rating")
    if review_star is None:
        # data.review_obj.star 파싱 시도
        review_obj = data.get("review_obj") or {}
        try:
            review_star = float(review_obj.get("star", 0.0))
        except ValueError:
            review_star = 0.0
            
    review_count = track_info.get("review_count")
    if review_count is None:
        # count 파싱 시도
        review_obj = data.get("review_obj") or {}
        review_count_str = review_obj.get("number", "0")
        # 괄호나 콤마 제거
        review_count_str = "".join(c for c in review_count_str if c.isdigit())
        try:
            review_count = int(review_count_str) if review_count_str else 0
        except ValueError:
            review_count = 0

    # 예약자 수
    participant_count = track_info.get("product_participant_count", 0)
    
    # 가격 정보
    price_obj = data.get("price") or {}
    selling_price_format = price_obj.get("selling_price_format", "")
    display_price = track_info.get("display_price")
    if display_price is None:
        # selling_price 에서 수치 추출 시도 (예: "HK$ 77")
        selling_price_str = price_obj.get("selling_price", "")
        price_digits = "".join(c for c in selling_price_str if c.isdigit() or c == '.')
        try:
            display_price = float(price_digits) if price_digits else 0.0
        except ValueError:
            display_price = 0.0

    parsed = {
        "vertical_id": data.get("vertical_id"),
        "title": data.get("title"),
        "sub_title": data.get("sub_title"),
        "city_name": data.get("city_name"),
        "category": data.get("category"),
        "cover_url": data.get("cover_url"),
        "deep_link": data.get("deep_link"),
        "sold_out": sold_out,
        "location_lat": lat,
        "location_lon": lon,
        "review_star": review_star,
        "review_count": review_count,
        "participant_count": participant_count,
        "display_price": display_price,
        "selling_price_format": selling_price_format,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return parsed


def scrape_klook():
    """
    Klook API를 호출하여 1~10페이지까지 데이터를 수집합니다.
    """
    url = "https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3"
    
    # 공통 헤더 설정
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-klook-market": "global",
        "x-klook-user-residence": "10_KR",
        "x-platform": "desktop",
        "x-requested-with": "XMLHttpRequest",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    # 공통 쿼리 매개변수
    base_params = {
        "location": "158,157,156,25723,5031,8928,24975,28741,545,6166,6268,703649,703648,705582,6955,15088,701102,16467,707516,26374,7204,20296,28972,28785,8898,23546,30633,15378,16365,28742,10956,26961,10093,16560,25178,30570,7558,7741,11925,24865,25140,707332,8989,10706,11364,11745,13523,14446,15281,15603,16655,18214,18323,20392,22390,22675,23237,24520,24762,25060,26454,27895,29136,29872,30051,30265,30376,30466,31247,7030,705101,9079",
        "sort": "most_relevant",
        "tab_key": "0",
        "query": "대한민국",
        "size": "15",
        "search_scope": "main_search",
        "k_lang": "ko_KR",
        "k_currency": "KRW"
    }

    all_parsed_products = []
    
    # 1페이지부터 10페이지까지 순회
    for page in range(1, 11):
        print(f"[수집] {page}/10 페이지 요청 중...")
        params = base_params.copy()
        params["start"] = str(page)
        
        # 최대 3회 재시도
        for attempt in range(1, 4):
            try:
                response = requests.get(url, params=params, headers=headers, impersonate="chrome110", timeout=10)
                if response.status_code == 200:
                    data_json = response.json()
                    if data_json.get("success"):
                        cards = data_json.get("result", {}).get("search_result", {}).get("cards", [])
                        print(f"[성공] {page}페이지에서 {len(cards)}개 상품 카드를 가져왔습니다.")
                        
                        for card in cards:
                            # card 구조 유효성 검사 후 파싱
                            if card.get("data") and card.get("data").get("vertical_id"):
                                parsed = parse_card(card)
                                all_parsed_products.append(parsed)
                        break
                    else:
                        error_msg = data_json.get("error", {}).get("message", "알 수 없는 오류")
                        print(f"[오류] API 결과 실패: {error_msg} (시도 {attempt}/3)")
                else:
                    print(f"[오류] HTTP {response.status_code} 응답 (시도 {attempt}/3)")
            except Exception as e:
                print(f"[에러] 요청 중 예외 발생: {e} (시도 {attempt}/3)")
            
            # 재시도 전 대기
            time.sleep(2)
        else:
            print(f"[실패] {page}페이지 수집을 완료하지 못했습니다.")
            
        # 페이지 간 요청 간격 대기 (부하 방지 및 봇 차단 예방)
        time.sleep(1.5)
        
    return all_parsed_products


def main():
    print("=== Klook 대한민국 액티비티 수집 스크립트 시작 ===")
    
    # 1. DB 초기화
    init_db()
    
    # 2. 데이터 수집
    products = scrape_klook()
    
    # 3. 데이터 저장
    if products:
        # SQLite DB 저장
        save_to_db(products)
        # CSV 저장
        save_to_csv(products)
        print(f"=== 수집 및 저장 완료 (총 {len(products)}개 아이템) ===")
    else:
        print("=== 수집된 데이터가 없습니다. ===")


if __name__ == "__main__":
    main()
