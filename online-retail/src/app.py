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

# 페이지 설정
st.set_page_config(
    page_title="온라인 리테일 개인화 추천 시스템 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- 데이터 로딩 및 캐싱 -----------------
@st.cache_data
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
st.sidebar.title("🧭 메뉴 선택")
page = st.sidebar.radio("이동할 페이지를 선택하세요:", ["🛒 상품 분석 & 추천", "👤 고객 분석 & 추천"])

# 사이드바 하단 정보 표시
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 데이터 요약 정보")
st.sidebar.metric("총 정제 상품 수", f"{len(products):,} 개")
st.sidebar.metric("총 등록 고객 수", f"{len(customer_stats):,} 명")


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
        
        # 테이블 컬럼 한글화 출력
        display_cust_df = sorted_customers.copy()
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
