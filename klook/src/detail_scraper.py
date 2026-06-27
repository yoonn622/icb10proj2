# -*- coding: utf-8 -*-
"""
Klook 상세페이지 데이터(가격, 평점, 리뷰 개수, 예약자 수 등)를 파싱하고,
비동기 리뷰 API를 추가 호출하여 실제 한글 리뷰 수 및 주요 리뷰 내용을
오류 없이 수집 및 정합성 있게 SQLite DB에 적재하는 스크립트입니다.
"""

import os
import re
import time
import sqlite3
import json
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests

# 상대 경로 정의
DB_PATH = "klook/data/klook_products.db"


def init_detail_table():
    """
    상세 정보를 기록할 klook_detail_info 테이블을 초기화합니다.
    새로운 스키마 반영을 위해 기존 테이블이 존재하면 삭제 후 새로 생성합니다.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 기존 테이블 삭제 (스키마 변경 대응)
    cursor.execute("DROP TABLE IF EXISTS klook_detail_info")
    
    # 새로운 스키마로 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS klook_detail_info (
            activity_id INTEGER PRIMARY KEY,
            detail_title TEXT,
            detail_desc TEXT,
            country_name TEXT,
            city_name TEXT,
            market_price REAL,
            selling_price REAL,
            review_rating REAL,
            review_count INTEGER,
            participant_count INTEGER,
            packages_summary TEXT,
            representative_review TEXT,
            representative_review_author TEXT,
            representative_review_rating REAL,
            packages_json TEXT,
            reviews_json TEXT,
            sections_json TEXT,
            collected_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] klook_detail_info 테이블 초기화 완료 (기존 테이블 존재 시 갱신 완료)")


def get_top_links(limit=10):
    """
    klook_products 테이블에서 상위 상품들의 ID와 링크를 가져옵니다.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT vertical_id, deep_link, title FROM klook_products LIMIT ?", (limit,))
    rows = cursor.fetchall()
    
    conn.close()
    return rows


def extract_balanced_json(text):
    """
    텍스트에서 첫 '{'부터 괄호 균형이 맞는 가장 바깥쪽 JSON 객체 문자열을 추출합니다.
    """
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    count = 0
    in_string = False
    escape = False
    
    for idx in range(start_idx, len(text)):
        char = text[idx]
        
        if escape:
            escape = False
            continue
            
        if char == '\\':
            escape = True
            continue
            
        if char == '"':
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                count += 1
            elif char == '}':
                count -= 1
                if count == 0:
                    return text[start_idx:idx+1]
    return None


