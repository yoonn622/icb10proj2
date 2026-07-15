"""
올리브영, 쿠팡, 아이허브의 상품 정보 CSV 데이터를 로드하여
공통된 표준 스키마 형태로 전처리하고, 병합(pd.concat)하여
최종 통합 데이터 파일로 저장하는 파이썬 스크립트입니다.
"""
import os
import glob
import re
import sys
import pandas as pd
import numpy as np

# stdout 한글 출력을 위한 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

def extract_brand_from_coupang_title(title):
    """
    쿠팡 상품명(title)에서 브랜드명을 정규식으로 추출하는 헬퍼 함수
    """
    if not isinstance(title, str):
        return np.nan
    
    # 1. 대괄호로 시작하는 패턴 검색 (예: [종근당건강] 프로메가...)
    bracket_match = re.match(r'^\[(.*?)\]', title)
    if bracket_match:
        bracket_content = bracket_match.group(1).strip()
        # 브랜드가 아닌 범용 수식어인 경우 건너뜀
        skip_words = ['정품', '추천', '단독', '특가', '기획', '무료배송', '한정', '공식', '설인아 PICK']
        if bracket_content not in skip_words and len(bracket_content) > 1:
            return bracket_content
        # 건너뛴 경우 대괄호 이후의 첫 단어 추출
        after_bracket = title[bracket_match.end():].strip()
        words = after_bracket.split()
        return words[0] if words else np.nan
    
    # 2. 대괄호가 없는 경우 띄어쓰기 기준 첫 어절을 브랜드로 판단
    words = title.split()
    return words[0] if words else np.nan

def clean_numeric_string(val):
    """
    통화 기호, 쉼표, 플러스 기호 등을 제거하여 숫자(float)로 변환하는 함수
    """
    if pd.isna(val):
        return np.nan
    
    # 문자열로 변환 후 공백 제거
    val_str = str(val).strip()
    if not val_str:
        return np.nan
        
    # 숫자, 소수점 이외의 모든 문자 제거 (단, 마이너스 부호 제외)
    # 쉼표, 원화 기호(₩), 플러스 기호(+) 등을 제거
    cleaned = re.sub(r'[^\d\.]', '', val_str)
    
    try:
        return float(cleaned) if cleaned else np.nan
    except ValueError:
        return np.nan

def process_oliveyoung():
    """
    올리브영 데이터 로드 및 정제
    """
    file_path = 'project2/data/oliveyoung.csv'
    print(f"[올리브영] 데이터 로드 중: {file_path}")
    
    df = pd.read_csv(file_path, encoding='utf-8')
    
    # 1차 매핑 (실제 컬럼 -> 사용자 정의 스키마)
    df_mapped = df.rename(columns={
        'goods_no': 'oliveyoung_id',
        'brand': 'brand_name',
        'name': 'product_name',
        'price_cur': 'price_sale',
        'score': 'rating',
        'review_count': 'review_count',
        'tags': 'product_desc'
    })
    
    # 정제 처리
    df_mapped['price_sale'] = df_mapped['price_sale'].apply(clean_numeric_string)
    df_mapped['rating'] = df_mapped['rating'].apply(clean_numeric_string)
    df_mapped['review_count'] = df_mapped['review_count'].apply(clean_numeric_string)
    
    # 최종 표준 스키마 형태로 가공
    df_standard = pd.DataFrame()
    df_standard['platform'] = ['oliveyoung'] * len(df_mapped)
    df_standard['product_id'] = df_mapped['oliveyoung_id'].astype(str)
    df_standard['brand'] = df_mapped['brand_name']
    df_standard['product_name'] = df_mapped['product_name']
    df_standard['price'] = df_mapped['price_sale']
    df_standard['rating'] = df_mapped['rating']
    df_standard['review_count'] = df_mapped['review_count']
    df_standard['description'] = df_mapped['product_desc']
    
    return df_standard

