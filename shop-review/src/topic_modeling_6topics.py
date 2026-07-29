"""
쇼핑몰 리뷰 데이터(shop-review.csv) 텍스트(제목 + 내용 + 제품명)에 대한 NMF 기반 6대 주제 토픽 모델링 스크립트.
- title + content + product를 공백 기준으로 병합 및 HTML/불용어 정제
- NMF 알고리즘(n_components=6)으로 6가지 주요 토픽 추출
- 토픽별 상위 30개 키워드 및 NMF 가중치 산출
- 3x2 서브플롯 막대그래프 시각화(plot15_topic_modeling_6topics.png) 생성
- Head 5 및 Tail 5 리뷰 샘플의 6대 토픽 가중치 분포 계산 및 JSON 저장
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
from sklearn.decomposition import NMF

# 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'shop-review.csv')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
REPORT_DIR = os.path.join(BASE_DIR, 'report')

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# 1. Matplotlib 한글 폰트 설정
plt.style.use('default')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드 및 NFC 정규화
df = pd.read_csv(DATA_PATH, encoding='utf-8')

def normalize_nfc(val):
    if isinstance(val, str):
        return unicodedata.normalize('NFC', val)
    return val

for col in df.columns:
    df[col] = df[col].apply(normalize_nfc)

df['title_clean'] = df['title'].fillna('')
df['content_clean'] = df['content'].fillna('')
df['product_clean'] = df['product'].fillna('미지정 상품')

# 제목, 내용, 제품을 공백으로 합친 텍스트
df['full_text_with_product'] = df['title_clean'] + ' ' + df['content_clean'] + ' ' + df['product_clean']

# 불용어 정의
STOPWORDS = set([
    '좋아요', '너무', '잘', '감사합니다', '만족합니다', '좋고', '좋네요', '좋습니다', 
    '아주', '많이', '같아요', '또', '늘', '좀', '좋은', '정말', '제품', '생각보다',
    '구매', '상품', '사용', '구매했어요', '구입', '사용하고', '쓰고', '있어요', '해서',
    '배송', '배송도', '빠르고', '저렴하게', '가격도', '추천합니다'
])

def clean_text_with_stopwords(text):
    text = re.sub(r'&lt;|&gt;|&amp;|<br\s*/?>', ' ', text)
    text = re.sub(r'[^가-힣0-9a-zA-Z\s]', ' ', text)
    words = [w for w in text.split() if w not in STOPWORDS and len(w) > 1]
    return ' '.join(words)

df['cleaned_text_prod'] = df['full_text_with_product'].apply(clean_text_with_stopwords)

# 3. TF-IDF 벡터화 및 NMF 토픽 모델링 (6개 토픽)
vectorizer = TfidfVectorizer(max_features=2500, min_df=3, token_pattern=r'(?u)\b\w+\b')
tfidf_matrix = vectorizer.fit_transform(df['cleaned_text_prod'])
feature_names = vectorizer.get_feature_names_out()

nmf_model = NMF(n_components=6, random_state=42, init='nndsvda', max_iter=500)
W_matrix = nmf_model.fit_transform(tfidf_matrix) # 문서별 토픽 가중치 (8042 x 6)
H_matrix = nmf_model.components_ # 토픽별 키워드 가중치 (6 x vocab_size)

# 토픽 이름 정의 (6개)
topic_names = {
    0: "토픽 1: 오메가3 영양제 건강 증진 및 정기 복용",
    1: "토픽 2: 물티슈 생필품 두께 및 사용 편의성",
    2: "토픽 3: 에어팟 프로 2세대 노이즈 캔슬링 및 음질",
    3: "토픽 4: 달바 선크림 피부 수분감 및 톤업 보정",
    4: "토픽 5: 상투적 충성 재구매 및 물류 배송 만족",
    5: "토픽 6: 가성비 혜택 및 선물용 브랜드 신뢰도"
}

topics_data_6 = {}

fig, axes = plt.subplots(3, 2, figsize=(18, 18))
axes = axes.flatten()
colors = ['#27ae60', '#8e44ad', '#2980b9', '#e67e22', '#16a085', '#d35400']

for topic_idx, topic in enumerate(H_matrix):
    top_indices = topic.argsort()[::-1][:30]
    top_keywords = [feature_names[i] for i in top_indices]
    top_weights = [float(topic[i]) for i in top_indices]
    
    topics_data_6[topic_idx] = {
        "name": topic_names[topic_idx],
        "keywords": list(zip(top_keywords, top_weights))
    }
    
    ax = axes[topic_idx]
    bars = ax.barh(top_keywords[::-1], top_weights[::-1], color=colors[topic_idx], edgecolor='black', alpha=0.85)
    ax.set_title(topic_names[topic_idx], fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel('NMF 가중치 점수', fontsize=10)
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    
    for bar in bars:
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, f'{bar.get_width():.2f}', 
                va='center', fontsize=8)

plt.suptitle('NMF 기반 6대 주제(Topic)별 상위 30개 키워드 및 가중치 시각화 (제목+내용+제품 포함)', fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'plot15_topic_modeling_6topics.png'), dpi=300)
plt.close()

print("Plot 15 (6-Topic NMF visualization) created successfully.")

# 문서별 가중치 정규화 (합이 1)
W_norm = W_matrix / (W_matrix.sum(axis=1, keepdims=True) + 1e-9)

head5_df = df.head(5).copy()
tail5_df = df.tail(5).copy()

head5_weights = W_norm[:5]
tail5_weights = W_norm[-5:]

sample_rows_data_6 = []

# Head 5
for idx in range(5):
    sample_rows_data_6.append({
        "type": "Head",
        "index": idx,
        "title": head5_df.iloc[idx]['title'],
        "product": head5_df.iloc[idx]['product_clean'],
        "weights": [round(float(w), 4) for w in head5_weights[idx]],
        "main_topic": int(np.argmax(head5_weights[idx]))
    })

# Tail 5
for idx in range(5):
    orig_idx = len(df) - 5 + idx
    sample_rows_data_6.append({
        "type": "Tail",
        "index": orig_idx,
        "title": tail5_df.iloc[idx]['title'],
        "product": tail5_df.iloc[idx]['product_clean'],
        "weights": [round(float(w), 4) for w in tail5_weights[idx]],
        "main_topic": int(np.argmax(tail5_weights[idx]))
    })

topic6_results_summary = {
    "topics_data": topics_data_6,
    "sample_rows": sample_rows_data_6
}

with open(os.path.join(REPORT_DIR, 'topic_modeling_6topics_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(topic6_results_summary, f, ensure_ascii=False, indent=2)

print("Topic 6 modeling analysis complete.")
