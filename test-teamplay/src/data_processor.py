"""
아이허브 스포츠 카테고리 특가 상품 데이터를 로드하고 전처리하여
Streamlit 대시보드 UI 및 EDA 분석에 연동하기 위한 데이터 프로세서 모듈입니다.
"""
import pandas as pd
import os
import re
import typing

def clean_price(price_str) -> int:
    """
    가격 문자열에서 원화 기호(₩) 및 쉼표(,) 등을 제거하고 정수형으로 변환합니다.
    
    Args:
        price_str: 가격 문자열 혹은 수치 데이터
        
    Returns:
        정수형 가격 데이터
    """
    if pd.isna(price_str):
        return 0
    if isinstance(price_str, (int, float)):
        return int(price_str)
    # 숫자만 남기고 제거
    cleaned = re.sub(r'[^\d]', '', str(price_str))
    return int(cleaned) if cleaned else 0

def extract_form_type(display_name: str) -> str:
    """
    상품명(displayName)에서 제형 키워드를 추출하여 표준화된 제형으로 반환합니다.
    
    - Gummy/구미/젤리 ➡️ 구미
    - Liquid/액상/음료 ➡️ 액상
    - Powder/파우더/분말 ➡️ 파우더
    - Capsule/Softgel/캡슐/정/Tablet ➡️ 알약
    - 나머지는 기타
    
    Args:
        display_name: 상품명
        
    Returns:
        표준화된 제형 분류 (구미, 액상, 파우더, 알약, 기타)
    """
    name_lower = display_name.lower()
    
    if any(k in name_lower for k in ['gummy', '구미', '젤리']):
        return '구미'
    elif any(k in name_lower for k in ['liquid', '액상', '음료']):
        return '액상'
    elif any(k in name_lower for k in ['powder', '파우더', '분말']):
        return '파우더'
    elif any(k in name_lower for k in ['capsule', 'softgel', '캡슐', '정', 'tablet']):
        return '알약'
    else:
        return '기타'

def map_functional_category(display_name: str) -> str:
    """
    상품명(displayName)을 기반으로 건강 기능 카테고리를 매핑합니다.
    
    - 'Joint/관절/MSM/Chondroitin' ➡️ 관절 및 연골 건강
    - 'Energy/BCAA/Vitamin B/에너지' ➡️ 에너지 대사
    - 'Protein/프로틴/단백질/Amino' ➡️ 근육 발달
    - 'Antioxidant/CoQ10/피로' ➡️ 피로 개선 및 항산화
    - 매핑되지 않으면 '미분류'로 설정
    
    Args:
        display_name: 상품명
        
    Returns:
        기능 카테고리 명칭
    """
    name_lower = display_name.lower()
    
    if any(k in name_lower for k in ['joint', '관절', 'msm', 'chondroitin']):
        return '관절 및 연골 건강'
    elif any(k in name_lower for k in ['energy', 'bcaa', 'vitamin b', '에너지']):
        return '에너지 대사'
    elif any(k in name_lower for k in ['protein', '프로틴', '단백질', 'amino']):
        return '근육 발달'
    elif any(k in name_lower for k in ['antioxidant', 'coq10', '피로']):
        return '피로 개선 및 항산화'
    else:
        return '미분류'