def process_iherb():
    """
    아이허브 데이터 로드 및 정제
    """
    file_path = 'project2/data/Herb_supplements.csv'
    print(f"[아이허브] 데이터 로드 중: {file_path}")
    
    df = pd.read_csv(file_path, encoding='utf-8')
    
    # 1차 매핑 (실제 컬럼 -> 사용자 정의 스키마)
    df_mapped = df.rename(columns={
        'productId': 'iherb_sku',
        'brandName': 'brand_name',
        'displayName': 'item_name',
        'discountPrice': 'price_krw',
        'rating': 'rating_num',
        'ratingCount': 'total_reviews'
    })
    
    # 정제 처리
    df_mapped['price_krw'] = df_mapped['price_krw'].apply(clean_numeric_string)
    df_mapped['rating_num'] = df_mapped['rating_num'].apply(clean_numeric_string)
    df_mapped['total_reviews'] = df_mapped['total_reviews'].apply(clean_numeric_string)
    
    # 최종 표준 스키마 형태로 가공
    df_standard = pd.DataFrame()
    df_standard['platform'] = ['iherb'] * len(df_mapped)
    df_standard['product_id'] = df_mapped['iherb_sku'].astype(str)
    df_standard['brand'] = df_mapped['brand_name']
    df_standard['product_name'] = df_mapped['item_name']
    df_standard['price'] = df_mapped['price_krw']
    df_standard['rating'] = df_mapped['rating_num']
    df_standard['review_count'] = df_mapped['total_reviews']
    # description 컬럼이 없으므로 packageQuantity 와 productForm을 결합하여 가공
    df_standard['description'] = df_mapped.apply(
        lambda r: f"수량: {r['packageQuantity']} | 제형: {r['productForm']}" 
        if pd.notna(r['packageQuantity']) and pd.notna(r['productForm']) else np.nan, axis=1
    )
    
    return df_standard

def process_coupang():
    """
    쿠팡 데이터 로드 및 정제
    """
    dir_path = 'project2/data/coupang_data'
    print(f"[쿠팡] 디렉토리 내 CSV 파일 수집 중: {dir_path}")
    
    csv_files = glob.glob(os.path.join(dir_path, '*.csv'))
    
    df_list = []
    for file in csv_files:
        df_list.append(pd.read_csv(file, encoding='utf-8'))
        
    df_all = pd.concat(df_list, ignore_index=True)
    
    # 중복 상품 제거 (product_id 기준)
    print(f"[쿠팡] 중복 제거 전 행 수: {len(df_all)}")
    df_all = df_all.drop_duplicates(subset=['product_id'])
    print(f"[쿠팡] 중복 제거 후 행 수: {len(df_all)}")
    
    # 1차 매핑 (실제 컬럼 -> 사용자 정의 스키마)
    df_mapped = df_all.rename(columns={
        'product_id': 'coupang_code',
        'product_name': 'title',
        'price': 'price',
        'rating': 'star_score',
        'review_count': 'review_total'
    })
    
    # 브랜드명 추출 정규식 알고리즘 적용
    df_mapped['brand'] = df_mapped['title'].apply(extract_brand_from_coupang_title)
    df_mapped['contents'] = np.nan
    
    # 정제 처리
    df_mapped['price'] = df_mapped['price'].apply(clean_numeric_string)
    df_mapped['star_score'] = df_mapped['star_score'].apply(clean_numeric_string)
    df_mapped['review_total'] = df_mapped['review_total'].apply(clean_numeric_string)
    
    # 최종 표준 스키마 형태로 가공
    df_standard = pd.DataFrame()
    df_standard['platform'] = ['coupang'] * len(df_mapped)
    df_standard['product_id'] = df_mapped['coupang_code'].astype(str)
    df_standard['brand'] = df_mapped['brand']
    df_standard['product_name'] = df_mapped['title']
    df_standard['price'] = df_mapped['price']
    df_standard['rating'] = df_mapped['star_score']
    df_standard['review_count'] = df_mapped['review_total']
    df_standard['description'] = df_mapped['contents']
    
    return df_standard

def main():
    print("=== 쇼핑몰 데이터 표준화 통합 파이프라인 시작 ===")
    
    # 각 플랫폼 데이터 정제 및 통합 포맷 변환
    df_oy = process_oliveyoung()
    df_ih = process_iherb()
    df_cp = process_coupang()
    
    # 데이터 병합 (pd.concat)
    print("\n[병합] 3사 데이터프레임 병합 시작...")
    df_total = pd.concat([df_oy, df_cp, df_ih], ignore_index=True)
    
    # 결과 검증
    print("\n" + "="*50)
    print("=== [결과 검증] 통합 데이터프레임 정보 (info) ===")
    print("="*50)
    df_total.info()
    print("\n" + "="*50)
    print("=== [결과 검증] 플랫폼별 데이터 수 (value_counts) ===")
    print("="*50)
    print(df_total['platform'].value_counts(dropna=False))
    print("="*50 + "\n")
    
    # 결과 저장
    out_dir = 'project2/data'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'ec_standardized_total.csv')
    
    print(f"[저장] 최종 통합 파일 저장 중: {out_path}")
    df_total.to_csv(out_path, encoding='utf-8-sig', index=False)
    print("[저장] 완료!")

if __name__ == '__main__':
    main()
