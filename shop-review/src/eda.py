"""
쇼핑몰 리뷰 데이터(shop-review.csv)에 대한 탐색적 데이터 분석(EDA) 수행 스크립트.
- 한글 폰트(Malgun Gothic) 설정 및 NFD->NFC 한글 자소 정규화 적용 (글꼴 깨짐/엑박 방지)
- 제목(title)과 내용(content)을 공백 기준으로 병합 및 HTML/불용어 정제
- 전체 데이터 및 상품(product)별 TF-IDF 상위 30개 키워드 서브플롯 시각화
- 상품(product)별 워드클라우드(WordCloud) 2x2 서브플롯 시각화
- 13종의 시각화 그래프 생성 및 shop-review/images/ 디렉토리에 저장
"""
import os
import re
import json
import unicodedata
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

# 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'shop-review.csv')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
REPORT_DIR = os.path.join(BASE_DIR, 'report')

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# 1. Matplotlib 한글 폰트 설정 (Windows 맑은 고딕 명시 지정)
plt.style.use('default')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드 및 NFD -> NFC 자소 통합 정규화
df = pd.read_csv(DATA_PATH, encoding='utf-8')

def normalize_nfc(val):
    if isinstance(val, str):
        return unicodedata.normalize('NFC', val)
    return val

for col in df.columns:
    df[col] = df[col].apply(normalize_nfc)

print("=== DATA BASIC INFO ===")
print(f"Total Rows: {len(df)}")
print(f"Total Columns: {len(df.columns)}")
print(f"Duplicate Rows: {df.duplicated().sum()}")

# 결측치 처리 및 정제 파생변수 생성
df['title_clean'] = df['title'].fillna('')
df['content_clean'] = df['content'].fillna('')
df['product_clean'] = df['product'].fillna('미지정 상품')
df['mallName_clean'] = df['mallName'].fillna('미지정 쇼핑몰')

# 제목(title)과 내용(content)을 공백을 기준으로 합치기
df['full_text'] = df['title_clean'] + ' ' + df['content_clean']

# 수치형 파생변수
df['title_len'] = df['title_clean'].apply(len)
df['content_len'] = df['content_clean'].apply(len)
df['product_len'] = df['product_clean'].apply(len)
df['title_word_count'] = df['title_clean'].apply(lambda x: len(x.split()))
df['content_word_count'] = df['content_clean'].apply(lambda x: len(x.split()))
df['has_html_tag'] = df['content_clean'].apply(lambda x: 1 if ('<br>' in x or '&lt;' in x or '&gt;' in x) else 0)

# HTML 태그 및 일반 불용어 정제 함수
STOPWORDS = set([
    '좋아요', '너무', '잘', '감사합니다', '만족합니다', '좋고', '좋네요', '좋습니다', 
    '아주', '많이', '같아요', '또', '늘', '좀', '좋은', '정말', '제품', '생각보다',
    '구매', '상품', '사용', '구매했어요', '구입', '사용하고', '쓰고', '있어요', '해서'
])

def clean_text_with_stopwords(text):
    # HTML 태그 및 엔티티 제거
    text = re.sub(r'&lt;|&gt;|&amp;|<br\s*/?>', ' ', text)
    # 한글, 숫자, 공백만 남기기
    text = re.sub(r'[^가-힣0-9a-zA-Z\s]', ' ', text)
    # 공백 단위 분할 후 불용어 및 1글자 단어 제거
    words = [w for w in text.split() if w not in STOPWORDS and len(w) > 1]
    return ' '.join(words)

df['cleaned_full_text'] = df['full_text'].apply(clean_text_with_stopwords)

print("\n--- Generating Visualizations ---")

# 1. Plot 1: 리뷰 본문 길이 히스토그램
plt.figure(figsize=(10, 6))
n, bins, patches = plt.hist(df['content_len'], bins=50, color='#3498db', edgecolor='black', alpha=0.7)
plt.title('리뷰 본문 길이(문자 수) 분포', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('리뷰 본문 길이 (자)', fontsize=12)
plt.ylabel('리뷰 수 (건)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot1_content_len_hist.png'), dpi=300)
plt.close()

