"""
교보문고 컴퓨터/IT 분야 베스트셀러 API를 호출하여 전체 페이지의 도서 정보를 수집하고 CSV 파일로 저장하는 스크립트입니다.
"""
import os
import time
import pandas as pd
import requests

def scrape_kyobobook_bestseller_all():
    url = "https://store.kyobobook.co.kr/api/gw/best/v2/best-seller/online"
    headers = {
        "host": "store.kyobobook.co.kr",
        "referer": "https://store.kyobobook.co.kr/category/domestic/33/best?page=1",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-api-gw-key": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..i35xkkCOngvXqCRx.0CqToQel6sj5d0qOS2ftoDu37jRwb0vtQwMBd1e_G1ynl7KUrTrH_qPJnygVpkc0tExt4BUX_pJ4RepB5QsxWmKLjC8tEuMELKG8SvRLEVn6ambMnSmDaJ85mLbGtHcM-zFiDBzi.3y1-RnxGHFxeLNMK2dWZoQ"
    }

    # 기본 파라미터 구성 (page는 루프 내에서 변경)
    params = {
        "per": 20,
        "saleCmdtClstCode": "33",
        "soldOutExcludeYn": "N",
        "saleCmdtDsplDvsnCode": "KOR",
        "period": "002",
        "dsplDvsnCode": "001",
        "dsplTrgtDvsnCode": "004"
    }

    parsed_books = []
    page = 1
    total_count = None

    print("교보문고 베스트셀러 데이터 전체 수집을 시작합니다.")

    while True:
        params["page"] = page
        # referer 헤더에 페이지 번호를 동적으로 업데이트
        headers["referer"] = f"https://store.kyobobook.co.kr/category/domestic/33/best?page={page}"
        
        print(f"[Page {page}] API 호출 중...", end="", flush=True)
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f" -> 실패 (상태 코드: {response.status_code})")
                break
            
            data = response.json()
            # 전체 아이템 개수 가져오기 (처음 한 번만 확인 및 출력)
            if total_count is None:
                total_count = data.get("data", {}).get("total", 0)
                print(f" (전체 대상 데이터 수: {total_count}개)")
                print(f"[Page {page}] API 호출 중...", end="", flush=True)

            bestsellers = data.get("data", {}).get("bestSeller", [])
            
            if not bestsellers:
                print(" -> 완료 (더 이상 데이터가 없습니다.)")
                break

            for item in bestsellers:
                product = item.get("product", {})
                info = product.get("productInfo", {})
                price = product.get("priceInfo", {})
                review = product.get("reviewInfo", {})

                book_data = {
                    "순위": item.get("prstRnkn"),
                    "이전순위": item.get("frmrRnkn"),
                    "상품ID": info.get("saleCmdtid"),
                    "도서명": info.get("cmdtName"),
                    "부제목": info.get("sbttName1"),
                    "저자": info.get("chrcName"),
                    "출판사": info.get("pbcmName"),
                    "출판일": info.get("rlseDate"),
                    "정가": price.get("saleCmdtPrce"),
                    "판매가": price.get("saleCmdtSapr"),
                    "평점": review.get("score"),
                    "리뷰수": review.get("count")
                }
                parsed_books.append(book_data)

            print(f" -> 성공 (현재까지 누적: {len(parsed_books)}개)")
            
            # 다음 페이지로 이동
            page += 1
            
            # API 서버 부하 방지를 위해 짧은 대기 시간 추가
            time.sleep(0.5)

        except Exception as e:
            print(f" -> 에러 발생: {e}")
            break

    # 수집 완료 후 저장
    if parsed_books:
        df = pd.DataFrame(parsed_books)
        
        # 저장 경로 폴더가 없다면 생성
        os.makedirs("kyobobook/data", exist_ok=True)
        
        output_path = "kyobobook/data/kyobobook_best_seller.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n[수집 완료] 총 {len(df)}개의 도서 데이터를 '{output_path}'에 저장하였습니다.")
    else:
        print("\n수집된 데이터가 없습니다.")

if __name__ == "__main__":
    scrape_kyobobook_bestseller_all()
