"""
NutriFit 서비스 추천 알고리즘 및 트렌드 대시보드 구축을 위한
이커머스 통합 데이터(ec_standardized_total.csv) 검증용 초안 분석 스크립트.
제형 분류, 감성 키워드 카운트, 건강 고민 매핑 및 비즈니스 가설 검증의 핵심 로직을 테스트합니다.
"""

import sys
import os
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    csv_path = 'project2/data/ec_standardized_total.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    df = pd.read_csv(csv_path, encoding='utf-8')
    print("=== 데이터 기본 정보 ===")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("Null counts:\n", df.isnull().sum())
    print("Duplicate rows:", df.duplicated().sum())
    
    # 0. 결측값 보완
    df['product_name'] = df['product_name'].fillna('')
    df['description'] = df['description'].fillna('')
    df['price'] = df['price'].fillna(0)
    df['rating'] = df['rating'].fillna(0)
    df['review_count'] = df['review_count'].fillna(0)
    
    print("\n=== 기술통계 (수치형) ===")
    print(df[['price', 'rating', 'review_count']].describe())
    
    print("\n=== 기술통계 (범주형) ===")
    print(df[['platform', 'brand']].describe(include='object'))
    
    # 파트 1: 제형 분류
    def classify_form(row):
        name = str(row['product_name']).lower()
        desc = str(row['description']).lower()
        text = name + ' ' + desc
        
        # 1. 스트립/필름
        if any(k in text for k in ['스트립', '필름', 'odf']):
            return '스트립/필름'
        # 2. 구미/젤리
        if any(k in text for k in ['구미', 'gummy', '젤리']):
            return '구미/젤리'
        # 3. 액상/샷
        if any(k in text for k in ['액상', '드롭', '앰플', '샷', 'liquid', 'drop', 'ampoule', 'shot']):
            return '액상/샷'
        # 4. 스틱
        if '스틱' in text:
            return '스틱'
        # 5. 패치
        if '패치' in text:
            return '패치'
        # 6. 파우더/분말
        if any(k in text for k in ['파우더', '분말', '가루', 'powder']):
            return '파우더/분말'
        # 7. 캡슐
        if any(k in text for k in ['캡슐', 'capsule', '소프트젤', 'softgel']):
            return '캡슐'
        # 8. 정제
        if any(k in text for k in ['정제', '타블렛', 'tablet']) or re.search(r'\d+\s*정\b|\b정\b', text):
            return '정제'
            
        return '기타(Unknown)'
        
    df['form_type'] = df.apply(classify_form, axis=1)
    
    form_counts = df['form_type'].value_counts()
    form_pct = df['form_type'].value_counts(normalize=True) * 100
    print("\n=== 제형 분류 분포 ===")
    for idx in form_counts.index:
        print(f"{idx}: {form_counts[idx]}개 ({form_pct[idx]:.2f}%)")
        
    # Unknown 데이터의 텍스트 마이닝 (TF-IDF 상위 20개 키워드 추출)
    unknown_df = df[df['form_type'] == '기타(Unknown)']
    unknown_texts = unknown_df['product_name'] + ' ' + unknown_df['description']
    
    # 영문/한글 기본 불용어 처리 (간단하게 설정)
    custom_stopwords = ['및', '제공', '도움을', '도움', '수', '있는', '있습니다', '위해', '함유', '추천', '섭취', '섭취방법', '함유되어', '건강을', '건강']
    
    if len(unknown_texts) > 0:
        vectorizer = TfidfVectorizer(max_features=100, stop_words=custom_stopwords, token_pattern=r'[ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9]+')
        tfidf_matrix = vectorizer.fit_transform(unknown_texts)
        feature_names = vectorizer.get_feature_names_out()
        tfidf_sums = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
        
        keywords_coef = pd.Series(tfidf_sums, index=feature_names).sort_values(ascending=False)
        print("\n=== Unknown 제형 상위 20개 TF-IDF 키워드 ===")
        print(keywords_coef.head(20))
        
    # 플랫폼별 제형 교차 테이블
    ct = pd.crosstab(df['platform'], df['form_type'])
    ct_pct = pd.crosstab(df['platform'], df['form_type'], normalize='index') * 100
    print("\n=== 플랫폼별 제형 교차 테이블 (개수) ===")
    print(ct)
    print("\n=== 플랫폼별 제형 교차 테이블 (백분율) ===")
    print(ct_pct.round(2))
    
    # 파트 2: 복용 편의성 & 휴대성 분석
    swallow_keywords = ['목넘김', '알약 크기', '작아서', '삼키기', '부담 없는']
    portability_keywords = ['개별포장', '휴대', '파우치', '외출', '가방', '스틱포']
    
    def count_kw(text, keywords):
        text = str(text).lower()
        return sum(text.count(kw) for kw in keywords)
        
    df['swallow_score'] = df['description'].apply(lambda x: count_kw(x, swallow_keywords))
    df['portability_score'] = df['description'].apply(lambda x: count_kw(x, portability_keywords))
    
    print("\n=== 편의성 및 휴대성 스코어 분포 ===")
    print("Swallow score > 0 count:", (df['swallow_score'] > 0).sum())
    print("Portability score > 0 count:", (df['portability_score'] > 0).sum())
    
    df['has_swallow_conv'] = df['swallow_score'] > 0
    df['has_portability_conv'] = df['portability_score'] > 0
    
    print("\n=== 삼킴 편의성 유무에 따른 평점/리뷰수 비교 ===")
    print(df.groupby('has_swallow_conv')[['rating', 'review_count']].mean())
    
    print("\n=== 휴대성 편의성 유무에 따른 평점/리뷰수 비교 ===")
    print(df.groupby('has_portability_conv')[['rating', 'review_count']].mean())
    
    print("\n=== 제형별 편의성 포함 상품의 평점 및 리뷰수 ===")
    swallow_by_form = df[df['has_swallow_conv']].groupby('form_type')[['rating', 'review_count']].agg(['mean', 'count'])
    print(swallow_by_form)
    
    # 파트 3: 8대 건강 고민 1차 라벨링 및 매핑
    concern_keywords = {
        '피로': ['비타민b', '밀크씨슬', '홍삼', '아르기닌', '활력', '피로', '에너지', '타우린', '옥타코사놀'],
        '장 건강': ['유산균', '프로바이오틱스', '프리바이오틱스', '포스트바이오틱스', '차전자피', '배변', '장건강', '유익균', '낙산균'],
        '눈 건강': ['루테인', '지아잔틴', '아스타잔틴', '비타민a', '안구', '눈건강', '시력', '차즈기'],
        '피부': ['콜라겐', '히알루론산', '엘라스틴', '글루타치온', '이너뷰티', '피부', '세라마이드', '석류'],
        '체중': ['다이어트', '가르시니아', '카테킨', '체지방', '슬리밍', '감량', '시서스', 'coleus'],
        '집중력': ['테아닌', '브레인', '포스파티딜세린', '은행잎', '기억력', '집중', '인지력', 'ginkgo'],
        '수면': ['멜라토닌', '락티움', '타트체리', '수면', '숙면', '밤', '감태', 'sleep'],
        '스트레스': ['아쉬와간다', '코르티솔', '스트레스', '긴장 완화', 'ashwagandha', 'stress']
    }
    
    def map_concerns(row):
        name = str(row['product_name']).lower()
        desc = str(row['description']).lower()
        text = name + ' ' + desc
        
        matched = []
        for concern, keywords in concern_keywords.items():
            if any(kw in text for kw in keywords):
                matched.append(concern)
        return matched if len(matched) > 0 else ['기타/미정']
        
    df['health_concern'] = df.apply(map_concerns, axis=1)
    
    df_exploded = df.explode('health_concern')
    
    print("\n=== 건강 고민별 상품 수 및 평균 가격대 ===")
    concern_summary = df_exploded.groupby('health_concern').agg(
        product_count=('product_id', 'count'),
        avg_price=('price', 'mean'),
        avg_rating=('rating', 'mean')
    ).sort_values(by='product_count', ascending=False)
    print(concern_summary)
    
    print("\n=== 건강 고민별 인기 제형 TOP 3 (리뷰 수 기준) ===")
    for concern in concern_keywords.keys():
        print(f"\n[{concern}]")
        subset = df_exploded[df_exploded['health_concern'] == concern]
        form_rank = subset.groupby('form_type').agg(
            product_count=('product_id', 'count'),
            sum_review=('review_count', 'sum'),
            avg_rating=('rating', 'mean')
        ).sort_values(by='sum_review', ascending=False).head(3)
        print(form_rank)
        
    print("\n=== 제형별 평균 가격 및 평점 ===")
    form_stats = df.groupby('form_type').agg(
        avg_price=('price', 'mean'),
        avg_rating=('rating', 'mean'),
        sum_reviews=('review_count', 'sum'),
        avg_reviews=('review_count', 'mean'),
        count=('product_id', 'count')
    ).sort_values(by='avg_price', ascending=False)
    print(form_stats)

if __name__ == '__main__':
    main()