# 2. Plot 2: 상자수염 그림
plt.figure(figsize=(10, 6))
plt.boxplot([df['title_len'], df['content_len']], tick_labels=['제목 길이', '본문 길이'], patch_artist=True,
            boxprops=dict(facecolor='#2ecc71', color='black'),
            medianprops=dict(color='red', linewidth=2))
plt.yscale('log')
plt.title('제목 및 본문 길이 상자수염 그림 (로그 스케일)', fontsize=14, fontweight='bold', pad=15)
plt.ylabel('문자 수 (로그 스케일)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot2_length_boxplot.png'), dpi=300)
plt.close()

# 3. Plot 3: 주요 쇼핑몰 Top 15
top_malls = df['mallName_clean'].value_counts().head(15)
plt.figure(figsize=(10, 6))
bars = plt.barh(top_malls.index[::-1], top_malls.values[::-1], color='#e74c3c', edgecolor='black')
plt.title('주요 쇼핑몰/판매처별 리뷰 수 Top 15', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('리뷰 건수 (건)', fontsize=12)
plt.ylabel('쇼핑몰명', fontsize=12)
for bar in bars:
    plt.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, f'{int(bar.get_width()):,}건', 
             va='center', fontsize=10)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot3_top_malls.png'), dpi=300)
plt.close()

# 4. Plot 4: 주요 상품 Top 15
top_products = df['product_clean'].value_counts().head(15)
plt.figure(figsize=(10, 6))
short_prod_names = [name[:25] + '...' if len(name) > 25 else name for name in top_products.index[::-1]]
bars = plt.barh(short_prod_names, top_products.values[::-1], color='#9b59b6', edgecolor='black')
plt.title('주요 등록 상품별 리뷰 수 Top 15', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('리뷰 건수 (건)', fontsize=12)
plt.ylabel('상품명', fontsize=12)
for bar in bars:
    plt.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, f'{int(bar.get_width()):,}건', 
             va='center', fontsize=10)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot4_top_products.png'), dpi=300)
plt.close()