def load_data(csv_path: str) -> pd.DataFrame:
    """
    아이허브 특가 상품 CSV 데이터를 읽고, 가격 정제 및 제형/기능 카테고리 매핑을 전처리하여 반환합니다.
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        전처리가 완료된 pandas DataFrame
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    # 가격 정제 (할인가 및 정가)
    df['cleaned_discount_price'] = df['discountPrice'].apply(clean_price)
    if 'listPrice' in df.columns:
        df['cleaned_list_price'] = df['listPrice'].apply(clean_price)
    
    # 제형 및 기능 매핑
    df['form_type'] = df['displayName'].apply(extract_form_type)
    df['functional_category'] = df['displayName'].apply(map_functional_category)
    
    # 상세 리뷰 수집을 위한 productId 및 reviewUrl 정합성 확보 (url 컬럼을 reviewUrl로 복사)
    if 'url' in df.columns:
        df['reviewUrl'] = df['url']
    else:
        df['reviewUrl'] = ""
        
    return df

def analyze_form_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    추출된 제형별로 전체 상품 중 차지하는 비율(%)과 평균 평점을 계산하여 반환합니다.
    
    Args:
        df: 전처리된 DataFrame
        
    Returns:
        제형 트렌드 통계 DataFrame [form_type, count, avg_rating, ratio]
    """
    total_count = len(df)
    if total_count == 0:
        return pd.DataFrame(columns=['form_type', 'count', 'avg_rating', 'ratio'])
        
    form_analysis = df.groupby('form_type').agg(
        count=('productId', 'count'),
        avg_rating=('rating', 'mean')
    ).reset_index()
    
    form_analysis['ratio'] = (form_analysis['count'] / total_count) * 100
    form_analysis = form_analysis.sort_values(by='ratio', ascending=False)
    
    return form_analysis

def get_top5_by_function(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    사용자가 선택한 기능 카테고리 내에서 리뷰 수(ratingCount)가 가장 많은 TOP 5 제품을 
    Streamlit UI용 양식에 맞추어 정제하여 반환합니다.
    
    Args:
        df: 전처리된 DataFrame
        category: 선택된 기능 카테고리 (예: '관절 및 연골 건강')
        
    Returns:
        정제된 TOP 5 DataFrame [순위, 브랜드, 제품명, 가격, 평점, 리뷰링크, productId]
    """
    # 해당 기능 카테고리 필터링
    df_filtered = typing.cast(pd.DataFrame, df[df['functional_category'] == category])
    
    # 리뷰 수(ratingCount) 기준으로 정렬 후 상위 5개 추출
    df_top5: pd.DataFrame = df_filtered.sort_values(by='ratingCount', ascending=False).head(5)
    
    result_rows = []
    for rank, (_, row) in enumerate(df_top5.iterrows(), start=1):
        # UI 친화적인 가격 포맷팅 (예: 25,000원)
        formatted_price = f"{row['cleaned_discount_price']:,}원" if 'cleaned_discount_price' in row else str(row['discountPrice'])
        
        result_rows.append({
            '순위': f"{rank}위",
            '브랜드': row['brandName'],
            '제품명': row['displayName'],
            '가격': formatted_price,
            '평점': f"⭐ {row['rating']:.1f}" if isinstance(row['rating'], (int, float)) else str(row['rating']),
            '리뷰링크': row['reviewUrl'],
            'productId': row['productId']
        })
        
    return pd.DataFrame(result_rows)

if __name__ == "__main__":
    import sys
    # 윈도우 콘솔 인코딩 에러 방지
    reconfig = getattr(sys.stdout, 'reconfigure', None)
    if reconfig is not None:
        try:
            reconfig(encoding='utf-8')
        except Exception:
            pass
            
    # 데이터 프로세서 모듈 검증 테스트
    test_csv = os.path.join("test-teamplay", "data", "iherb_specials_1_3.csv")
    print("=== 데이터 프로세서 모듈 검증 시작 ===")
    try:
        data = load_data(test_csv)
        print(f"1. 데이터 로드 성공: {len(data)}행 로드됨.")
        
        trends = analyze_form_trends(data)
        print("\n2. 제형 트렌드 분석 결과:")
        print(trends.to_string(index=False))
        
        print("\n3. 기능별 TOP 5 추출 테스트:")
        test_cat = "관절 및 연골 건강"
        top5 = get_top5_by_function(data, test_cat)
        print(top5.to_string(index=False))
        
        print("\n=== 모든 검증 테스트 완료 ===")
    except Exception as e:
        print(f"검증 중 오류 발생: {e}")
