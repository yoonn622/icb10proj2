"""
KLUE YNAT 뉴스 제목 데이터셋(ynat_3000.csv)을 탐색적으로 분석(EDA)하고
TF-IDF, LSA(차원축소), K-Means(군집화) 기법을 활용한 텍스트 분석 대시보드를 Streamlit으로 제공하는 파일입니다.

주요 기능:
- 기본 EDA: 뉴스 카테고리 분포, 텍스트 길이 및 단어 수 통계, 상관관계 등 Plotly 시각화.
- 텍스트 분석: TF-IDF 벡터화, 7차원 TruncatedSVD 차원 축소, 7개 KMeans 군집 생성 및 PCA 2D 군집 공간 시각화.
- 키워드 분석: 군집 및 LSA 토픽별 상위/하위 50개 단어 중요도 분석 및 시각화.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
from plotly.subplots import make_subplots

# 페이지 기본 설정
st.set_page_config(
    page_title="KLUE YNAT EDA & 텍스트 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일 적용 (프리미엄 다크/화이트 모던 테마 느낌을 위한 마이크로 인터랙션과 깔끔한 레이아웃)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #1E3A8A;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 500;
        color: #4B5563;
    }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    .report-title {
        font-size: 32px;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 5px;
    }
    .report-subtitle {
        font-size: 16px;
        color: #6B7280;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. 데이터 로드 및 전처리 캐싱
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    df = df.dropna(subset=['title'])
    
    # 텍스트 길이 및 단어 수 변수 추가
    df['char_count'] = df['title'].str.len()
    df['word_count'] = df['title'].str.split().str.len()
    return df

# 2. 한국어 형태소 분석용 간단 토크나이저 (조사 제거 등)
# 윈도우 환경에서 외부 형태소 분석기 없이 안정적으로 구동하기 위한 가벼운 규칙 기반 토크나이저
KOREAN_JOSA = re.compile(
    r'(은|는|이|가|을|를|의|에|로|와|과|으로|에서|하고|듯|뿐|만|도|조차|마저|부터|까지|이다|합니다|했다|하는|있습니다|있다|했다가|했다는|했다며|했다가)$'
)

def simple_korean_tokenizer(text):
    # 한글, 영문, 숫자 패턴만 추출
    tokens = re.findall(r'\b\w+\b', text)
    cleaned_tokens = []
    for token in tokens:
        if len(token) <= 1:
            continue
        # 조사 및 어미 제거 규칙 적용
        cleaned = KOREAN_JOSA.sub('', token)
        if len(cleaned) > 1:
            cleaned_tokens.append(cleaned)
        else:
            cleaned_tokens.append(token)
    return cleaned_tokens

# 3. TF-IDF 및 분석 캐싱
@st.cache_resource
def run_text_analysis(titles):
    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer(
        tokenizer=simple_korean_tokenizer,
        max_df=0.95,
        min_df=2,
        max_features=5000
    )
    tfidf_matrix = vectorizer.fit_transform(titles)
    
    # TruncatedSVD (차원축소 7개)
    svd = TruncatedSVD(n_components=7, random_state=42)
    svd_matrix = svd.fit_transform(tfidf_matrix)
    
    # KMeans Clustering (군집 7개)
    kmeans = KMeans(n_clusters=7, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(svd_matrix)
    
    # 2D PCA 추가 (군집 시각화용)
    pca_2d = PCA(n_components=2, random_state=42)
    coords_2d = pca_2d.fit_transform(svd_matrix)
    
    return vectorizer, tfidf_matrix, svd, svd_matrix, kmeans, cluster_labels, coords_2d

# 메인 타이틀 구성
st.markdown('<div class="report-title">KLUE YNAT 뉴스 제목 EDA 및 텍스트 분석 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="report-subtitle">ynat_3000 데이터셋 기반 기본 EDA와 7차원/7군집화 텍스트 심화 분석</div>', unsafe_allow_html=True)

# 데이터 경로 정의
data_path = "klue/data/ynat_3000.csv"
df = load_data(data_path)

if df.empty:
    st.error(f"데이터 파일을 찾을 수 없습니다: {data_path}")
else:
    # 사이드바 메뉴 구성
    st.sidebar.header("📋 대시보드 메뉴")
    menu = st.sidebar.radio("메뉴를 선택하세요:", ["기본 EDA", "텍스트 분석"])
    
    # 데이터 필터링 사이드바
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 데이터 필터링")
    labels = sorted(df['label'].unique())
    selected_labels = st.sidebar.multiselect("뉴스 카테고리 필터:", labels, default=labels)
    
    # 필터 적용 데이터프레임
    filtered_df = df[df['label'].isin(selected_labels)]
    
    if filtered_df.empty:
        st.warning("선택한 필터 조건에 부합하는 데이터가 없습니다.")
    else:
        if menu == "기본 EDA":
            st.subheader("📊 기본 탐색적 데이터 분석 (EDA)")
            
            # --- KPI 카드를 최상단에 배치 (핵심 원칙) ---
            kpi_cols = st.columns(4)
            with kpi_cols[0]:
                st.metric("총 뉴스 기사 수", f"{len(filtered_df):,} 건")
            with kpi_cols[1]:
                st.metric("선택된 카테고리 수", f"{len(selected_labels)} 개")
            with kpi_cols[2]:
                avg_chars = filtered_df['char_count'].mean()
                st.metric("평균 기사 글자 수", f"{avg_chars:.1f} 자")
            with kpi_cols[3]:
                most_common = filtered_df['label'].value_counts().idxmax()
                most_common_cnt = filtered_df['label'].value_counts().max()
                st.metric("가장 많은 카테고리", f"{most_common} ({most_common_cnt}건)")
            
            st.markdown("---")
            
            # 레이아웃 구성
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏷️ 뉴스 카테고리(Label) 분포")
                label_counts = filtered_df['label'].value_counts().reset_index()
                label_counts.columns = ['카테고리', '기사 수']
                fig_label = px.bar(
                    label_counts, 
                    x='카테고리', 
                    y='기사 수', 
                    color='카테고리',
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    title="뉴스 카테고리별 기사 건수"
                )
                fig_label.update_layout(showlegend=False, template='plotly_white')
                st.plotly_chart(fig_label, use_container_width=True)
                
            with col2:
                st.markdown("### 📏 뉴스 제목 길이 분포 (글자 수 / 단어 수)")
                fig_dist = go.Figure()
                fig_dist.add_trace(go.Histogram(x=filtered_df['char_count'], name='글자 수', marker_color='#3B82F6', opacity=0.75))
                fig_dist.add_trace(go.Histogram(x=filtered_df['word_count'], name='단어 수', marker_color='#10B981', opacity=0.75))
                fig_dist.update_layout(
                    title="글자 수 및 단어 수 히스토그램",
                    barmode='overlay',
                    template='plotly_white',
                    xaxis_title="길이 / 단어 수",
                    yaxis_title="빈도"
                )
                fig_dist.update_traces(opacity=0.75)
                st.plotly_chart(fig_dist, use_container_width=True)
            
            st.info("💡 **분포 해석**: 카테고리가 7개 분야로 정확히 균등하게 분포(각 428~429건)되어 있어, 카테고리 편향(Class Imbalance) 문제없이 안정적인 분석이 가능합니다. 뉴스 제목의 글자 수와 단어 수 분포는 대략 25자~30자(단어 6~7개) 구간에 데이터가 집중되는 전형적인 짧은 기사 제목의 형태를 보입니다.")
            
            st.markdown("---")
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("### 📈 기사 길이와 단어 수의 상관관계")
                fig_scatter = px.scatter(
                    filtered_df,
                    x='char_count',
                    y='word_count',
                    color='label',
                    opacity=0.6,
                    title="글자 수 대비 단어 수 분포",
                    labels={'char_count': '글자 수', 'word_count': '단어 수'},
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_scatter.update_layout(template='plotly_white')
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            with col4:
                st.markdown("### 📦 카테고리별 글자 수 비교 (Box Plot)")
                fig_box = px.box(
                    filtered_df,
                    x='label',
                    y='char_count',
                    color='label',
                    title="카테고리별 글자 수 분포 비교",
                    labels={'label': '카테고리', 'char_count': '글자 수'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_box.update_layout(showlegend=False, template='plotly_white')
                st.plotly_chart(fig_box, use_container_width=True)
            
            st.info("💡 **상관관계 및 비교 해석**:\n\n"
                    "- **상관관계**: 글자 수와 단어 수는 매우 뚜렷한 정비례(선형) 관계를 보입니다. 뉴스 제목의 특성상 단어 하나당 평균 4.1자 수준으로 구성되어 있으며, 불필요한 공백이나 비정상 단어 패턴이 적은 규칙적인 어절 구성을 갖추고 있습니다.\n"
                    "- **카테고리별 비교**: '세계', '스포츠', '정치' 카테고리는 중앙값(Median)이 약 28자로 제목이 상대적으로 길고 균일한 편인 반면, '생활문화'는 중앙값 약 25자로 짧은 제목의 비중이 높고 넓은 이상치 영역을 가지고 있어 카테고리별 제목 작성 관행의 미세한 차이를 나타냅니다.")
            
            st.markdown("---")
            
            # 기술통계 및 왜도/첨도 정보 (항목 분석 기법 반영)
            st.markdown("### 📑 기사 길이 기술통계 및 분포 형태")
            desc_cols = st.columns(2)
            with desc_cols[0]:
                st.markdown("**글자 수 기술통계**")
                desc_char = filtered_df['char_count'].describe().to_frame().T
                st.dataframe(desc_char, use_container_width=True)
                
                # 왜도 및 첨도 계산
                skew_char = filtered_df['char_count'].skew()
                kurt_char = filtered_df['char_count'].kurt()
                st.info(f"💡 **글자 수 왜도(Skewness)**: `{skew_char:.3f}` | **첨도(Kurtosis)**: `{kurt_char:.3f}`"
                        f"\n- 왜도가 0에 가깝고 첨도가 3에 가까울수록 정규분포를 따릅니다.")
                
            with desc_cols[1]:
                st.markdown("**단어 수 기술통계**")
                desc_word = filtered_df['word_count'].describe().to_frame().T
                st.dataframe(desc_word, use_container_width=True)
                
                skew_word = filtered_df['word_count'].skew()
                kurt_word = filtered_df['word_count'].kurt()
                st.info(f"💡 **단어 수 왜도(Skewness)**: `{skew_word:.3f}` | **첨도(Kurtosis)**: `{kurt_word:.3f}`")
            
            st.info("💡 **통계적 분포 상세 해석**:\n\n"
                    "- **글자 수 왜도(-0.887) 및 첨도(1.449)**: 음수 왜도는 분포의 꼬리가 왼쪽에 있음을 의미하며, 20자 미만의 지나치게 짧은 기사 제목보다 25~35자 사이의 정상적인 기사 제목 비중이 높음을 뜻합니다. 첨도가 양수이므로 정규분포에 비해 중앙 부근에 상대적으로 뾰족하게 모여 있습니다.\n"
                    "- **단어 수 왜도(-0.170) 및 첨도(0.183)**: 왜도가 0에 매우 가깝고 첨도 또한 0 부근으로 정규분포(대칭형 종 모양)에 고도로 수렴하는 이상적인 단어 길이 분포를 나타냅니다.")
                
            st.markdown("---")
            st.markdown("### 🔍 데이터 미리보기 및 검색")
            st.dataframe(filtered_df[['title', 'label', 'char_count', 'word_count']], use_container_width=True)

        elif menu == "텍스트 분석":
            st.subheader("🤖 TF-IDF, 차원축소 및 군집 기반 텍스트 심화 분석")
            
            with st.spinner("텍스트 벡터화 및 차원축소, 군집화 모델을 학습 중입니다..."):
                vectorizer, tfidf_matrix, svd, svd_matrix, kmeans, cluster_labels, coords_2d = run_text_analysis(filtered_df['title'])
            
            # --- 텍스트 분석 KPI 최상단 배치 ---
            kpi_cols = st.columns(4)
            with kpi_cols[0]:
                st.metric("총 추출 고유 단어 수 (Vocab Size)", f"{len(vectorizer.vocabulary_):,} 개")
            with kpi_cols[1]:
                n_comp = getattr(svd, 'n_components', 7)
                st.metric("설정된 차원 축소 수 (Components)", f"{n_comp} 개 (LSA)")
            with kpi_cols[2]:
                n_clust = getattr(kmeans, 'n_clusters', 7)
                st.metric("설정된 군집 수 (Clusters)", f"{n_clust} 개 (K-Means)")
            with kpi_cols[3]:
                # SVD 누적 설명 분산량
                explained_variance = svd.explained_variance_ratio_.sum() * 100
                st.metric("LSA 누적 설명 분산량", f"{explained_variance:.2f} %")
                
            st.markdown("---")
            
            # 시각화 레이아웃
            col1, col2 = st.columns([3, 2])
            
            # 필터 적용된 데이터에 군집 할당
            filtered_df_with_cluster = filtered_df.copy()
            filtered_df_with_cluster['cluster'] = cluster_labels
            
            with col1:
                st.markdown("### 🌌 2D 차원축소 군집 시각화 (LSA -> PCA 2D)")
                plot_df = pd.DataFrame({
                    'PC1': coords_2d[:, 0],
                    'PC2': coords_2d[:, 1],
                    'Cluster': [f"Cluster {c}" for c in cluster_labels],
                    'Title': filtered_df['title'],
                    'Label': filtered_df['label']
                })
                
                fig_scatter_2d = px.scatter(
                    plot_df,
                    x='PC1',
                    y='PC2',
                    color='Cluster',
                    hover_data=['Title', 'Label'],
                    title="7개 군집의 2차원 공간 분포 (마우스 오버로 기사 확인 가능)",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_scatter_2d.update_layout(template='plotly_white', legend_title_text='군집')
                st.plotly_chart(fig_scatter_2d, use_container_width=True)
                
            with col2:
                st.markdown("### 📊 군집별 데이터 개수 및 라벨 구성 분포")
                cluster_label_dist = filtered_df_with_cluster.groupby(['cluster', 'label']).size().reset_index(name='count')
                cluster_label_dist['cluster'] = cluster_label_dist['cluster'].apply(lambda x: f"Cluster {x}")
                
                fig_cluster_bar = px.bar(
                    cluster_label_dist,
                    x='cluster',
                    y='count',
                    color='label',
                    title="군집별 기존 뉴스 카테고리 구성 비율",
                    labels={'cluster': '군집', 'count': '기사 수', 'label': '뉴스 카테고리'},
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_cluster_bar.update_layout(template='plotly_white')
                st.plotly_chart(fig_cluster_bar, use_container_width=True)
                
            st.markdown("---")
            
            # --- 상위/하위 50개 키워드 추출 분석 ---
            st.markdown("## 🔍 군집 및 토픽별 상위/하위 키워드 분석 (50개씩 추출)")
            
            # 키워드 추출 로직
            feature_names = vectorizer.get_feature_names_out()
            
            # 1) 토픽(TruncatedSVD components)별 키워드 추출
            topic_keywords = {}
            for i, component in enumerate(svd.components_):
                sorted_idx = np.argsort(component)
                # 하위 50개 (가중치 최소)
                bottom_50_idx = sorted_idx[:50]
                bottom_50_words = [feature_names[idx] for idx in bottom_50_idx]
                bottom_50_weights = [component[idx] for idx in bottom_50_idx]
                
                # 상위 50개 (가중치 최대)
                top_50_idx = sorted_idx[-50:][::-1]
                top_50_words = [feature_names[idx] for idx in top_50_idx]
                top_50_weights = [component[idx] for idx in top_50_idx]
                
                topic_keywords[i] = {
                    'top_words': top_50_words, 'top_weights': top_50_weights,
                    'bottom_words': bottom_50_words, 'bottom_weights': bottom_50_weights
                }
                
            # 2) 군집(K-Means centers)별 키워드 추출 (차원 축소 공간의 중심을 단어 공간으로 역투영)
            cluster_centers_vocab = svd.inverse_transform(kmeans.cluster_centers_)
            cluster_keywords = {}
            for i, center in enumerate(cluster_centers_vocab):
                sorted_idx = np.argsort(center)
                # 하위 50개
                bottom_50_idx = sorted_idx[:50]
                bottom_50_words = [feature_names[idx] for idx in bottom_50_idx]
                bottom_50_weights = [center[idx] for idx in bottom_50_idx]
                
                # 상위 50개
                top_50_idx = sorted_idx[-50:][::-1]
                top_50_words = [feature_names[idx] for idx in top_50_idx]
                top_50_weights = [center[idx] for idx in top_50_idx]
                
                cluster_keywords[i] = {
                    'top_words': top_50_words, 'top_weights': top_50_weights,
                    'bottom_words': bottom_50_words, 'bottom_weights': bottom_50_weights
                }
                
            # 분석 뷰어 레이아웃 (서브플롯 시각화 및 인사이트 일괄 표시)
            analysis_tab1, analysis_tab2 = st.tabs(["👥 군집(Cluster) 전체 서브플롯 및 인사이트", "🔮 LSA 토픽(Topic) 전체 서브플롯 및 인사이트"])
            
            with analysis_tab1:
                st.markdown("### 📊 7개 군집별 상위 10개 키워드 중요도 (한눈에 보기)")
                
                # 군집 서브플롯 생성 (2행 4열 격자 레이아웃)
                fig_clusters_sub = make_subplots(
                    rows=2, cols=4,
                    subplot_titles=[f"Cluster {i}" for i in range(7)],
                    horizontal_spacing=0.08,
                    vertical_spacing=0.15
                )
                
                for i in range(7):
                    row = (i // 4) + 1
                    col = (i % 4) + 1
                    c_data = cluster_keywords[i]
                    
                    # 가독성을 위해 상위 10개만 시각화
                    words = c_data['top_words'][:10][::-1]
                    weights = c_data['top_weights'][:10][::-1]
                    
                    fig_clusters_sub.add_trace(
                        go.Bar(
                            x=weights,
                            y=words,
                            orientation='h',
                            marker=dict(color=px.colors.qualitative.Set2[i % len(px.colors.qualitative.Set2)]),
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                
                fig_clusters_sub.update_layout(
                    height=700,
                    margin=dict(t=50, b=50, l=50, r=50),
                    template='plotly_white'
                )
                st.plotly_chart(fig_clusters_sub, use_container_width=True)
                
                # --- 군집별 상세 분석 인사이트 (300자 이상) ---
                st.markdown("---")
                st.markdown("### 💡 군집(Cluster)별 키워드 심화 분석 및 비즈니스 인사이트")
                
                # 7개 군집을 아코디언(st.expander) 형태로 정리하여 일괄 제공
                for i in range(7):
                    c_data = cluster_keywords[i]
                    top_words_str = ", ".join(c_data['top_words'][:15])
                    
                    with st.expander(f"📌 Cluster {i} 심화 분석 (핵심 키워드: {top_words_str[:60]}...)", expanded=True):
                        st.markdown(f"**대표 키워드:** `{', '.join(c_data['top_words'][:20])}`")
                        
                        if i == 0:
                            st.write(
                                "이 군집은 대통령, 트럼프, 문재인, 국회 등의 핵심 키워드들을 통해 국내 정치 및 대외 한미/한독 외교 관계에 관한 정치 뉴스를 대변하고 있습니다. "
                                "문재인 전 대통령과 도널드 트럼프 미국 전 대통령의 정상회담이나 대북 및 대미 전략, 여야 국회 대립 등 정국을 움직이는 굵직한 주요 정치 쟁점들이 대량으로 묶여 있습니다. "
                                "정치 관련 기사는 통상적으로 미치는 영향력과 대중의 관심도가 매우 높은 특성을 띱니다. "
                                "따라서 본 대시보드에서 분석된 정치 키워드는 각 기사 제목 간의 높은 의미적 유사성을 토대로 긴밀히 군집을 형성하고 있으며, "
                                "이를 통해 정당 간 입법 갈등이나 외교 현안 협의 등의 흐름을 파악하기에 매우 유용한 구조를 가지고 있음을 확인할 수 있습니다."
                            )
                        elif i == 1:
                            st.write(
                                "본 군집은 朴대통령, 이란, 한국, 최고, 올해, 공개 등의 키워드를 중심으로 박근혜 전 대통령 임기 당시 진행되었던 정상 외교 활동과 국제 경제 파트너십 구축 관련 기사들을 포함합니다. "
                                "특히 당시 주요 호재이자 이슈였던 이란 국빈 방문과 경제 제재 해제 이후의 대규모 인프라 수주, 그리고 한국 기업들의 글로벌 신제품 공개 및 대규모 포럼 개최 등 국가 단위의 경제 외교 정책에 밀접히 반응하고 있습니다. "
                                "이 군집은 외교 활동이 단순한 정치 행사에 그치지 않고, 국가 간 경제 협약과 첨단 스마트폰 등 수출 핵심 사업의 대외 공개와 같은 국내 거시 경제적 이익과 결부되어 기사화되었던 당시의 시대적 배경을 잘 드러내 줍니다."
                            )
                        elif i == 2:
                            st.write(
                                "이 군집은 신간, 한국, 인간, 남자, 강의, 역사, 조총 등의 어휘를 토대로 신규 출판 도서 소개와 교양, 인문학 강의 및 역사 정보 제공 등의 생활문화 영역 뉴스를 분류하고 있습니다. "
                                "현대 사회인들의 지식 욕구를 충족시키기 위한 인문 교양 도서 및 다양한 인문적 질문을 던지는 신작 소개들이 대거 포함되어 있습니다. "
                                "텍스트 분석 결과에 따르면, 이 군집은 과학기술이나 딱딱한 증권 실적 공시 등 타 군집의 키워드들과 공유하는 어휘가 거의 없는 독자적인 어휘적 특징을 띱니다. "
                                "즉, 책 제목에 자주 등장하는 추상적이거나 철학적인 단어(인간, 역사 등)가 이 군집만의 고유한 텍스트 패턴을 형성하며 명확한 문화 도서 클러스터로 정착하게 되었습니다."
                            )
                        elif i == 3:
                            st.write(
                                "본 군집은 kt, 5g, 출시, 서비스, skt, 가입자, 요금제 등의 기술 지향적이고 비즈니스적인 어휘들을 중심으로 형성되었습니다. "
                                "국내 대표적인 이동통신 사업자인 SKT와 KT가 차세대 5G 인프라를 구축하고 시장 점유율을 차지하기 위해 치열한 가입자 유치 판촉 및 마케팅 경쟁을 벌이던 시기의 통신사 동향을 면밀히 담고 있습니다. "
                                "5G 상용화 초기의 요금제 논란, 네트워크 기술 개발 현황, 그리고 데이터 무제한 요금제 도입 등 통신 소비자들의 실생활과 밀접한 실무적 정보성 기사들이 주를 이룹니다. "
                                "이 클러스터는 통신 인프라 혁신 속에서 테크 기업들이 신규 부가 서비스를 발표하고 고객 만족도를 높이기 위해 기획한 비즈니스 이벤트들을 직접 반영하고 있습니다."
                            )
                        elif i == 4:
                            st.write(
                                "이 군집은 게시판, 개최, 미래부, 업무협약, 워크숍, rd(연구개발) 등의 단어들이 주도하고 있습니다. "
                                "이는 과학기술정보통신부(구 미래창조과학부 등)나 산하기관, 주요 기업 연합체들이 연구개발 활성화를 위해 체결하는 대외 업무협약(MOU)이나 공청회, 워크숍 등의 정형화된 공공 및 학술 발표 뉴스를 그룹화한 결과입니다. "
                                "기사 제목의 구조가 'OO 개최', 'OO 체결', 'OO 출범'과 같이 패턴이 매우 정형화되어 있는 것이 특징이며, 일상적인 정보 제공성 공고문 성격을 갖습니다. "
                                "따라서 텍스트 벡터 상에서 이러한 형식적 단어들의 코사인 유사도가 높게 계산되어 하나의 거대한 공공/학술 알림성 군집을 자연스럽게 이루고 있음을 해석할 수 있습니다."
                            )
                        elif i == 5:
                            st.write(
                                "본 군집은 영업익, 증가, 작년, 2분기, 1분기, 3분기, 감소, 연결, 영업이익 등의 수치 및 재무 용어들로 완전히 집중되어 있습니다. "
                                "코스피 및 코스닥에 상장된 상장 기업들이 분기별 혹은 반기별로 발표하는 공식 기업 공시(Earnings Release) 뉴스들을 명확히 포착하고 있습니다. "
                                "영업이익의 전년 동기 대비 증가 및 감소율, 연결 기준 재무제표 수치 등 기업 경영의 투명성을 나타내는 객관적 수치 정보가 뉴스 제목의 대부분을 채우고 있습니다. "
                                "주식 투자자들과 금융 시장 참가자들의 중요한 의사결정 지표로 활용되는 경제 기사군이며, "
                                "텍스트 분석 관점에서는 일반적인 뉴스 제목들과는 완전히 차별화된 분기형 정량 키워드들이 강하게 결합하여 독보적인 고유 군집을 보여줍니다."
                            )
                        elif i == 6:
                            st.write(
                                "이 군집은 출시, 국내, 삼성, lg, 스마트폰, lg전자, 서비스, 애플, 구글 등의 핵심 기술 및 제조사 브랜드들을 포함하고 있습니다. "
                                "삼성전자, LG전자 등 국내 대표 하드웨어 제조사들과 애플, 구글 같은 글로벌 테크 자이언트 간의 스마트폰, 디바이스, 신규 가전 신제품 출시 및 시장 주도권 쟁탈전에 관련한 뉴스가 이 군집을 대표합니다. "
                                "신제품의 티저 이미지 공개부터 사전 예약 개시, 공식 출시로 이어지는 일련의 하이테크 비즈니스 라이프사이클을 그대로 반영하며, 기술적 사양과 글로벌 혁신 경쟁 구도가 돋보이는 기사들입니다. "
                                "이는 통신망을 다루는 5G 인프라 군집(Cluster 3)과는 구별되는, 물리적인 제품 단말 및 IT 기기 하드웨어 시장의 흐름을 정확히 묘사하고 있습니다."
                            )
            
            with analysis_tab2:
                st.markdown("### 🔮 7개 LSA 토픽별 상위 10개 키워드 기여도 (한눈에 보기)")
                
                # 토픽 서브플롯 생성 (2행 4열 격자 레이아웃)
                fig_topics_sub = make_subplots(
                    rows=2, cols=4,
                    subplot_titles=[f"Topic {i+1}" for i in range(7)],
                    horizontal_spacing=0.08,
                    vertical_spacing=0.15
                )
                
                for i in range(7):
                    row = (i // 4) + 1
                    col = (i % 4) + 1
                    t_data = topic_keywords[i]
                    
                    words = t_data['top_words'][:10][::-1]
                    weights = t_data['top_weights'][:10][::-1]
                    
                    fig_topics_sub.add_trace(
                        go.Bar(
                            x=weights,
                            y=words,
                            orientation='h',
                            marker=dict(color=px.colors.qualitative.Safe[i % len(px.colors.qualitative.Safe)]),
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                
                fig_topics_sub.update_layout(
                    height=700,
                    margin=dict(t=50, b=50, l=50, r=50),
                    template='plotly_white'
                )
                st.plotly_chart(fig_topics_sub, use_container_width=True)
                
                # --- 토픽별 상세 분석 인사이트 (300자 이상) ---
                st.markdown("---")
                st.markdown("### 💡 LSA 토픽(Topic)별 성분 분석 및 의미 해석")
                
                for i in range(7):
                    t_data = topic_keywords[i]
                    top_words_str = ", ".join(t_data['top_words'][:15])
                    
                    with st.expander(f"📌 Topic {i+1} 상세 성분 분석 (핵심 키워드: {top_words_str[:60]}...)", expanded=True):
                        st.markdown(f"**상위 키워드:** `{', '.join(t_data['top_words'][:20])}`")
                        
                        if i == 0:
                            st.write(
                                "Topic 1은 출시, 서비스, 국내, 삼성, lg, 스마트폰 등 ICT 디바이스 제품 및 소프트웨어 서비스의 출시에 기여하는 강한 성향을 나타냅니다. "
                                "IT 제조사와 유통망이 주도하는 상업적 테크 생태계를 분석하는 토픽으로, 새로운 제품이 국내 시장에 도입되었을 때 나타나는 대중적 기대감과 브랜드 파워의 흐름을 정량적으로 관찰할 수 있습니다. "
                                "상위 단어들이 기술적 사양이나 특정 기능보다 제품의 국내 상용화 자체에 높은 가중치를 두고 있는 점은, "
                                "해당 데이터셋이 신기술 개발 소식보다는 소비자가 즉각 체감할 수 있는 상용 디바이스 출시와 마케팅 이벤트성 정보에 더 편향되어 보도되고 있음을 의미론적으로 증명합니다."
                            )
                        elif i == 1:
                            st.write(
                                "Topic 2는 신간, 한국, 인간, 남자, 강의, 역사 등의 독특한 인문·교양적 단어 군에 높은 양의 가중치를 부여하고 있습니다. "
                                "이는 뉴스 데이터 전반에서 출판 및 생활문화 영역의 흐름을 한눈에 대변해 줍니다. "
                                "텍스트 분석 관점에서 이 토픽은 사회적 제도나 하이테크 인프라와는 정반대의 거리에 위치한 개인의 내면적 성장, 역사에 대한 탐구, 인간 본성에 관한 철학적 논의를 주로 추적합니다. "
                                "강의 정보나 인문 지식 교양 콘텐츠 기사의 등장 패턴을 정교하게 모델링하고 있으며, "
                                "바쁘고 획일화된 뉴스 매체 환경 내에서도 지속적으로 소비되는 문화적·소양적 콘텐츠의 독립적인 영역과 고유 가치를 입증하는 분석 지표로 평가됩니다."
                            )
                        elif i == 2:
                            st.write(
                                "Topic 3은 게시판, 개최, 미래부, 업무협약, 워크숍 등의 업무 중심적 용어들이 압도적인 기여도를 갖습니다. "
                                "정부 부처와 학계, 산학 협력단이 주최하는 공적 네트워크 행사와 정책 공고를 집계하고 필터링하는 데 매우 유용한 토픽입니다. "
                                "기업 간 협력을 의미하는 업무협약이나 국가 미래 성장을 위한 연구개발(R&D) 보고회 등 공적인 어조를 띠는 텍스트를 고유한 성분으로 분리해 냅니다. "
                                "이 토픽을 통해 사용자는 뉴스 데이터가 지닌 정책 집행의 투명성이나 산학협력 활성화 추세를 모니터링할 수 있으며, "
                                "불필요한 홍보성 기사들 중에서 순수한 제도적 발표나 행사 알림 성격의 기사들을 구별하여 필터링하는 용도로 활용할 수 있습니다."
                            )
                        elif i == 3:
                            st.write(
                                "Topic 4는 대통령, 트럼프, 문재인, 국회, 청와대 등 여야 대치 및 국가 수반의 최고 외교 활동에 높은 양의 가중치를 할당합니다. "
                                "한반도를 둘러싼 외교 역학 관계와 입법부의 거시 정치를 전문적으로 추적하는 축(Dimension)입니다. "
                                "정상회담의 성패, 대외 공동성명 발표, 정당 간의 대치 구도 등 매체의 메인 헤드라인을 차지하는 중량감 있는 거시 이슈들이 집중 분석됩니다. "
                                "텍스트 분석에서는 단어 간의 높은 연관 강도를 통해 외교 현안 협상과 국회 내 쟁점 법안 입법 갈등 등이 의미상 밀접하게 얽혀 있음을 입증하며, "
                                "국내외를 관통하는 핵심적 정치적 사건의 변곡점을 시계열적으로 추적하는 데 아주 강력한 토픽 요소로 기능합니다."
                            )
                        elif i == 5:
                            st.write(
                                "Topic 6은 영업익, 증가, 작년, 2분기, 감소, 영업이익 등 기업의 실적 공시 정보를 정밀하게 식별하는 통계적 차원입니다. "
                                "기업 경영 성과가 거시 경제 지표에 미치는 영향을 데이터 측면에서 정량화하여 제시합니다. "
                                "분기별 실적 발표 시기에 뉴스 기사량이 급증하는 경향을 보이며, 전년 대비 증감 수치는 주식 시장에 즉각적인 피드백을 전달하는 매개체가 됩니다. "
                                "텍스트 분석에서는 복잡한 서술형 묘사 없이 객관적인 회계 지표 단어들이 고도의 연관성을 갖고 하나의 축을 이룸으로써, "
                                "전체 한글 뉴스 원문 텍스트 내에서 산업 및 기업 실적 변화 흐름을 다른 노이즈 이슈들과 완벽히 격리하여 체계적으로 파악하도록 돕습니다."
                            )
                        elif i == 4:
                            st.write(
                                "Topic 5는 kt, 5g, skt, 가입자, 네트워크, 데이터 등의 키워드에 집중하여 차세대 무선 통신 고속도로(인프라) 도입과 이에 따른 비즈니스 생태계 변화를 추적합니다. "
                                "타 IT 제품군과 구별되는 고속 5G 네트워크 기술 자체의 상용화 흐름을 모니터링하기 위해 별도의 독립적인 차원으로 축소되었습니다. "
                                "5G망 상용화를 위한 통신사들의 설비 투자, 커버리지 확충 경쟁, 모바일 트래픽 급증에 대응하는 플랫폼 기술 등이 핵심 주제로 부각됩니다. "
                                "이를 통하여 ICT 인프라 고도화가 기업 간 신제품 경쟁(Topic 1)의 밑바탕이 되고 있으며, "
                                "경제 활성화와 플랫폼 비즈니스의 성장동력으로 작동하는 기술적 근간임이 객관적으로 증명됩니다."
                            )
                        elif i == 6:
                            st.write(
                                "Topic 7은 朴대통령, 이란, 한국, 핵합, 방문 등 과거 정상의 국빈 방문과 글로벌 안보 및 다자 외교 협정 뉴스를 특징짓는 차원입니다. "
                                "특정 역사적 사건(예: 이란 핵협정 및 자원 협력 방문)을 중심으로 뉴스 매체들이 어떻게 한 국가의 외교 안보 어젠다를 구성하는지 잘 보여줍니다. "
                                "국제 정세의 안정화 여부와 에너지 자원 확보, 글로벌 핵 비확산 조치 등 고도의 국제 정치학적 맥락을 반영하는 고급 뉴스군입니다. "
                                "텍스트의 다차원 공간 분석을 통해, 이란과 같은 특정 외교 대상국과의 협력 관계가 단발성 행사가 아닌 경제·에너지·안보의 다차원적 복합 관계로 뉴스 생태계에서 매우 독자적으로 다루어지고 있음을 증명합니다."
                            )
            
            st.markdown("---")
            
            # 군집별 샘플 뉴스 기사 보기 (드릴 다운)
            st.markdown("### 📝 군집별 뉴스 기사 드릴 다운")
            selected_cluster_drill = st.selectbox("샘플 기사를 조회할 군집:", range(7), format_func=lambda x: f"Cluster {x} 샘플 기사")
            cluster_samples = filtered_df_with_cluster[filtered_df_with_cluster['cluster'] == selected_cluster_drill][['title', 'label']].head(15)
            st.dataframe(cluster_samples, use_container_width=True)
            
            st.markdown("---")
            # --- 🔍 코사인 유사도 기반 유사 기사 검색 및 추천 섹션 ---
            st.markdown("### 🔍 뉴스 기사 코사인 유사도 검색 및 추천")
            st.info("💡 **유사 기사 추천 서비스**: 선택하신 뉴스 기사와 TF-IDF 벡터 거리가 가장 가까운(코사인 유사도가 높은) 다른 뉴스 기사들을 탐색하여 실시간 추천합니다. 아래 조절바를 통해 추천 임계값과 개수를 실시간으로 조정하실 수 있습니다.")
            
            # 입력 데이터가 있는 경우 분석 진행
            unique_titles = filtered_df['title'].unique()
            selected_title = st.selectbox("유사도를 비교할 기준 뉴스 기사를 선택하세요:", unique_titles)
            
            # 조절 필터 UI 구성 (요청 사항: 임계값과 개수 조정 기능 UI 추가)
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                similarity_threshold = st.slider("유사도 임계값 기준 (Threshold)", min_value=0.0, max_value=1.0, value=0.15, step=0.05,
                                                 help="설정한 임계값 점수 이상을 가진 유사한 기사들만 필터링하여 노출합니다.")
            with filter_col2:
                top_n = st.slider("유사 기사 최대 노출 개수 (Top N)", min_value=1, max_value=30, value=5, step=1,
                                  help="유사도 순위가 가장 높은 상위 N개의 기사를 화면에 노출합니다.")
            
            # 유사도 연산 수행
            # 기준 문서의 상대 인덱스 확인
            rel_idx_arr = filtered_df.reset_index().index[filtered_df.reset_index()['title'] == selected_title]
            if len(rel_idx_arr) > 0:
                selected_relative_idx = rel_idx_arr[0]
                
                # TF-IDF 행렬에서 기준 벡터 추출
                selected_vector = tfidf_matrix[selected_relative_idx]
                
                # 코사인 유사도 계산 -> [1, N_docs]
                sim_scores = cosine_similarity(selected_vector, tfidf_matrix).flatten()
                
                # 전체 데이터 복사 및 유사도 할당
                similarity_results = filtered_df.copy().reset_index(drop=True)
                similarity_results['유사도 점수'] = sim_scores
                
                # 자기 자신 제외
                similarity_results = similarity_results[similarity_results.index != selected_relative_idx]
                
                # 임계값 필터링 및 정렬
                filtered_similarity_results = similarity_results[similarity_results['유사도 점수'] >= similarity_threshold]
                filtered_similarity_results = filtered_similarity_results.sort_values(by='유사도 점수', ascending=False).head(top_n)
                
                # 결과 출력
                st.markdown(f"#### 🎯 '{selected_title}' 와 유사도가 높은 기사 추천 결과")
                if filtered_similarity_results.empty:
                    st.warning(f"⚠️ 유사도 점수가 `{similarity_threshold}` 이상인 기사가 없습니다. 임계값을 더 낮추거나 다른 기사를 선택해 보세요.")
                else:
                    # 표 형태로 출력
                    disp_df = filtered_similarity_results[['title', 'label', '유사도 점수']].rename(columns={'title': '뉴스 제목', 'label': '카테고리'})
                    st.dataframe(disp_df.set_index('뉴스 제목'), use_container_width=True)
                    
                    # 시각화 추가 (Plotly 가로 바 차트로 유사도 시각화)
                    fig_sim = px.bar(
                        filtered_similarity_results,
                        x='유사도 점수',
                        y='title',
                        color='유사도 점수',
                        orientation='h',
                        title="추천된 뉴스 기사별 코사인 유사도 분포",
                        labels={'title': '뉴스 제목', '유사도 점수': '유사도'},
                        color_continuous_scale='Viridis'
                    )
                    fig_sim.update_layout(yaxis={'categoryorder':'total ascending'}, template='plotly_white')
                    st.plotly_chart(fig_sim, use_container_width=True)
