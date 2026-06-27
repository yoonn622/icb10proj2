"""
YES24 베스트셀러 도서 데이터를 대상으로 탐색적 데이터 분석(EDA)을 수행하는 스크립트입니다.
수집된 CSV 파일의 데이터를 불러와 기초 통계를 계산하고, 시각화 차트 11종을 생성하여 저장합니다.
또한, 도서명 텍스트 데이터를 TF-IDF 기법으로 분석하여 핵심 키워드 30개를 추출합니다.
"""
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer

# matplotlib 스타일 설정 (Seaborn은 배제하고 기본 스타일 유지)
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True

def run_eda():
    csv_path = os.path.join("yes24", "data", "yes24_bestsellers.csv")
    if not os.path.exists(csv_path):
        print(f"데이터 파일이 존재하지 않습니다: {csv_path}")
        return

    # 데이터 로드
    df = pd.read_csv(csv_path)
    
    # 이미지 저장 경로 설정
    img_dir = os.path.join("yes24", "images")
    os.makedirs(img_dir, exist_ok=True)
    
    print("=== [1] 기본 데이터 정보 ===")
    print(f"총 행 수: {df.shape[0]}")
    print(f"총 열 수: {df.shape[1]}")
    print("\n--- df.info() 결과 ---")
    df.info()
    
    # 중복 행 검사
    duplicates = df.duplicated().sum()
    print(f"\n중복된 행의 수: {duplicates}")
    
    print("\n=== [2] 수치형 변수 기술 통계 ===")
    num_cols = ["정가", "판매가", "판매지수", "평점", "리뷰수"]
    print(df[num_cols].describe())
    
    print("\n=== [3] 범주형 변수 기술 통계 ===")
    cat_cols = ["카테고리", "저자", "출판사", "출판일"]
    for col in cat_cols:
        print(f"\n--- {col} 빈도수 (상위 10개) ---")
        print(df[col].value_counts().head(10))

    # --- 시각화 생성 ---
    
    # 1. 정가 분포 (Histogram)
    plt.figure(figsize=(10, 6))
    plt.hist(df["정가"], bins=20, color="skyblue", edgecolor="black")
    plt.title("도서 정가 분포")
    plt.xlabel("정가 (원)")
    plt.ylabel("도서 수")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot1_price_hist.png"))
    plt.close()
    
    # 2. 판매가 분포 (Boxplot)
    plt.figure(figsize=(10, 6))
    plt.boxplot(df["판매가"], vert=False, patch_artist=True, 
                boxprops=dict(facecolor="lightgreen", color="black"),
                medianprops=dict(color="red"))
    plt.title("도서 판매가 상자 그림 (Boxplot)")
    plt.xlabel("판매가 (원)")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot2_sale_price_box.png"))
    plt.close()
    
    # 3. 평점 분포 (Histogram)
    plt.figure(figsize=(10, 6))
    plt.hist(df["평점"], bins=15, color="orange", edgecolor="black")
    plt.title("도서 평점 분포")
    plt.xlabel("평점")
    plt.ylabel("도서 수")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot3_rating_hist.png"))
    plt.close()
    
    # 4. 리뷰수 분포 (Boxplot)
    plt.figure(figsize=(10, 6))
    plt.boxplot(df["리뷰수"], vert=False, patch_artist=True,
                boxprops=dict(facecolor="lightcoral", color="black"),
                medianprops=dict(color="blue"))
    plt.title("도서 리뷰수 상자 그림 (Boxplot)")
    plt.xlabel("리뷰수 (건)")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot4_review_box.png"))
    plt.close()
    
    # 5. 판매지수 분포 (Histogram)
    plt.figure(figsize=(10, 6))
    plt.hist(df["판매지수"], bins=20, color="plum", edgecolor="black")
    plt.title("도서 판매지수 분포")
    plt.xlabel("판매지수")
    plt.ylabel("도서 수")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot5_sale_index_hist.png"))
    plt.close()
    
    # 6. 카테고리별 도서 수 (Barplot)
    plt.figure(figsize=(10, 6))
    cat_counts = df["카테고리"].value_counts()
    plt.bar(cat_counts.index, cat_counts.values, color="teal", edgecolor="black")
    plt.title("카테고리별 도서 분포")
    plt.xlabel("카테고리")
    plt.ylabel("도서 수")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot6_category_count.png"))
    plt.close()
    
    # 7. 출판사별 도서 수 (Barplot - 상위 30개)
    plt.figure(figsize=(12, 8))
    pub_counts = df["출판사"].value_counts().head(30)
    plt.bar(pub_counts.index, pub_counts.values, color="coral", edgecolor="black")
    plt.title("출판사별 도서 빈도 (상위 30개)")
    plt.xlabel("출판사")
    plt.ylabel("도서 수")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot7_publisher_count.png"))
    plt.close()
    
    # 8. 정가 vs 판매가 산점도 (Scatter plot)
    plt.figure(figsize=(10, 6))
    plt.scatter(df["정가"], df["판매가"], alpha=0.6, color="blue", edgecolor="k")
    # 대각선 (할인율 비교용) 기준선 추가
    min_val = min(df["정가"].min(), df["판매가"].min())
    max_val = max(df["정가"].max(), df["판매가"].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label="정가=판매가 기준선")
    plt.title("도서 정가 대비 판매가 산점도")
    plt.xlabel("정가 (원)")
    plt.ylabel("판매가 (원)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot8_price_scatter.png"))
    plt.close()
    
    # 9. 판매지수 vs 리뷰수 산점도 (Scatter plot)
    plt.figure(figsize=(10, 6))
    plt.scatter(df["판매지수"], df["리뷰수"], alpha=0.6, color="darkgreen", edgecolor="k")
    plt.title("판매지수 대비 리뷰수 산점도")
    plt.xlabel("판매지수")
    plt.ylabel("리뷰수 (건)")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot9_sales_reviews_scatter.png"))
    plt.close()
    
    # 10. 상관관계 히트맵 (Correlation Heatmap)
    plt.figure(figsize=(10, 8))
    corr = df[num_cols].corr()
    
    # 수동 히트맵 그리기 (Seaborn 차단 대응)
    im = plt.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(im)
    
    # 축 라벨 설정
    plt.xticks(range(len(num_cols)), num_cols, rotation=45)
    plt.yticks(range(len(num_cols)), num_cols)
    
    # 셀 내의 상관계수 값 표시
    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}",
                     ha="center", va="center", color="black" if abs(corr.iloc[i, j]) < 0.7 else "white")
            
    plt.title("수치형 변수 간 상관계수 히트맵")
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, "plot10_correlation_heatmap.png"))
    plt.close()
    
    # 11. 도서명 텍스트 TF-IDF 상위 30개 키워드
    print("\n=== [4] TF-IDF 기반 도서명 핵심 키워드 추출 (상위 30개) ===")
    # 특수문자 제거 및 텍스트 정제
    cleaned_titles = df["도서명"].apply(lambda x: re.sub(r"[^\w\s]", " ", str(x)))
    
    # 한글 형태소 분석기를 사용하지 않고 띄어쓰기 기준으로 토큰화하는 TF-IDF vectorizer 생성
    # 최소 문서 빈도 2회 이상, 최대 문서 빈도 90% 이하인 단어로 필터링
    tfidf = TfidfVectorizer(max_df=0.90, min_df=2, token_pattern=r"(?u)\b\w+\b")
    try:
        tfidf_matrix = tfidf.fit_transform(cleaned_titles)
        feature_names = tfidf.get_feature_names_out()
        
        # 전체 도서명에서의 가중치 합계 계산
        weights = tfidf_matrix.sum(axis=0).A1
        tfidf_df = pd.DataFrame({"단어": feature_names, "가중치": weights})
        top_30_keywords = tfidf_df.sort_values(by="가중치", ascending=False).head(30)
        
        print(top_30_keywords.to_string(index=False))
        
        # 키워드 빈도 시각화
        plt.figure(figsize=(12, 8))
        plt.barh(top_30_keywords["단어"][::-1], top_30_keywords["가중치"][::-1], color="darkviolet", edgecolor="black")
        plt.title("도서명 TF-IDF 기반 핵심 키워드 Top 30")
        plt.xlabel("TF-IDF 가중치 합계")
        plt.ylabel("핵심 키워드")
        plt.tight_layout()
        plt.savefig(os.path.join(img_dir, "plot11_tfidf_keywords.png"))
        plt.close()
        
    except Exception as e:
        print(f"TF-IDF 분석 중 오류 발생: {e}")

if __name__ == "__main__":
    run_eda()