# 5. Plot 5: 평균 본문 길이
top10_malls_list = df['mallName_clean'].value_counts().head(10).index
mall_avg_len = df[df['mallName_clean'].isin(top10_malls_list)].groupby('mallName_clean')['content_len'].mean().sort_values(ascending=False)
plt.figure(figsize=(10, 6))
bars = plt.bar(mall_avg_len.index, mall_avg_len.values, color='#f39c12', edgecolor='black')
plt.title('상위 10개 쇼핑몰별 평균 리뷰 본문 길이', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('쇼핑몰명', fontsize=12)
plt.ylabel('평균 본문 글자 수 (자)', fontsize=12)
plt.xticks(rotation=45, ha='right')
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, f'{bar.get_height():.1f}자', 
             ha='center', fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot5_mall_avg_content_len.png'), dpi=300)
plt.close()

# 6. Plot 6: 산점도
plt.figure(figsize=(10, 6))
plt.scatter(df['title_len'], df['content_len'], alpha=0.3, color='#16a085', edgecolors='none', s=20)
plt.title('제목 길이 vs 본문 길이 산점도', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('제목 길이 (자)', fontsize=12)
plt.ylabel('본문 길이 (자)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot6_title_vs_content_scatter.png'), dpi=300)
plt.close()

# 7. Plot 7: HTML 유무 비교
html_summary = df.groupby('has_html_tag').agg(
    count=('content_len', 'count'),
    mean_len=('content_len', 'mean')
).reset_index()
html_summary['label'] = html_summary['has_html_tag'].map({0: '일반 텍스트', 1: 'HTML 태그/엔티티 포함'})

fig, ax1 = plt.subplots(figsize=(8, 6))
bars = ax1.bar(html_summary['label'], html_summary['count'], color='#34495e', alpha=0.7, width=0.4, label='리뷰 건수')
ax1.set_ylabel('리뷰 건수 (건)', color='#34495e', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#34495e')

ax2 = ax1.twinx()
lines = ax2.plot(html_summary['label'], html_summary['mean_len'], color='#e74c3c', marker='o', linewidth=3, markersize=10, label='평균 글자 수')
ax2.set_ylabel('평균 글자 수 (자)', color='#e74c3c', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#e74c3c')

plt.title('HTML 태그/엔티티 유무별 리뷰 건수 및 평균 글자 수 비교', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot7_html_tag_comparison.png'), dpi=300)
plt.close()

# 8. Plot 8: 상관계수 히트맵
num_cols = ['title_len', 'content_len', 'product_len', 'title_word_count', 'content_word_count', 'has_html_tag']
corr = df[num_cols].corr()

plt.figure(figsize=(8, 6))
im = plt.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
plt.colorbar(im)
plt.xticks(range(len(num_cols)), ['제목길이', '본문길이', '상품명길이', '제목단어수', '본문단어수', 'HTML유무'], rotation=45, ha='right')
plt.yticks(range(len(num_cols)), ['제목길이', '본문길이', '상품명길이', '제목단어수', '본문단어수', 'HTML유무'])
plt.title('수치형 파생변수 간 상관계수 히트맵', fontsize=14, fontweight='bold', pad=15)

for i in range(len(num_cols)):
    for j in range(len(num_cols)):
        text = plt.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center', color='black' if abs(corr.iloc[i, j]) < 0.6 else 'white', fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot8_correlation_heatmap.png'), dpi=300)
plt.close()

# 9. Plot 9: 전체 데이터 TF-IDF 상위 30개
vectorizer = TfidfVectorizer(max_features=3000, min_df=3, token_pattern=r'(?u)\b\w+\b')
tfidf_matrix = vectorizer.fit_transform(df['cleaned_full_text'])
feature_names = vectorizer.get_feature_names_out()
tfidf_sums = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

tfidf_df = pd.DataFrame({'keyword': feature_names, 'score': tfidf_sums}).sort_values(by='score', ascending=False)
top30_tfidf = tfidf_df.head(30)

plt.figure(figsize=(12, 8))
bars = plt.barh(top30_tfidf['keyword'][::-1], top30_tfidf['score'][::-1], color='#27ae60', edgecolor='black')
plt.title('TF-IDF 기반 리뷰 전체 텍스트 상위 30개 핵심 키워드', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('TF-IDF 합계 점수', fontsize=12)
plt.ylabel('키워드', fontsize=12)
for bar in bars:
    plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f'{bar.get_width():.1f}', 
             va='center', fontsize=9)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot9_tfidf_top30.png'), dpi=300)
plt.close()

# 10. Plot 10: 도넛 차트
def categorize_product(name):
    name_lower = name.lower()
    if '에어팟' in name_lower or 'airpods' in name_lower:
        return '에어팟 시리즈'
    elif '오메가' in name_lower:
        return '오메가3 건강식품'
    elif '물티슈' in name_lower:
        return '물티슈 생필품'
    elif '선크림' in name_lower or '달바' in name_lower:
        return '달바 선크림 뷰티'
    elif '아이폰' in name_lower or 'iphone' in name_lower:
        return '아이폰 시리즈'
    elif '맥북' in name_lower or 'macbook' in name_lower:
        return '맥북 시리즈'
    else:
        return '기타 상품'

df['product_category'] = df['product_clean'].apply(categorize_product)
cat_counts = df['product_category'].value_counts()

plt.figure(figsize=(8, 8))
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6']
plt.pie(cat_counts.values, labels=cat_counts.index, autopct='%1.1f%%', startangle=140, colors=colors, 
        wedgeprops=dict(width=0.4, edgecolor='white'))
plt.title('제품 분류별 리뷰 작성 비중 (도넛 차트)', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot10_product_category_pie.png'), dpi=300)
plt.close()

# 11. Plot 11: 글자 수 구간별 분포
bins = [0, 50, 100, 200, 500, 1000, 10000]
labels = ['50자 이하', '51~100자', '101~200자', '201~500자', '501~1000자', '1000자 초과']
df['len_group'] = pd.cut(df['content_len'], bins=bins, labels=labels, right=True)
len_group_counts = df['len_group'].value_counts().reindex(labels)

plt.figure(figsize=(10, 6))
bars = plt.bar(len_group_counts.index, len_group_counts.values, color='#8e44ad', edgecolor='black')
plt.title('리뷰 본문 글자 수 구간별 분포', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('글자 수 구간', fontsize=12)
plt.ylabel('리뷰 건수 (건)', fontsize=12)
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, f'{int(bar.get_height()):,}건', 
             ha='center', fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot11_content_length_groups.png'), dpi=300)
plt.close()

# ==========================================
# NEW 12. Plot 12: product 컬럼별 TF-IDF 상위 30개 키워드 서브플롯 막대그래프 (2x2)
# ==========================================
main_products = ['오메가3', '물티슈', '달바선크림', '에어팟프로2세대']
# product 이름 매핑 (자소 및 공백 처리)
def map_main_product(p):
    if '오메가' in p: return '오메가3'
    if '물티슈' in p: return '물티슈'
    if '선크림' in p or '달바' in p: return '달바선크림'
    if '에어팟' in p: return '에어팟프로2세대'
    return p

df['main_product'] = df['product_clean'].apply(map_main_product)

fig, axes = plt.subplots(2, 2, figsize=(18, 14))
axes = axes.flatten()

product_tfidf_results = {}

colors_list = ['#2980b9', '#27ae60', '#e67e22', '#8e44ad']

for idx, prod in enumerate(main_products):
    sub_df = df[df['main_product'] == prod]
    texts = sub_df['cleaned_full_text']
    
    vec = TfidfVectorizer(max_features=1000, min_df=2, token_pattern=r'(?u)\b\w+\b')
    mat = vec.fit_transform(texts)
    fn = vec.get_feature_names_out()
    sums = np.asarray(mat.sum(axis=0)).flatten()
    
    res_df = pd.DataFrame({'keyword': fn, 'score': sums}).sort_values(by='score', ascending=False).head(30)
    product_tfidf_results[prod] = res_df.to_dict(orient='records')
    
    ax = axes[idx]
    bars = ax.barh(res_df['keyword'][::-1], res_df['score'][::-1], color=colors_list[idx], edgecolor='black', alpha=0.85)
    ax.set_title(f'[{prod}] TF-IDF 상위 30개 핵심 키워드', fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel('TF-IDF 점수 합계', fontsize=10)
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    
    for bar in bars:
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, f'{bar.get_width():.1f}', 
                va='center', fontsize=8)

plt.suptitle('주요 상품(product)별 TF-IDF 상위 30개 키워드 비교 (2x2 서브플롯)', fontsize=16, fontweight='bold', y=0.99)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot12_tfidf_by_product.png'), dpi=300)
plt.close()

# ==========================================
# NEW 13. Plot 13: product 컬럼별 워드클라우드(WordCloud) 2x2 서브플롯
# ==========================================
font_path = 'C:/Windows/Fonts/malgun.ttf'

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

for idx, prod in enumerate(main_products):
    sub_df = df[df['main_product'] == prod]
    text_data = ' '.join(sub_df['cleaned_full_text'])
    
    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=600,
        background_color='white',
        max_words=100,
        colormap='viridis' if idx%2==0 else 'plasma',
        random_state=42
    ).generate(text_data)
    
    ax = axes[idx]
    ax.imshow(wc, interpolation='bilinear')
    ax.set_title(f'[{prod}] 리뷰 워드클라우드', fontsize=14, fontweight='bold', pad=10)
    ax.axis('off')

plt.suptitle('주요 상품(product)별 리뷰 워드클라우드 서브플롯', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot13_wordcloud_by_product.png'), dpi=300)
plt.close()

print("Plot 12 (Product TF-IDF) and Plot 13 (WordCloud Subplots) created successfully.")

# 통계 요약 데이터 저장
stats_summary = {
    "num_rows": int(len(df)),
    "num_cols": int(len(df.columns)),
    "duplicates": int(df.duplicated().sum()),
    "missing_values": df.isnull().sum().to_dict(),
    "num_stats": df[['title_len', 'content_len', 'product_len', 'title_word_count', 'content_word_count']].describe().to_dict(),
    "cat_stats_mall": df['mallName_clean'].value_counts().head(10).to_dict(),
    "cat_stats_prod": df['product_clean'].value_counts().head(10).to_dict(),
    "tfidf_top30": top30_tfidf.to_dict(orient='records'),
    "product_tfidf_results": product_tfidf_results,
    "html_summary": html_summary.to_dict(orient='records'),
    "len_group_counts": len_group_counts.to_dict(),
    "cat_counts": cat_counts.to_dict()
}

with open(os.path.join(REPORT_DIR, 'summary_data.json'), 'w', encoding='utf-8') as f:
    json.dump(stats_summary, f, ensure_ascii=False, indent=2)

print("EDA Analysis complete and summary_data.json updated with new plot data.")