def fetch_reviews_via_api(activity_id, sub_category_id, headers):
    """
    Klook 비동기 리뷰 API를 호출하여 리뷰 리스트를 수집합니다.
    """
    url = "https://www.klook.com/v1/experiencesrv/activity/component_service/activity_reviews_list"
    params = {
        "activity_id": str(activity_id),
        "page": "1",
        "limit": "8",
        "star_num": "",
        "lang": "ko_KR",  # 한국어 리뷰 수집
        "sort_type": "0",
        "only_image": "false",
        "sub_category_id": str(sub_category_id) if sub_category_id else "171"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, impersonate="chrome110", timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("success"):
                res_result = res_json.get("result")
                reviews = res_result.get("item", []) if isinstance(res_result, dict) else []
                print(f"   * [리뷰 API] {len(reviews)}개의 한글 리뷰 데이터를 수집했습니다.")
                return reviews
            else:
                print(f"   * [리뷰 API] 실패 응답: {res_json.get('error', {}).get('message')}")
        else:
            print(f"   * [리뷰 API] HTTP {response.status_code} 오류 발생")
    except Exception as e:
        print(f"   * [리뷰 API] 요청 예외 발생: {e}")
        
    return []


def fetch_packages_via_api(activity_id, link, headers):
    """
    Klook 비동기 패키지 API 호출을 시도합니다.
    실패(403 등)할 경우 빈 리스트를 리턴하며 크래시 없이 넘어가도록 예외처리합니다.
    """
    url = "https://www.klook.com/v1/experiencesrv/activity/package_service/get_package_option_sources"
    params = {
        "activity_id": str(activity_id),
        "sales_channel": "customer",
        "package_option_type": "package_option"
    }
    
    # 세부 비동기 헤더 보강
    ajax_headers = headers.copy()
    ajax_headers.update({
        "x-requested-with": "XMLHttpRequest",
        "referer": link,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    })
    
    try:
        response = requests.get(url, params=params, headers=ajax_headers, impersonate="chrome110", timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("success"):
                packages = res_json.get("result", {}).get("packages") or res_json.get("result", {}).get("package_list") or []
                print(f"   * [패키지 API] {len(packages)}개의 패키지 데이터를 수집했습니다.")
                return packages
        # 403 등의 에러 발생 시 로그만 출력하고 조용히 넘김
        print(f"   * [패키지 API] 수집 제한됨 (HTTP {response.status_code} / Cloudflare 차단)")
    except Exception as e:
        print(f"   * [패키지 API] 예외 발생: {e}")
        
    return []


def parse_detail_html(html_content, vertical_id, link, headers, default_title=""):
    """
    상세페이지 HTML 및 비어있는 비동기 API들로부터 데이터를 온전하게 수집합니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    script_text = None
    for s in soup.find_all('script'):
        if s.text and 'window.__KLOOK__' in s.text:
            script_text = s.text
            break
            
    # 기본적인 Fallback 데이터 구성
    parsed_data = {
        "activity_id": vertical_id,
        "detail_title": default_title,
        "detail_desc": "",
        "country_name": "",
        "city_name": "",
        "market_price": 0.0,
        "selling_price": 0.0,
        "review_rating": 0.0,
        "review_count": 0,
        "participant_count": 0,
        "packages_summary": "",
        "representative_review": "",
        "representative_review_author": "",
        "representative_review_rating": 0.0,
        "packages_json": "[]",
        "reviews_json": "[]",
        "sections_json": "[]",
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # HTML Meta 및 og 태그를 통한 기본 Fallback 정보 수집
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        content_val = meta_desc.get('content', '')
        parsed_data["detail_desc"] = str(content_val) if content_val else ""
        
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title:
        title_val = og_title.get('content', default_title)
        parsed_data["detail_title"] = str(title_val) if title_val else default_title

    sub_category_id = 171  # 기본값
    
    # window.__KLOOK__ 변수가 존재할 경우 파싱
    if script_text:
        try:
            parts = script_text.split('window.__KLOOK__=', 1)
            if len(parts) >= 2:
                json_part = parts[1].strip()
                ext_json = extract_balanced_json(json_part)
                
                if ext_json:
                    data = json.loads(ext_json)
                    state = data.get('state', {})
                    traveller = state.get('traveller', {})
                    activity_data = traveller.get('activity', {})
                    
                    if activity_data:
                        detail = activity_data.get('activityDetail', {})
                        basic = detail.get('basic_data', {})
                        
                        if basic:
                            # 기본 텍스트 정보 수집
                            seo = basic.get('seo', {})
                            og_title_content = str(og_title.get('content')) if og_title and og_title.get('content') else None
                            parsed_data["detail_title"] = seo.get('title') or basic.get('title') or og_title_content or default_title
                            parsed_data["detail_desc"] = seo.get('description') or basic.get('intro') or parsed_data["detail_desc"]
                            parsed_data["country_name"] = basic.get('country_name', '')
                            parsed_data["city_name"] = basic.get('city_name', '')
                            parsed_data["activity_id"] = basic.get('activity_id') or vertical_id
                            
                            sub_category_id = basic.get('sub_category_id', 171)
                            
                            # 평점, 리뷰 개수 및 예약 인원 수
                            # mini_review 소스가 존재하는 경우 우선적으로 실시간 수치 적용
                            source = detail.get('source', {})
                            mini_review_data = source.get('mini_review', {}).get('data', {}) if isinstance(source.get('mini_review'), dict) else {}
                            rating_info = mini_review_data.get('rating_info') or {}
                            
                            parsed_data["review_rating"] = float(rating_info.get('avg_rating') or basic.get('review_rating', 0.0) or 0.0)
                            parsed_data["review_count"] = int(rating_info.get('review_count') or basic.get('review_count', 0) or 0)
                            parsed_data["participant_count"] = int(basic.get('product_participant_count', 0) or 0)
                            
                            # 가격 정보
                            price_obj = basic.get('price', {})
                            if price_obj:
                                try:
                                    parsed_data["market_price"] = float(price_obj.get('market_price', 0.0) or 0.0)
                                    parsed_data["selling_price"] = float(price_obj.get('selling_price', 0.0) or 0.0)
                                except ValueError:
                                    pass
                            
                        # 레이아웃 섹션 정보
                        sections = detail.get('sections', [])
                        if sections:
                            parsed_data["sections_json"] = json.dumps(sections, ensure_ascii=False)
        except Exception as e:
            print(f"   * [파싱 에러] window.__KLOOK__ 디코드 에러: {e}")

    # 4. 비동기 리뷰 API 호출
    reviews = fetch_reviews_via_api(vertical_id, sub_category_id, headers)
    if reviews:
        parsed_data["reviews_json"] = json.dumps(reviews, ensure_ascii=False)
        # 첫 번째 리뷰를 대표 리뷰로 설정
        if len(reviews) > 0 and isinstance(reviews[0], dict):
            rep_rev = reviews[0]
            parsed_data["representative_review"] = rep_rev.get('content') or rep_rev.get('translate_content') or rep_rev.get('text') or ""
            # 작성자 닉네임 설정
            parsed_data["representative_review_author"] = rep_rev.get('author', {}).get('nickname') if isinstance(rep_rev.get('author'), dict) else rep_rev.get('author') or ""
            try:
                # 100점 만점을 5점 단위 평점으로 변환 (예: 100 -> 5.0)
                raw_rating = float(rep_rev.get('rating', 0.0) or 0.0)
                parsed_data["representative_review_rating"] = round(raw_rating / 20.0, 1) if raw_rating > 5.0 else raw_rating
            except ValueError:
                pass
            
    # 5. 비동기 패키지 API 호출 (실패 시 예외처리 및 기본값 처리 완료)
    packages = fetch_packages_via_api(vertical_id, link, headers)
    if packages:
        parsed_data["packages_json"] = json.dumps(packages, ensure_ascii=False)
        pkg_names = []
        for pkg in packages:
            if isinstance(pkg, dict):
                name = pkg.get('name') or pkg.get('title')
                if name:
                    pkg_names.append(str(name))
        parsed_data["packages_summary"] = ", ".join(pkg_names)
        
    return parsed_data


def save_detail_to_db(detail_data):
    """
    파싱된 상세 정보를 klook_detail_info 테이블에 저장합니다.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO klook_detail_info (
                activity_id, detail_title, detail_desc, country_name, city_name,
                market_price, selling_price, review_rating, review_count, participant_count,
                packages_summary, representative_review, representative_review_author,
                representative_review_rating, packages_json, reviews_json, sections_json, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            detail_data["activity_id"],
            detail_data["detail_title"],
            detail_data["detail_desc"],
            detail_data["country_name"],
            detail_data["city_name"],
            detail_data["market_price"],
            detail_data["selling_price"],
            detail_data["review_rating"],
            detail_data["review_count"],
            detail_data["participant_count"],
            detail_data["packages_summary"],
            detail_data["representative_review"],
            detail_data["representative_review_author"],
            detail_data["representative_review_rating"],
            detail_data["packages_json"],
            detail_data["reviews_json"],
            detail_data["sections_json"],
            detail_data["collected_at"]
        ))
        conn.commit()
        print(f"[DB] ID {detail_data['activity_id']} 저장 완료 (리뷰 수: {detail_data['review_count']})")
    except Exception as e:
        print(f"[DB 에러] ID {detail_data['activity_id']} 저장 실패: {e}")
        
    conn.close()


def scrape_details():
    """
    상위 10개 상품의 링크에 접속해 상세 정보를 스크래핑합니다.
    """
    top_items = get_top_links(limit=10)
    print(f"[수집] DB에서 상위 {len(top_items)}개 상품 링크를 로드했습니다.")
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "referer": "https://www.klook.com/ko/"
    }
    
    for i, (vertical_id, link, title) in enumerate(top_items, 1):
        print(f"\n[상세 수집] ({i}/10) ID: {vertical_id} | 상품명: {title}")
        print(f" - URL: {link}")
        
        if not link or not link.startswith("http"):
            print(" - [경고] 유효하지 않은 상세페이지 URL입니다. 건너뜁니다.")
            continue
            
        for attempt in range(1, 4):
            try:
                response = requests.get(link, headers=headers, impersonate="chrome110", timeout=12)
                if response.status_code == 200:
                    print(f" - [성공] 페이지 다운로드 완료 (크기: {len(response.text)} 바이트)")
                    detail_data = parse_detail_html(response.text, vertical_id, link, headers, default_title=title)
                    save_detail_to_db(detail_data)
                    break
                else:
                    print(f" - [오류] HTTP 응답 코드: {response.status_code} (시도 {attempt}/3)")
            except Exception as e:
                print(f" - [에러] 상세페이지 요청 중 예외 발생: {e} (시도 {attempt}/3)")
                
            time.sleep(3)
        else:
            print(f" - [실패] ID {vertical_id} 상세페이지 수집 최종 실패")
            
        time.sleep(2.5)


def main():
    print("=== Klook 액티비티 상세정보 및 리뷰 비동기 수집 스크립트 시작 ===")
    
    # 1. 상세 테이블 초기화 (새로운 컬럼 스키마 적용)
    init_detail_table()
    
    # 2. 상세정보 수집 및 저장
    scrape_details()
    
    print("\n=== 모든 상세정보 및 리뷰 파싱 저장 완료 ===")


if __name__ == "__main__":
    main()
