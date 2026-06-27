"""
아이허브 스포츠 카테고리 특가 상품 데이터를 분석하여 제형 트렌드 및 기능 카테고리별 매핑 분석을 수행하는 스크립트입니다.
"""
import pandas as pd
import os
import re

def clean_price(price_str):
    """
    가격 문자열에서 숫자만 추출하여 정수형으로 변환합니다.
    예: '₩26,355' -> 26355
    """
    if pd.isna(price_str):
        return 0
    if isinstance(price_str, (int, float)):
        return int(price_str)
    # 숫자만 남기고 제거
    cleaned = re.sub(r'[^\d]', '', str(price_str))
    return int(cleaned) if cleaned else 0

def extract_form_type(display_name):
    """
    displayName에서 제형 키워드를 추출하여 form_type을 반환합니다.
    - Gummy/구미/젤리 ➡️ 구미
    - Liquid/액상/음료 ➡️ 액상
    - Powder/파우더/분말 ➡️ 파우더
    - Capsule/Softgel/캡슐/정/Tablet ➡️ 알약
    - 나머지는 기타
    """
    name_lower = str(display_name).lower()
    
    # 1. 구미
    if any(k in name_lower for k in ['gummy', '구미', '젤리']):
        return '구미'
    # 2. 액상
    elif any(k in name_lower for k in ['liquid', '액상', '음료']):
        return '액상'
    # 3. 파우더
    elif any(k in name_lower for k in ['powder', '파우더', '분말']):
        return '파우더'
    # 4. 알약
    elif any(k in name_lower for k in ['capsule', 'softgel', '캡슐', '정', 'tablet']):
        return '알약'
    else:
        return '기타'

def map_functional_category(display_name):
    """
    displayName을 기반으로 기능 카테고리를 매핑합니다.
    - 'Joint/관절/MSM/Chondroitin' ➡️ 관절 및 연골 건강
    - 'Energy/BCAA/Vitamin B/에너지' ➡️ 에너지 대사
    - 'Protein/프로틴/단백질/Amino' ➡️ 근육 발달
    - 'Antioxidant/CoQ10/피로' ➡️ 피로 개선 및 항산화
    - 매핑되지 않으면 '미분류'로 설정
    """
    name_lower = str(display_name).lower()
    
    # 1. 관절 및 연골 건강
    if any(k in name_lower for k in ['joint', '관절', 'msm', 'chondroitin']):
        return '관절 및 연골 건강'
    # 2. 에너지 대사
    elif any(k in name_lower for k in ['energy', 'bcaa', 'vitamin b', '에너지']):
        return '에너지 대사'
    # 3. 근육 발달
    elif any(k in name_lower for k in ['protein', '프로틴', '단백질', 'amino']):
        return '근육 발달'
    # 4. 피로 개선 및 항산화
    elif any(k in name_lower for k in ['antioxidant', 'coq10', '피로']):
        return '피로 개선 및 항산화'
    else:
        return '미분류'

def run_analysis():
    csv_path = os.path.join("test-teamplay", "data", "iherb_specials_1_3.csv")
    df = pd.read_csv(csv_path)
    
    # 가격 정제
    df['cleaned_discount_price'] = df['discountPrice'].apply(clean_price)
    
    # 제형 및 기능 매핑
    df['form_type'] = df['displayName'].apply(extract_form_type)
    df['functional_category'] = df['displayName'].apply(map_functional_category)
    
    output_lines = []
    
    # URL 구조 확인을 위해 상위 5개 출력
    output_lines.append("=== URL 샘플 ===")
    for idx, row in df[['productId', 'url']].head(5).iterrows():
        output_lines.append(f"ID: {row['productId']}, URL: {row['url']}")
    
    # 1. 신제형 트렌드 분석
    total_count = len(df)
    form_analysis = df.groupby('form_type').agg(
        count=('productId', 'count'),
        avg_rating=('rating', 'mean')
    ).reset_index()
    form_analysis['ratio'] = (form_analysis['count'] / total_count) * 100
    form_analysis = form_analysis.sort_values(by='ratio', ascending=False)
    
    output_lines.append("\n=== 제형 트렌드 분석 결과 ===")
    output_lines.append(form_analysis.to_string(index=False))
    
    # 2. 기능 카테고리별 TOP 5 추출
    output_lines.append("\n=== 기능 카테고리별 TOP 5 제품 (리뷰 수 기준) ===")
    valid_categories = ['관절 및 연골 건강', '에너지 대사', '근육 발달', '피로 개선 및 항산화']
    df_filtered: pd.DataFrame = df[df['functional_category'].isin(valid_categories)]
    
    # 각 카테고리별로 ratingCount 기준 상위 5개
    top5_products: pd.DataFrame = df_filtered.sort_values(by=['functional_category', 'ratingCount'], ascending=[True, False])
    top5_products = top5_products.groupby('functional_category').head(5)
    
    for category in valid_categories:
        output_lines.append(f"\n[{category}]")
        cat_df = top5_products[top5_products['functional_category'] == category]
        rank = 1
        for idx, row in cat_df.iterrows():
            output_lines.append(f"{rank}위. [{row['brandName']}] {row['displayName']} | 가격: {row['discountPrice']} | 평점: {row['rating']} | 리뷰수: {row['ratingCount']} | URL: {row['url']}")
            rank += 1
            
    # 결과를 파일로 저장
    output_path = os.path.join("test-teamplay", "report", "analysis_output.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"Analysis saved to {output_path}")

if __name__ == "__main__":
    run_analysis()
