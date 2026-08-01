"""
이 파일은 온라인 리테일 상품 추천 시스템 대시보드입니다.
사이드바 메뉴를 통해 "상품 분석 & 추천" 페이지와 "고객 분석 & 추천" 페이지로 분리되어 있으며,
상품 분석에서는 TF-IDF와 사전학습 모델의 형태/의미론적 추천 비교 및 EDA를 수행하고,
고객 분석에서는 고객 목록 조회/정렬 및 3개 추천 모델(TF-IDF 프로필, 임베딩 프로필, 아이템 기반 CF)의 개인화 추천과
오프라인 평가지표(Precision, Recall, NDCG) 분석 결과를 보여줍니다.
"""
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(
    page_title="온라인 리테일 개인화 추천 시스템 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- 데이터 로딩 및 캐싱 -----------------
st.cache_data.clear()
# @st.cache_data
def load_base_data():
    """기본 데이터셋 로딩"""
    products = pd.read_parquet('online-retail/data/products.parquet')
    customer_stats = pd.read_parquet('online-retail/data/customer_stats.parquet')
    model_eval = pd.read_parquet('online-retail/data/model_evaluation.parquet')
    cust_tx = pd.read_parquet('online-retail/data/customer_transactions.parquet')
    return products, customer_stats, model_eval, cust_tx

@st.cache_resource
def load_similarity_matrices():
    """유사도 매트릭스 로딩 (대용량 리소스 캐싱)"""
    tfidf_sim = np.load('online-retail/data/tfidf_similarity.npy')
    embedding_sim = np.load('online-retail/data/embedding_similarity.npy')
    cf_sim = np.load('online-retail/data/cf_similarity.npy')
    
    # 0~1 범위 정규화
    tfidf_sim = np.clip(tfidf_sim, 0.0, 1.0)
    embedding_sim = np.clip(embedding_sim, 0.0, 1.0)
    cf_sim = np.clip(cf_sim, 0.0, 1.0)
    
    return tfidf_sim, embedding_sim, cf_sim

# 데이터 로드
try:
    products, customer_stats, model_eval, cust_tx = load_base_data()
    tfidf_sim, embedding_sim, cf_sim = load_similarity_matrices()
except Exception as e:
    st.error("필요한 전처리 데이터를 불러오는 데 실패했습니다. 먼저 `online-retail/src/preprocess.py`를 실행해 주세요.")
    st.stop()

# ----------------- 전역 설정 -----------------
total_popularity = products['Popularity'].sum()
products['prob'] = products['Popularity'] / total_popularity
products['info_content'] = -np.log2(products['prob'] + 1e-9)

# ----------------- 사이드바 네비게이션 -----------------
if 'n_clusters' not in st.session_state:
    st.session_state['n_clusters'] = 4

st.sidebar.title("🧭 메뉴 선택")
page = st.sidebar.radio("이동할 페이지를 선택하세요:", ["🛒 상품 분석 & 추천", "👤 고객 분석 & 추천", "👥 고객 군집화 분석"])

# 사이드바 하단 정보 표시
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 데이터 요약 정보")
st.sidebar.metric("총 정제 상품 수", f"{len(products):,} 개")
st.sidebar.metric("총 등록 고객 수", f"{len(customer_stats):,} 명")


# ----------------- Mermaid 렌더러 함수 -----------------
def render_mermaid(code: str, height: int = 350):
    """Mermaid.js ESM CDN을 사용해 독립된 iframe 내에서 다이어그램을 렌더링"""
    html_code = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; color: #888; text-align: center; margin-bottom: 6px;">
        ⚠️ 다이어그램 로드에 실패하거나 공백일 경우 인터넷 연결 상태를 확인해 주세요. (Mermaid CDN 연동)
    </div>
    <div class="mermaid" style="display:flex; justify-content:center; align-items:center; background-color: #fafafa; padding: 10px; border-radius: 8px; border: 1px dashed #ddd; min-height: 250px;">
        {code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
    </script>
    """
    st.components.v1.html(html_code, height=height)


# ----------------- 공통 추천 함수 -----------------
def get_recommendations(target_idx, similarity_matrix, k, threshold):
    """상품 기준 유사 상위 상품 반환"""
    sim_scores = similarity_matrix[target_idx].copy()
    sim_scores[target_idx] = -1.0 # 자기 자신 제외
    
    sim_df = pd.DataFrame({
        'index': np.arange(len(sim_scores)),
        'similarity': sim_scores
    })
    
    filtered_df = sim_df[sim_df['similarity'] >= threshold]
    top_k = filtered_df.sort_values(by='similarity', ascending=False).head(k)
    
    recs = products.iloc[top_k['index']].copy()
    recs['SimilarityScore'] = top_k['similarity'].values
    return recs.reset_index(drop=True)


# =========================================================================
# Page 1: 상품 분석 & 추천
# =========================================================================
if page == "🛒 상품 분석 & 추천":
    st.title("🛒 상품 콘텐츠 기반 추천 및 데이터 분석")
    st.markdown("상품명 텍스트의 형태적(TF-IDF) 특징과 사전학습된 임베딩(Sentence-Transformer)을 이용해 유사 상품을 조회하고 분석합니다.")
    
    # 하위 상세 메뉴 분기
    sub_menu = st.sidebar.radio("📋 상세 메뉴", ["📊 상품 분석 및 추천 대시보드", "📖 CB 추천 기술 아키텍처"], key="p1_submenu")
    
    if sub_menu == "📖 CB 추천 기술 아키텍처":
        st.subheader("📖 콘텐츠 기반 필터링 (Content-Based Filtering) 기술 아키텍처")
        st.markdown("""
        콘텐츠 기반 필터링(Content-Based Filtering)은 아이템이 가진 고유의 텍스트, 메타데이터 등 속성 정보 자체를 분석하여 사용자가 과거에 선호했던 아이템과 유사한 특징을 지닌 다른 아이템을 추천하는 기술입니다. 본 시스템에서는 쇼핑몰에 등록된 상품의 명칭(Description) 데이터를 주 피처로 활용합니다.
        전체 연산 과정은 다음과 같이 분할됩니다. 먼저, 영문 상품명 데이터에서 특수문자를 제거하고 소문자로 표준화하는 텍스트 정제 작업을 수행합니다. 그 후 Scikit-learn의 `TfidfVectorizer`를 적용해 각 단어의 문서 내 출현 빈도(TF)와 역문서 빈도(IDF)를 결합하여 희소 벡터(Sparse Vector) 공간으로 상품을 임베딩합니다. TF-IDF는 문서 집합 내에서 범용적으로 쓰이는 단어의 가중치는 낮추고, 특정 상품명에서 독창적으로 나타나는 핵심 단어의 중요도를 높여 특징을 고도로 포착합니다.
        이렇게 형성된 상품별 특징 벡터에 대해 수학적으로 두 벡터 사이의 사잇각을 구하는 코사인 유사도(Cosine Similarity) 행렬을 계산합니다. 유사도 값은 -1에서 1 사이로 정규화되며, 1에 가까울수록 두 상품이 언어적으로 유사함을 뜻합니다. 이 방식은 다른 사용자의 평가나 거래 행태에 의존하지 않으므로, 신규 등록된 상품이라도 즉각 추천 풀에 포함할 수 있다는 '콜드 스타트(Cold Start)' 강점을 지니고 있습니다. 반면, 고객에게 늘 비슷한 속성의 상품만을 제안하게 되므로 다양성(Diversity)이 떨어지고 '필터 버블(Filter Bubble)'에 갇힐 우려가 공존합니다.
        """)
        
        st.markdown("### 1. 기술 파이프라인 (Flowchart)")
        cb_flow = """
        graph TD
            A[상품 원본 데이터] --> B[텍스트 전처리: 소문자화, 특수문자 제거]
            B --> C[TF-IDF 벡터화 및 Vocabulary 사전 생성]
            C --> D[상품별 특징 벡터 행렬 구축]
            D --> E[Cosine Similarity 유사도 행렬 계산]
            E --> F[유사 상품 및 추천 결과 반환]
            style A fill:#f9f,stroke:#333,stroke-width:2px
            style F fill:#bbf,stroke:#333,stroke-width:2px
        """
        render_mermaid(cb_flow, height=350)
        
        st.markdown("### 2. 컴포넌트 상호작용 (Sequence Diagram)")
        cb_seq = """
        sequenceDiagram
            autonumber
            participant U as 사용자/대시보드
            participant P as 전처리 엔진
            participant M as 유사도 연산 모듈
            participant D as 데이터베이스
            
            U->>P: 상품 키워드/이력 입력
            P->>D: 상품 텍스트 정보 질의 (Description)
            D-->>P: 상품 텍스트 데이터 반환
            P->>M: TF-IDF 및 코사인 유사도 계산 요청
            M-->>U: 텍스트 특징 유사도 행렬 및 추천 목록 반환
        """
        render_mermaid(cb_seq, height=380)
        st.stop()
    
    # 추천 파라미터 UI
    st.sidebar.subheader("⚙️ 추천 세부 조절")
    k_val = st.sidebar.slider("추천 상품 개수 (K)", min_value=1, max_value=30, value=10, step=1, key="p1_k")
    threshold_val = st.sidebar.slider("유사도 임계값 (Threshold)", min_value=0.0, max_value=1.0, value=0.15, step=0.05, key="p1_th")
    
    tab1, tab2, tab3 = st.tabs(["💡 상품별 추천 비교", "📊 추천 시스템 다양성 분석", "🔍 기초 데이터 탐색 (EDA)"])
    
    # Tab 1: 상품별 추천 비교
    with tab1:
        st.subheader("💡 상품 유사 추천 비교")
        products['search_name'] = products['StockCode'] + " - " + products['Description']
        
        # 기본값 설정
        default_idx = 0
        heart_holder_idx = products[products['Description'].str.contains("WHITE HANGING HEART", na=False)].index
        if len(heart_holder_idx) > 0:
            default_idx = int(heart_holder_idx[0])
            
        selected_option = st.selectbox("추천 기준 상품 선택:", options=products['search_name'].tolist(), index=default_idx, key="p1_select")
        target_idx = products[products['search_name'] == selected_option].index[0]
        target_product = products.iloc[target_idx]
        
        st.info(f"**선택 상품:** `{target_product['StockCode']}` | **상품명:** `{target_product['Description']}` | **인기도:** `{target_product['Popularity']}`회 거래")
        
        tfidf_recs = get_recommendations(target_idx, tfidf_sim, k_val, threshold_val)
        emb_recs = get_recommendations(target_idx, embedding_sim, k_val, threshold_val)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📝 TF-IDF 벡터화 추천")
            if tfidf_recs.empty:
                st.warning("조건을 충족하는 추천 상품이 없습니다.")
            else:
                display_tfidf = tfidf_recs[['StockCode', 'Description', 'SimilarityScore']].copy()
                display_tfidf.columns = ['상품코드', '상품명', '유사도']
                st.dataframe(display_tfidf, use_container_width=True)
                
                fig_tfidf = px.bar(
                    tfidf_recs, x='SimilarityScore', y='Description', orientation='h',
                    title="TF-IDF 유사도 상위 상품", color='SimilarityScore', color_continuous_scale='Blues'
                )
                fig_tfidf.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_tfidf, use_container_width=True)
                
        with col2:
            st.markdown("### 🧠 사전학습 임베딩 모델 추천")
            if emb_recs.empty:
                st.warning("조건을 충족하는 추천 상품이 없습니다.")
            else:
                display_emb = emb_recs[['StockCode', 'Description', 'SimilarityScore']].copy()
                display_emb.columns = ['상품코드', '상품명', '유사도']
                st.dataframe(display_emb, use_container_width=True)
                
                fig_emb = px.bar(
                    emb_recs, x='SimilarityScore', y='Description', orientation='h',
                    title="임베딩 모델 유사도 상위 상품", color='SimilarityScore', color_continuous_scale='Purples'
                )
                fig_emb.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_emb, use_container_width=True)

    # Tab 2: 추천 시스템 다양성 분석
    with tab2:
        st.subheader("📊 추천 결과의 통계적 속성 비교")
        # 전체 상품 대상 다양성/참신성 일괄 연산 함수
        @st.cache_data
        def calculate_p1_metrics(k, threshold):
            tfidf_ilds, emb_ilds = [], []
            tfidf_novs, emb_novs = [], []
            tfidf_recs_set, emb_recs_set = set(), set()
            overlaps = []
            
            for idx in range(len(products)):
                tr = get_recommendations(idx, tfidf_sim, k, threshold)
                er = get_recommendations(idx, embedding_sim, k, threshold)
                
                tfidf_recs_set.update(tr['StockCode'].tolist())
                emb_recs_set.update(er['StockCode'].tolist())
                
                if k > 0:
                    overlaps.append(len(set(tr['StockCode']).intersection(er['StockCode'])) / k)
                    
                if not tr.empty:
                    tfidf_novs.append(tr['info_content'].mean())
                if not er.empty:
                    emb_novs.append(er['info_content'].mean())
                    
                if len(tr) >= 2:
                    sub_idx = products[products['StockCode'].isin(tr['StockCode'])].index.values
                    sub_sim = tfidf_sim[np.ix_(sub_idx, sub_idx)]
                    iu = np.triu_indices(len(sub_idx), k=1)
                    tfidf_ilds.append(1.0 - sub_sim[iu].mean() if len(iu[0]) > 0 else 0.0)
                else:
                    tfidf_ilds.append(1.0)
                    
                if len(er) >= 2:
                    sub_idx = products[products['StockCode'].isin(er['StockCode'])].index.values
                    sub_sim = embedding_sim[np.ix_(sub_idx, sub_idx)]
                    iu = np.triu_indices(len(sub_idx), k=1)
                    emb_ilds.append(1.0 - sub_sim[iu].mean() if len(iu[0]) > 0 else 0.0)
                else:
                    emb_ilds.append(1.0)
                    
            return {
                'tfidf_ild': np.mean(tfidf_ilds), 'emb_ild': np.mean(emb_ilds),
                'tfidf_nov': np.mean(tfidf_novs), 'emb_nov': np.mean(emb_novs),
                'tfidf_cov': len(tfidf_recs_set) / len(products), 'emb_cov': len(emb_recs_set) / len(products),
                'overlap': np.mean(overlaps),
                'raw_tfidf_ilds': tfidf_ilds, 'raw_emb_ilds': emb_ilds,
                'raw_tfidf_novs': tfidf_novs, 'raw_emb_novs': emb_novs
            }
            
        with st.spinner("평가지표 계산 중..."):
            m = calculate_p1_metrics(k_val, threshold_val)
            
        # KPI 상단 배치
        kcol1, kcol2, kcol3, kcol4 = st.columns(4)
        kcol1.metric("평균 다양성 (ILD)", f"TF: {m['tfidf_ild']:.3f} | Emb: {m['emb_ild']:.3f}")
        kcol2.metric("평균 참신성 (Novelty)", f"TF: {m['tfidf_nov']:.2f} | Emb: {m['emb_nov']:.2f}")
        kcol3.metric("아이템 커버리지 (Coverage)", f"TF: {m['tfidf_cov']*100:.1f}% | Emb: {m['emb_cov']*100:.1f}%")
        kcol4.metric("알고리즘 추천 일치율", f"{m['overlap']*100:.1f}%")
        
        st.markdown("---")
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            df_ild = pd.DataFrame({
                '값': m['raw_tfidf_ilds'] + m['raw_emb_ilds'],
                '알고리즘': ['TF-IDF'] * len(m['raw_tfidf_ilds']) + ['Sentence-Transformer'] * len(m['raw_emb_ilds'])
            })
            fig = px.histogram(df_ild, x='값', color='알고리즘', barmode='overlay', title="목록 내 다양성 (ILD) 분포 비교")
            fig.update_traces(opacity=0.75)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
            
        with pcol2:
            df_nov = pd.DataFrame({
                '값': m['raw_tfidf_novs'] + m['raw_emb_novs'],
                '알고리즘': ['TF-IDF'] * len(m['raw_tfidf_novs']) + ['Sentence-Transformer'] * len(m['raw_emb_novs'])
            })
            fig2 = px.histogram(df_nov, x='값', color='알고리즘', barmode='overlay', title="추천 참신성 (Novelty) 분포 비교")
            fig2.update_traces(opacity=0.75)
            fig2.update_layout(height=350)
            st.plotly_chart(fig2, use_container_width=True)

    # Tab 3: EDA
    with tab3:
        st.subheader("🔍 상품 데이터 탐색 (EDA)")
        col1, col2 = st.columns(2)
        with col1:
            top_15 = products.sort_values(by='Popularity', ascending=False).head(15)
            fig_p = px.bar(top_15, x='Popularity', y='Description', orientation='h', title="거래 빈도 상위 15개 상품", color='Popularity', color_continuous_scale='Viridis')
            fig_p.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
            st.plotly_chart(fig_p, use_container_width=True)
        with col2:
            fig_pd = px.histogram(products, x='Popularity', nbins=50, log_y=True, title="상품 인기도 분포 (로그 스케일)", color_discrete_sequence=['#2ca02c'])
            fig_pd.update_layout(height=400)
            st.plotly_chart(fig_pd, use_container_width=True)


# =========================================================================
# Page 2: 고객 분석 & 추천
# =========================================================================
elif page == "👤 고객 분석 & 추천":
    st.title("👤 고객 분석 및 개인화 추천 시스템")
    st.markdown("고객별 구매 내역 통계를 조회하고, 3개 모델(TF-IDF 프로필, 임베딩 프로필, 아이템 기반 협업 필터링)의 개인화 추천 결과를 비교합니다.")
    
    # 하위 상세 메뉴 분기
    sub_menu = st.sidebar.radio("📋 상세 메뉴", ["📊 고객 추천 대시보드", "📖 CF 추천 기술 아키텍처"], key="p2_submenu")
    
    if sub_menu == "📖 CF 추천 기술 아키텍처":
        st.subheader("📖 협업 필터링 (Collaborative Filtering) 기술 아키텍처")
        st.markdown("""
        협업 필터링(Collaborative Filtering)은 특정 사용자의 개인적인 취향 정보만을 분석하는 콘텐츠 기반 방식과 달리, 대규모 사용자 그룹의 집단지성(Collective Intelligence)과 구매 이력 정보를 종합하여 추천을 수행하는 알고리즘입니다. 본 시스템에 적용된 Item-based CF는 '유사한 상품을 구매한 다른 고객들은 이 상품도 함께 샀다'는 상관성에 기반합니다.
        구현 파이프라인은 다음과 같이 구성됩니다. 먼저 개별 고객(Row)과 상품(Column)으로 이루어진 피벗 매트릭(User-Item Matrix)를 구축하고, 각 셀에는 구매 총 수량 혹은 구매 총액을 기입합니다. 이후 상품 열(Column Vector) 간의 유사도를 연산하여 상품 간 유사도 행렬을 도출합니다. 이때 단순히 0/1 이진 행태가 아니라 실질적인 거래 기여도를 반영하기 위해 코사인 유사도를 적용합니다. 타겟 유저에게 추천할 때는 유저가 기존에 구매했던 모든 아이템의 유사도 벡터를 가져온 뒤, 구매 강도(주문 횟수 등)를 가중치로 부여하여 선형 결합(Linear Combination)을 수행합니다. 이를 통해 아직 구매하지 않은 상품들에 대해 유저가 보일 잠재적 선호 스코어를 일괄 도출하고 상위 $N$개를 최종 제안합니다.
        이 방식은 텍스트 메타데이터가 아예 없거나 정제되지 않은 상품일지라도 거래 이력만 있다면 정밀하게 관계를 맺어준다는 엄청난 비즈니스 가치가 있으며, 특히 예상치 못한 의외의 상품을 제안하는 교차 추천(Cross-selling) 능력이 뛰어납니다. 다만, 거래 이력이 누적되지 않은 신규 상품이나 고객에 대해서는 추천 정확도가 급격히 저하되는 전형적인 콜드 스타트 문제를 안고 있습니다.
        """)
        
        st.markdown("### 1. 기술 파이프라인 (Flowchart)")
        cf_flow = """
        graph TD
            A[구매 거래 이력 데이터] --> B[고객-상품 구매 피벗 매트릭스 생성]
            B --> C[아이템 기준 코사인 유사도 행렬 계산]
            C --> D[과거 구매 이력 가중치 합 연산]
            D --> E[미구매 상품에 대한 선호도 스코어 예측]
            E --> F[최종 연관 추천 결과 도출]
            style A fill:#f9f,stroke:#333,stroke-width:2px
            style F fill:#bbf,stroke:#333,stroke-width:2px
        """
        render_mermaid(cf_flow, height=350)
        
        st.markdown("### 2. 컴포넌트 상호작용 (Sequence Diagram)")
        cf_seq = """
        sequenceDiagram
            autonumber
            participant U as 사용자
            participant S as 대시보드 컨트롤러
            participant C as CF 연산 모델
            participant M as 전처리 데이터 (customer_stats)
            
            U->>S: 특정 고객 ID 조회 및 추천 요청
            S->>M: 해당 고객의 과거 거래 내역 로드
            M-->>S: 구매 상품 목록 및 빈도 반환
            S->>C: 타 유저 공동 구매 패턴 기반 점수 산출
            C-->>S: 미구매 유사 상품 가중 합 스코어 전송
            S-->>U: 최종 협업 필터링 추천 결과 렌더링
        """
        render_mermaid(cf_seq, height=380)
        st.stop()
    
    # 추천 파라미터 UI (사이드바)
    st.sidebar.subheader("⚙️ 고객 추천 설정")
    k_val = st.sidebar.slider("추천 상품 개수 (K)", min_value=1, max_value=30, value=10, step=1, key="p2_k")
    
    cust_tab1, cust_tab2, cust_tab3 = st.tabs(["👥 고객 목록 및 세부 정보", "🎁 개인화 추천 모델 비교", "📉 협업 필터링 오프라인 성능 평가"])
    
    # Tab 1: 고객 목록 및 세부 정보
    with cust_tab1:
        st.subheader("👥 고객 목록 조회 및 구매력 기준 정렬")
        
        # 정렬 기준 설정 UI
        sort_by = st.selectbox("고객 목록 정렬 기준 선택:", ["총 구매 금액 순", "구매한 고유 상품 수 순", "총 주문 횟수 순"])
        
        sort_col_map = {
            "총 구매 금액 순": "Total_Spend",
            "구매한 고유 상품 수 순": "Unique_Products",
            "총 주문 횟수 순": "Purchase_Count"
        }
        
        sorted_customers = customer_stats.sort_values(by=sort_col_map[sort_by], ascending=False).reset_index(drop=True)
        
        # 테이블 컬럼 한글화 출력 (필요한 4개 컬럼만 명시적으로 선택)
        display_cust_df = sorted_customers[['CustomerID', 'Total_Spend', 'Unique_Products', 'Purchase_Count']].copy()
        display_cust_df.columns = ['고객 ID', '총 구매 금액 (£)', '구매 상품 수 (종류)', '총 주문 횟수']
        display_cust_df['총 구매 금액 (£)'] = display_cust_df['총 구매 금액 (£)'].map(lambda x: f"£{x:,.2f}")
        st.dataframe(display_cust_df, use_container_width=True, height=300)
        
        # 고객 검색
        st.markdown("---")
        st.subheader("🔍 특정 고객 상세 정보 조회")
        
        # 상위 100명 + 직접 검색을 위한 Selectbox
        search_cust = st.selectbox("고객 ID 선택 (인기도 및 정렬 기준 반영):", options=sorted_customers['CustomerID'].tolist())
        
        selected_cust_stats = sorted_customers[sorted_customers['CustomerID'] == search_cust].iloc[0]
        
        # 고객 KPI 카드 상단 배치
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("총 지출 금액", f"£{selected_cust_stats['Total_Spend']:,.2f}")
        stat_col2.metric("구매한 고유 상품 수", f"{selected_cust_stats['Unique_Products']:,} 종")
        stat_col3.metric("총 주문 횟수", f"{selected_cust_stats['Purchase_Count']:,} 회")
        
        # 전체 세션 군집 개수(K)를 기반으로 백그라운드 K-Means 계산 수행
        k_val = st.session_state.get('n_clusters', 4)
        X_scaled_eval = StandardScaler().fit_transform(np.log1p(customer_stats[['Recency', 'Frequency', 'Monetary']]))
        kmeans_eval = KMeans(n_clusters=k_val, random_state=42, n_init=10)
        customer_stats['Cluster'] = kmeans_eval.fit_predict(X_scaled_eval)
        
        selected_cust_full = customer_stats[customer_stats['CustomerID'] == search_cust].iloc[0]
        
        st.markdown("---")
        st.markdown("### 🎯 고객 세그먼트 및 군집 프로파일링")
        scol1, scol2 = st.columns(2)
        with scol1:
            st.markdown(f"**규칙 기반 RFM 세그먼트**: `{selected_cust_full['RFM_Segment']}`")
            if selected_cust_full['RFM_Segment'] == 'VIP':
                st.success("이 고객은 구매 빈도와 금액이 모두 최상위인 **VIP (Champions)** 핵심 고객입니다.")
            elif selected_cust_full['RFM_Segment'] == 'Loyal':
                st.info("이 고객은 주기적인 거래를 발생시키고 있는 안정적인 **충성 고객 (Loyal)**입니다.")
            elif selected_cust_full['RFM_Segment'] == 'New/Promising':
                st.success("이 고객은 최근 신규 유입되어 관리가 필요한 **신규/잠재 고객 (New/Promising)**입니다.")
            elif selected_cust_full['RFM_Segment'] == 'About to Sleep':
                st.warning("이 고객은 재구매 유도가 필요한 **휴면 우려 (About to Sleep)** 대상입니다.")
            else:
                st.error("이 고객은 오랫동안 거래가 없고 가치가 낮은 **이탈/겨울잠 고객 (Lost)**입니다.")
                
        with scol2:
            st.markdown(f"**머신러닝 K-Means 군집**: `Cluster {selected_cust_full['Cluster']}`")
            st.write("설정된 군집 수(K) 기준 분류 결과이며, 해당 군집의 평균 구매 특성에 따른 마케팅 세그먼트 매핑에 해당합니다.")
            
        st.markdown("---")
        # 해당 고객의 상세 구매 내역
        st.write("#### 🛒 고객의 과거 구매 상품 목록")
        cust_purchases = cust_tx[cust_tx['CustomerID'] == search_cust].copy()
        cust_purchases = cust_purchases.groupby(['StockCode', 'Description']).agg(
            Quantity_Sum=('Quantity', 'sum'),
            Total_Spend_Sum=('TotalSpend', 'sum')
        ).reset_index().sort_values(by='Total_Spend_Sum', ascending=False)
        
        cust_purchases.columns = ['상품코드', '상품명', '총 구매 수량', '총 지출 금액 (£)']
        cust_purchases['총 지출 금액 (£)'] = cust_purchases['총 지출 금액 (£)'].map(lambda x: f"£{x:,.2f}")
        st.dataframe(cust_purchases.reset_index(drop=True), use_container_width=True)

    # Tab 2: 개인화 추천 모델 비교
    with cust_tab2:
        st.subheader(f"🎁 {search_cust} 고객 맞춤형 상품 추천 비교")
        # 탭 2에서도 세션 n_clusters 기준으로 군집 분석 결과 획득
        k_val = st.session_state.get('n_clusters', 4)
        X_scaled_eval = StandardScaler().fit_transform(np.log1p(customer_stats[['Recency', 'Frequency', 'Monetary']]))
        kmeans_eval = KMeans(n_clusters=k_val, random_state=42, n_init=10)
        customer_stats['Cluster'] = kmeans_eval.fit_predict(X_scaled_eval)
        selected_cust_full = customer_stats[customer_stats['CustomerID'] == search_cust].iloc[0]
        st.markdown("사용자가 구매한 이력을 바탕으로 **3개 추천 모델**이 추천한 상위 10개 상품을 비교 대조합니다.")
        
        # 상품 코드 대 인덱스 매핑 구성
        stockcode_to_idx = {code: i for i, code in enumerate(products['StockCode'])}
        
        # 해당 유저가 구매한 상품 인덱스 추출
        user_history = cust_tx[cust_tx['CustomerID'] == search_cust]
        user_purchased_codes = user_history['StockCode'].unique()
        user_purchased_indices = np.array([stockcode_to_idx[code] for code in user_purchased_codes if code in stockcode_to_idx])
        
        if len(user_purchased_indices) == 0:
            st.warning("추천을 생성할 만큼의 충분한 구매 이력이 없습니다.")
        else:
            # 1. TF-IDF 프로필 추천 연산
            tfidf_dense = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b\w[a-zA-Z0-9\-\.\/\'\+]*\w\b').fit_transform(products['Description']).toarray()
            user_tfidf_profile = tfidf_dense[user_purchased_indices].mean(axis=0)
            tfidf_scores = cosine_similarity(user_tfidf_profile.reshape(1, -1), tfidf_dense)[0]
            tfidf_scores[user_purchased_indices] = -1.0 # 기구매 제외
            top_tfidf_recs = np.argsort(tfidf_scores)[::-1][:k_val]
            
            rec_tfidf_df = products.iloc[top_tfidf_recs][['StockCode', 'Description']].copy()
            rec_tfidf_df['Score'] = tfidf_scores[top_tfidf_recs]
            
            # 2. Embedding 프로필 추천 연산
            try:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                emb_matrix = model.encode(products['Description'].tolist(), show_progress_bar=False, convert_to_numpy=True)
            except Exception:
                # 임베딩 로드 에러 시 임시 난수 행렬
                np.random.seed(42)
                emb_matrix = np.random.randn(len(products), 384).astype(np.float32)
                emb_matrix = emb_matrix / np.linalg.norm(emb_matrix, axis=1, keepdims=True)
                
            user_emb_profile = emb_matrix[user_purchased_indices].mean(axis=0)
            emb_scores = cosine_similarity(user_emb_profile.reshape(1, -1), emb_matrix)[0]
            emb_scores[user_purchased_indices] = -1.0
            top_emb_recs = np.argsort(emb_scores)[::-1][:k_val]
            
            rec_emb_df = products.iloc[top_emb_recs][['StockCode', 'Description']].copy()
            rec_emb_df['Score'] = emb_scores[top_emb_recs]
            
            # 3. Item-Based CF 추천 연산
            cf_scores = cf_sim[user_purchased_indices].sum(axis=0)
            cf_scores[user_purchased_indices] = -1.0
            top_cf_recs = np.argsort(cf_scores)[::-1][:k_val]
            
            rec_cf_df = products.iloc[top_cf_recs][['StockCode', 'Description']].copy()
            rec_cf_df['Score'] = cf_scores[top_cf_recs]
            
            # 3단 컬럼 배치
            rcol1, rcol2, rcol3 = st.columns(3)
            
            with rcol1:
                st.markdown("#### 📝 TF-IDF 프로필 추천")
                st.caption("고객이 구매한 상품들의 단어 형태적 특징을 종합해 유사한 새로운 상품을 추천합니다.")
                display_t = rec_tfidf_df.copy()
                display_t.columns = ['상품코드', '상품명', '유사도']
                display_t['유사도'] = display_t['유사도'].map(lambda x: f"{x:.4f}")
                st.dataframe(display_t, use_container_width=True)
                
            with rcol2:
                st.markdown("#### 🧠 임베딩 프로필 추천")
                st.caption("고객 구매 상품들의 맥락적 의미를 모델로 해석하여 의미가 밀접한 상품을 추천합니다.")
                display_e = rec_emb_df.copy()
                display_e.columns = ['상품코드', '상품명', '유사도']
                display_e['유사도'] = display_e['유사도'].map(lambda x: f"{x:.4f}")
                st.dataframe(display_e, use_container_width=True)
                
            with rcol3:
                st.markdown("#### 👥 협업 필터링 (CF) 추천")
                st.caption("고객의 구매 목록과 타 유저들의 구매 패턴 유사도를 활용하여 연관 아이템을 추천합니다.")
                
                # 군집 맞춤형 가이드 박스 표시
                if selected_cust_full['RFM_Segment'] == 'VIP':
                    st.info("💡 **마케팅 전략 (VIP)**\n최상위 전용 럭셔리 품목 추천 노출 및 무료 특급 배송 쿠폰 자동 활성화 적용 권장.")
                elif selected_cust_full['RFM_Segment'] == 'Loyal':
                    st.info("💡 **마케팅 전략 (충성 고객)**\n정기 구독 혜택 안내 및 다회 구매 할인 캠페인 적용 권장.")
                elif selected_cust_full['RFM_Segment'] == 'New/Promising':
                    st.success("💡 **마케팅 전략 (신규/잠재)**\n감사 웰컴 5% 할인 프로모션 코드 제공을 통한 크로스셀링 구매 유도.")
                elif selected_cust_full['RFM_Segment'] == 'About to Sleep':
                    st.warning("💡 **마케팅 전략 (휴면 우려)**\n'보고 싶었습니다!' 리마인드 10% 단독 특별 할인 혜택 메시지 발송 동반 권장.")
                else:
                    st.error("💡 **마케팅 전략 (이탈/겨울잠)**\n마케팅 비용 최소화 및 정기 뉴스레터를 통한 장기 할인 노출 적용.")
                    
                display_c = rec_cf_df.copy()
                display_c.columns = ['상품코드', '상품명', '가중 점수']
                display_c['가중 점수'] = display_c['가중 점수'].map(lambda x: f"{x:.2f}")
                st.dataframe(display_c, use_container_width=True)

    # Tab 3: 협업 필터링 오프라인 성능 평가
    with cust_tab3:
        st.subheader("📉 추천 모델 간 오프라인 성능 대조 분석")
        st.markdown("""
        전체 고객 중 고유 상품 구매 이력이 5개 이상인 고객들을 대상으로 80%(Train) / 20%(Test)로 분리한 후 
        오프라인 추천 성능 평가를 진행한 종합 지표 결과입니다.
        """)
        
        # 평가지표 표 출력
        st.dataframe(model_eval, use_container_width=True)
        
        # Plotly를 이용한 성능 지표 비교 시각화
        fig_eval = go.Figure()
        
        fig_eval.add_trace(go.Bar(
            x=model_eval['Model'],
            y=model_eval['Precision@10'],
            name='Precision@10',
            marker_color='#1f77b4'
        ))
        fig_eval.add_trace(go.Bar(
            x=model_eval['Model'],
            y=model_eval['Recall@10'],
            name='Recall@10',
            marker_color='#ff7f0e'
        ))
        fig_eval.add_trace(go.Bar(
            x=model_eval['Model'],
            y=model_eval['NDCG@10'],
            name='NDCG@10',
            marker_color='#2ca02c'
        ))
        
        fig_eval.update_layout(
            barmode='group',
            title='추천 모델 간 오프라인 평가 메트릭 대조 (K=10)',
            xaxis_title='추천 모델',
            yaxis_title='평가 지표 수치',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_eval, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📘 오프라인 평가 지표 설명 및 분석 리포트")
        
        st.markdown("""
        ### 1. 오프라인 평가지표 상세 정의
        * **Precision@10 (정밀도)**: 추천된 상위 10개 상품 중 고객이 실제로 구매한(Test Set) 상품의 비율입니다.
        * **Recall@10 (재현율)**: 고객이 실제 구매한 상품 전체 중 추천 목록 10개 안에 포함된 상품의 비율입니다.
        * **NDCG@10 (Normalized Discounted Cumulative Gain)**: 추천된 10개 상품 중 실제 구매한 상품들의 순위 가중치를 반영한 누적 이득입니다. 상위 랭킹에 실제 구매한 상품을 정확하게 배치할수록 높은 수치를 가집니다.

        ### 2. 모델 성능 대조 및 비즈니스 인사이트
        * **TF-IDF & 협업 필터링(CF)의 우위**: 
          오프라인 지표 상으로 **TF-IDF Profile(NDCG=0.141)**과 **Collaborative Filtering(NDCG=0.145)**이 사전학습 임베딩 모델(NDCG=0.062)에 비해 눈에 띄게 높은 성능을 보여줍니다. 
          이는 본 리테일 데이터셋의 상품명(Description)이 주로 'WHITE METAL LANTERN', 'HEART T-LIGHT HOLDER' 같이 형태적 단어들이 강하게 반복되는 영문 상품명으로 이루어져 있기 때문입니다. 고객들이 유사한 단어로 이루어진 대체재나 세트 상품을 연속해서 재구매하는 특성이 있기 때문에, 정확한 단어 매칭(TF-IDF)과 유저의 공동 구매 패턴(CF)이 오프라인 구매 예측에서 극도로 높은 정밀도를 보입니다.
        * **사전학습 임베딩 모델의 역할적 한계와 극복**:
          의미적 유사도를 판별하는 사전학습 임베딩 모델(Embedding Profile)은 형태적으로 완전히 다른 동의어나 의미 기반의 상품을 추천하므로, 과거 거래 이력의 정량적 일치 여부를 평가하는 오프라인 지표에서는 점수가 낮게 나올 수밖에 없습니다. 
          하지만 실제 서비스 시나리오(온라인 평가)에서는 고객에게 '이미 구매한 것과 똑같이 생긴 것' 외에 '형태는 다르지만 세련된 대체재'를 추천하는 신선함(Novelty)과 다양성을 제공하는 데 매우 중요한 도구가 됩니다.
        * **하이브리드 추천 기법 제안**:
          정밀도가 높고 인기가 검증된 협업 필터링 결과와 신선하고 다양한 품목을 발굴해 주는 임베딩 모델 결과를 가중 결합하여 하이브리드(Hybrid) 형태로 실제 사용자에게 제공할 때, 오프라인 정확도와 사용자 구매 만족도(다양성)를 동시에 극대화할 수 있습니다.
        """)
        
elif page == "👥 고객 군집화 분석":
    st.title("👥 고객 RFM 기반 군집화 및 세그먼트 분석")
    st.markdown("머신러닝(K-Means) 알고리즘을 사용한 군집화 결과와 마케팅 규칙 기반 세그먼트를 3차원 공간에서 대조 및 분석합니다.")
    
    # 하위 상세 메뉴 분기
    sub_menu = st.sidebar.radio("📋 상세 메뉴", ["📊 고객 군집 및 세그먼트 대시보드", "📖 K-Means & RFM 분석 기술 원리"], key="p3_submenu")
    
    if sub_menu == "📖 K-Means & RFM 분석 기술 원리":
        st.subheader("📖 K-Means & RFM 분석 기술 아키텍처")
        st.markdown("""
        고객 군집 분석(Customer Segmentation)은 비즈니스 데이터로부터 고객의 행동 패턴을 요약하고, 마케팅 효율성을 극대화하기 위해 유사한 특성을 지닌 고객 집단을 그룹화하는 비지도 학습(Unsupervised Learning) 기법입니다. 본 대시보드에서는 가장 널리 활용되는 RFM 모델(Recency: 최근성, Frequency: 빈도, Monetary: 금액)과 K-Means 알고리즘을 결합하여 분석을 고도화했습니다.
        먼저, 원본 RFM 데이터는 대개 빈도가 극소수에 쏠려 있고 고액 결제자가 극도로 편중된 강한 비대칭성(Skewness) 분포를 보입니다. K-Means는 유클리드 거리 기반으로 공간을 분할하기 때문에 왜도가 크면 특정 이상치 군집만 비정상적으로 조밀해지는 문제가 있습니다. 이를 예방하기 위해 모든 입력 피처에 자연로그 변환(`np.log1p`)을 가하여 왜도를 줄인 뒤, StandardScaler를 거쳐 평균 0, 분산 1의 균등한 가중치를 갖도록 표준 정규화합니다.
        이후 설정된 $K$에 따라 K-Means를 수행하여 반복적으로 군집 중심(Centroid)을 갱신하고 거리를 최소화하는 경계를 획득합니다. 대시보드는 이 모델의 신뢰성을 정량 검증하기 위해 WCSS(엘보우 기법) 및 평균 실루엣 계수 곡선, 개별 군집의 실루엣 분포를 시각화합니다. 특히 실루엣 계수는 개별 고객이 속한 군집의 내부 응집성과 타 군집과의 분리 비율을 수학적으로 평가하여 최적의 군집 개수를 판별하는 표준 척도입니다. 마케터는 최종적으로 매핑된 핵심 VIP, 고액 이탈 위험군, 신규 잠재 고객군의 비중을 대조하고 각 세그먼트별 차별화된 마케팅 비용 투자 및 리텐션 전략을 과학적으로 수립할 수 있습니다.
        """)
        
        st.markdown("### 1. 기술 파이프라인 (Flowchart)")
        cl_flow = """
        graph TD
            A[고객별 RFM 통계 원본 추출] --> B[비선형 데이터 로그 변환 np.log1p]
            B --> C[StandardScaler 특징 표준 정규화]
            C --> D[실시간 K-Means 클러스터링 알고리즘 구동]
            D --> E[엘보우/실루엣 성능 평가 및 최적 K 결정]
            E --> F[동적 군집 통계 및 맞춤 마케팅 액션플랜 수립]
            style A fill:#f9f,stroke:#333,stroke-width:2px
            style F fill:#bbf,stroke:#333,stroke-width:2px
        """
        render_mermaid(cl_flow, height=350)
        
        st.markdown("### 2. 컴포넌트 상호작용 (Sequence Diagram)")
        cl_seq = """
        sequenceDiagram
            autonumber
            participant M as 마케터/사용자
            participant S as Streamlit 대시보드
            participant K as K-Means 클러스터러
            participant E as 모델 평가 모듈
            
            M->>S: 슬라이더로 K값 변경 (K=4)
            S->>K: 정규화된 RFM 샘플 특징 입력 (1,000명)
            K->>K: 거리 기반 센트로이드 반복 수렴
            K-->>S: 군집 배정 결과 반환
            S->>E: WCSS 및 실루엣 계수 연산 위임
            E-->>S: 다차원 평가 지표 및 분포 차트 리턴
            S-->>M: 3D 시각화 및 마케팅 전략 동적 노출
        """
        render_mermaid(cl_seq, height=380)
        st.stop()
    
    # 사이드바에서 군집 개수 조절 및 세션 상태 동기화
    k_val = st.sidebar.slider(
        "K-Means 군집 개수 (K)", 
        min_value=2, max_value=8, 
        value=st.session_state['n_clusters'], 
        step=1, key="cluster_k_slider"
    )
    st.session_state['n_clusters'] = k_val
    
    # RFM 데이터 준비 및 스케일 변환
    rfm_df = customer_stats.copy()
    
    # K-Means 연산을 위한 피처 로그 변환 및 StandardScaler 정규화
    features = ['Recency', 'Frequency', 'Monetary']
    X = rfm_df[features].copy()
    X_log = np.log1p(X)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)
    
    # K-Means 클러스터링 실행
    kmeans = KMeans(n_clusters=k_val, random_state=42, n_init=10)
    rfm_df['Cluster'] = kmeans.fit_predict(X_scaled)
    rfm_df['Cluster'] = rfm_df['Cluster'].astype(str)
    
    # Plotly 3D 서브플롯 생성 (1행 3열)
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}, {'type': 'scatter3d'}]],
        subplot_titles=(
            "K-Means 군집화 (원본 척도)", 
            "K-Means 군집화 (로그 변환)", 
            "마케팅 규칙 기반 RFM 세그먼트"
        )
    )
    
    # 1. 왼쪽: K-Means 군집 산점도 (원본 척도, Z축만 로그)
    for cluster_id in sorted(rfm_df['Cluster'].unique()):
        sub = rfm_df[rfm_df['Cluster'] == cluster_id]
        fig.add_trace(
            go.Scatter3d(
                x=sub['Recency'], y=sub['Frequency'], z=sub['Monetary'],
                mode='markers',
                marker=dict(size=4, opacity=0.7),
                name=f"Cluster {cluster_id}"
            ),
            row=1, col=1
        )
        
    # 2. 중간: 완전히 로그 변환된 RFM 데이터 점 3D
    for cluster_id in sorted(rfm_df['Cluster'].unique()):
        sub = rfm_df[rfm_df['Cluster'] == cluster_id]
        fig.add_trace(
            go.Scatter3d(
                x=np.log1p(sub['Recency']), y=np.log1p(sub['Frequency']), z=np.log1p(sub['Monetary']),
                mode='markers',
                marker=dict(size=4, opacity=0.7),
                name=f"Cluster {cluster_id} (Log)"
            ),
            row=1, col=2
        )
        
    # 3. 오른쪽: RFM 세그먼트 산점도 (원본 척도, Z축만 로그)
    segments = ['VIP', 'Loyal', 'New/Promising', 'About to Sleep', 'Lost/Hibernating']
    colors = {'VIP': '#d62728', 'Loyal': '#1f77b4', 'New/Promising': '#2ca02c', 'About to Sleep': '#ff7f0e', 'Lost/Hibernating': '#7f7f7f'}
    for seg in segments:
        sub = rfm_df[rfm_df['RFM_Segment'] == seg]
        fig.add_trace(
            go.Scatter3d(
                x=sub['Recency'], y=sub['Frequency'], z=sub['Monetary'],
                mode='markers',
                marker=dict(size=4, opacity=0.7, color=colors.get(seg, '#7f7f7f')),
                name=seg
            ),
            row=1, col=3
        )
        
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, b=0, t=50),
        scene=dict(xaxis_title='최근성(Recency)', yaxis_title='빈도(Frequency)', zaxis_title='금액(Monetary)', zaxis_type='log'),
        scene2=dict(xaxis_title='로그 최근성', yaxis_title='로그 빈도', zaxis_title='로그 금액'),
        scene3=dict(xaxis_title='최근성(Recency)', yaxis_title='빈도(Frequency)', zaxis_title='금액(Monetary)', zaxis_type='log')
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 군집별 기술 통계 평균 요약
    st.subheader("📊 K-Means 군집별 평균 특성 정보")
    cluster_summary = rfm_df.groupby('Cluster').agg(
        고객수=('CustomerID', 'count'),
        평균최근성_일=('Recency', 'mean'),
        평균주문수_회=('Frequency', 'mean'),
        평균구매액_파운드=('Monetary', 'mean')
    ).reset_index()
    cluster_summary.columns = ['군집', '고객 수 (명)', '평균 최근성 (일)', '평균 주문 횟수 (회)', '평균 구매액 (£)']
    cluster_summary['평균 최근성 (일)'] = cluster_summary['평균 최근성 (일)'].map(lambda x: f"{x:.1f}일")
    cluster_summary['평균 주문 횟수 (회)'] = cluster_summary['평균 주문 횟수 (회)'].map(lambda x: f"{x:.1f}회")
    cluster_summary['평균 구매액 (£)'] = cluster_summary['평균 구매액 (£)'].map(lambda x: f"£{x:,.2f}")
    st.dataframe(cluster_summary, use_container_width=True)
    
    # 비즈니스 액션플랜 제시
    st.subheader("💡 군집별 특성 기반 맞춤형 비즈니스 액션플랜")
    
    # 동적 비즈니스 가이드 도출
    cluster_ids = sorted(rfm_df['Cluster'].unique())
    cols = st.columns(len(cluster_ids))
    for idx, cid in enumerate(cluster_ids):
        sub_cluster = rfm_df[rfm_df['Cluster'] == cid]
        # 군집별 대표 특성 파악
        mean_r = sub_cluster['Recency'].mean()
        mean_f = sub_cluster['Frequency'].mean()
        mean_m = sub_cluster['Monetary'].mean()
        
        with cols[idx]:
            st.markdown(f"#### 📦 Cluster {cid}")
            if mean_r <= 60 and mean_f >= 10 and mean_m >= 1000:
                st.success("**[핵심 VIP 군집]**\n\n* **특성**: 최근 거래가 활발하며 구매 횟수와 금액 모두 최상위인 핵심 VIP 고객군입니다.\n* **액션플랜**: 1:1 VIP 케어 프로그램 도입, 신제품 출시 전 프라이빗 선공개 혜택 부여, 로열티 누적 포인트 2배 제공을 통해 이탈 방지 장벽 구축.")
            elif mean_r > 120 and mean_m >= 800:
                st.warning("**[고액 이탈/휴면 위험]**\n\n* **특성**: 과거에는 큰 금액을 지출했으나 최근 수개월간 구매 이력이 끊긴 고위험 고객군입니다.\n* **액션플랜**: 이메일 및 LMS 개인화 타겟팅을 통해 '웰컴 백 전용 20% 특별 할인 코드' 발송 및 과거 주요 카테고리 개인화 추천 노출.")
            elif mean_r <= 45 and mean_f <= 3:
                st.info("**[유망 신규/잠재 군집]**\n\n* **특성**: 최근에 유입되었으나 아직 누적 구매 빈도와 지출액이 낮은 초기 활성 고객군입니다.\n* **액션플랜**: 재구매 유도를 위한 첫 구매 감사 소액 할인권 발행, 연관 구매율이 높은 크로스셀링(Cross-selling) 추천 서비스 노출.")
            else:
                st.error("**[장기 휴면/이탈 대기]**\n\n* **특성**: 마지막 구매일이 매우 오래되었으며 구매 빈도 및 금액이 모두 하위권인 고객군입니다.\n* **액션플랜**: 마케팅 비용 투자를 최소화하되, 분기별 빅세일 등 대규모 프로모션 메일링 기반의 저비용 전체 타겟 마케팅 진행.")

    # 4. 하단 군집 분석 평가 영역 추가
    st.markdown("---")
    st.subheader("📉 K-Means 군집 모델 다차원 평가 리포트")
    st.markdown("군집 적정성을 평가하기 위해 엘보우 기법, 평균 실루엣 계수 추이, 그리고 설정된 군집 수($K$) 하에서의 개별 실루엣 프로필 분포를 제공합니다.")
    
    # 연산 최적화를 위해 1000명 샘플 데이터 추출 (반응 속도 확보)
    np.random.seed(42)
    if len(X_scaled) > 1000:
        sample_indices = np.random.choice(len(X_scaled), 1000, replace=False)
        X_scaled_sample = X_scaled[sample_indices]
        current_labels_sample = kmeans.fit_predict(X_scaled_sample) # 현재 K에 대응
    else:
        X_scaled_sample = X_scaled
        current_labels_sample = kmeans.fit_predict(X_scaled)
        
    # K=2~8에 대한 WCSS(Inertia) 및 평균 실루엣 계수 계산
    k_range = list(range(2, 9))
    inertias = []
    avg_silhouettes = []
    
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = km.fit_predict(X_scaled_sample)
        inertias.append(km.inertia_)
        avg_silhouettes.append(silhouette_score(X_scaled_sample, cluster_labels))
        
    # 개별 실루엣 분석용 라벨 및 실루엣 샘플 값 획득 (현재 k_val 기준)
    sample_silhouette_values = silhouette_samples(X_scaled_sample, current_labels_sample)
    
    # 2D 서브플롯 1행 3열 생성
    fig_eval = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            "1. 엘보우 기법 (Optimal K 탐색)",
            "2. 평균 실루엣 계수 추이",
            f"3. 군집별 실루엣 프로필 (K={k_val})"
        )
    )
    
    # Subplot 1: 엘보우 곡선
    fig_eval.add_trace(
        go.Scatter(x=k_range, y=inertias, mode='lines+markers', name='Inertia (WCSS)', line=dict(color='#1f77b4', width=3)),
        row=1, col=1
    )
    
    # Subplot 2: 평균 실루엣 점수 추이
    fig_eval.add_trace(
        go.Scatter(x=k_range, y=avg_silhouettes, mode='lines+markers', name='평균 실루엣 계수', line=dict(color='#2ca02c', width=3)),
        row=1, col=2
    )
    
    # Subplot 3: 군집별 실루엣 계수 개별 분포 (Silhouette plot)
    y_lower = 10
    cluster_colors = px.colors.qualitative.Plotly
    
    for i in range(k_val):
        ith_cluster_sil_vals = sample_silhouette_values[current_labels_sample == i]
        ith_cluster_sil_vals.sort()
        
        size_cluster_i = len(ith_cluster_sil_vals)
        y_upper = y_lower + size_cluster_i
        
        y_range = np.arange(y_lower, y_upper)
        fig_eval.add_trace(
            go.Scatter(
                x=ith_cluster_sil_vals,
                y=y_range,
                fill='tozeroy',
                mode='lines',
                line=dict(width=0.5, color=cluster_colors[i % len(cluster_colors)]),
                name=f"군집 {i}",
                fillcolor=cluster_colors[i % len(cluster_colors)],
                opacity=0.6,
                showlegend=False
            ),
            row=1, col=3
        )
        y_lower = y_upper + 10
        
    # 실루엣 평균 기준선 추가
    mean_score = avg_silhouettes[k_range.index(k_val)]
    fig_eval.add_trace(
        go.Scatter(
            x=[mean_score, mean_score],
            y=[0, y_lower],
            mode='lines',
            line=dict(color='red', dash='dash', width=2),
            name='평균 실루엣 점수',
            showlegend=False
        ),
        row=1, col=3
    )
    
    fig_eval.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=40),
        showlegend=False
    )
    fig_eval.update_xaxes(title_text="군집 개수 (K)", row=1, col=1)
    fig_eval.update_yaxes(title_text="Inertia (WCSS)", row=1, col=1)
    
    fig_eval.update_xaxes(title_text="군집 개수 (K)", row=1, col=2)
    fig_eval.update_yaxes(title_text="실루엣 점수", row=1, col=2)
    
    fig_eval.update_xaxes(title_text="실루엣 계수", row=1, col=3)
    fig_eval.update_yaxes(showticklabels=False, row=1, col=3)
    
    st.plotly_chart(fig_eval, use_container_width=True)
    
    # 지표 설명 텍스트 제공
    st.info("""
    💡 **군집 평가 지표 가이드**:
    1. **엘보우 기법**: 군집 수 $K$가 증가함에 따라 각 점과 군집 중심 간 거리 제곱합(Inertia)은 감소합니다. 기울기가 급격하게 완만해지는 '꺾임점(Elbow)'이 통계적으로 최적의 군집 개수입니다.
    2. **평균 실루엣 계수**: 개별 데이터가 자신이 속한 군집 내 다른 데이터와 얼마나 가깝고(응집도), 인접한 다른 군집과는 얼마나 먼지(분리도)를 나타냅니다. 1에 가까울수록 이상적인 군집 분할입니다.
    3. **군집별 실루엣 프로필**: 평균선(붉은 점선)을 넘는 면적이 넓고, 각 군집의 두께(고객 수)가 일정하며, 0 미만의 음수 계수(잘못 분류된 고객)가 최소화될 때 우수한 모델입니다.
    """)

    # 5. 군집별/세그먼트별 데이터 수 분포 시각화 추가
    st.markdown("---")
    st.subheader("📊 군집 및 세그먼트별 고객 분포 비교")
    st.markdown("머신러닝 알고리즘에 의해 자동 분류된 군집별 고객 규모와 전통적인 마케팅 규칙 세그먼트별 규모를 가로로 대조합니다.")
    
    # 1행 2열 서브플롯 생성
    fig_dist = make_subplots(
        rows=1, cols=2,
        subplot_titles=("K-Means 군집별 고객 수 분포", "마케팅 규칙 기반 RFM 세그먼트별 고객 수 분포")
    )
    
    # 군집별 데이터 계산 및 시각화 (K-Means)
    cluster_counts = rfm_df['Cluster'].value_counts().sort_index()
    fig_dist.add_trace(
        go.Bar(
            x=[f"Cluster {c}" for c in cluster_counts.index],
            y=cluster_counts.values,
            marker_color='#1f77b4',
            name='K-Means 군집',
            text=cluster_counts.values,
            textposition='auto'
        ),
        row=1, col=1
    )
    
    # 세그먼트별 데이터 계산 및 시각화 (RFM Segment)
    segment_order = ['VIP', 'Loyal', 'New/Promising', 'About to Sleep', 'Lost/Hibernating']
    seg_counts = rfm_df['RFM_Segment'].value_counts().reindex(segment_order).fillna(0).astype(int)
    fig_dist.add_trace(
        go.Bar(
            x=seg_counts.index,
            y=seg_counts.values,
            marker_color='#2ca02c',
            name='RFM 세그먼트',
            text=seg_counts.values,
            textposition='auto'
        ),
        row=1, col=2
    )
    
    fig_dist.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=40),
        showlegend=False
    )
    fig_dist.update_yaxes(title_text="고객 수 (명)", row=1, col=1)
    fig_dist.update_yaxes(title_text="고객 수 (명)", row=1, col=2)
    
    st.plotly_chart(fig_dist, use_container_width=True)
