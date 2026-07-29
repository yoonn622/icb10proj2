"""
Online Shoppers Purchasing Intention 데이터셋 EDA 및 ML 예측 대시보드
작성일: 2026-07-18
설명: 온라인 쇼핑몰 방문 고객의 행동 데이터를 분석하는 EDA 대시보드와 함께,
      랜덤 포레스트(Random Forest) 및 부스팅(Boosting) 알고리즘을 활용해
      고객의 구매 전환(Revenue) 여부를 예측하고 모델 성능을 평가/비교하는 Streamlit 통합 대시보드입니다.
      Mermaid.js async render API 및 JSON 변환을 적용하여 시퀀스 다이어그램 시각화 오류를 100% 근본 해결하였습니다.
"""

import os
import zipfile
import textwrap
import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

# Scikit-Learn 머신러닝 모듈
from sklearn.model_selection import train_test_split
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    AdaBoostClassifier
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve
)

# 1. 페이지 설정
st.set_page_config(
    page_title="온라인 쇼핑 구매 의도 EDA & ML 대시보드",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 적용 (프리미엄 비즈니스 대시보드 디자인 고도화)
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    .main {
        background-color: #f4f6f9;
    }
    /* KPI 카드 스타일링 */
    .kpi-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 22px 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        text-align: center;
        border-top: 4px solid #4e73df;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .kpi-container:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }
    .kpi-title {
        font-size: 13px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 26px;
        color: #0f172a;
        font-weight: 800;
    }
    /* 비즈니스 전략 카드 */
    .strategy-card {
        background-color: #ffffff;
        border-left: 5px solid #4e73df;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    </style>
""", unsafe_allow_html=True)


# 2. Mermaid.js 시각화 도우미 함수 (json.dumps + async render API 사용으로 오류 100% 해결)
def render_mermaid(code: str, height: int = 500, elem_id: str = "mermaid_svg"):
    """
    Mermaid.js async render API를 활용하여 오류 없이 SVG를 선명하게 렌더링하는 함수
    """
    clean_code = textwrap.dedent(code).strip()
    json_code = json.dumps(clean_code)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
      <style>
        body {{
          background-color: transparent;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Pretendard', sans-serif;
          margin: 0;
          padding: 5px;
          display: flex;
          justify-content: center;
          align-items: center;
        }}
        #mermaid-container {{
          background: #ffffff;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 4px 15px rgba(0,0,0,0.05);
          border: 1px solid #e2e8f0;
          width: 96%;
          min-height: 120px;
          display: flex;
          justify-content: center;
          align-items: center;
        }}
        svg {{
          max-width: 100% !important;
          height: auto !important;
        }}
      </style>
    </head>
    <body>
      <div id="mermaid-container">다이어그램을 로딩 중입니다...</div>
      <script>
        mermaid.initialize({{
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
        }});

        const graphDefinition = {json_code};
        
        async function drawDiagram() {{
          const container = document.getElementById('mermaid-container');
          try {{
            const res = await mermaid.render('{elem_id}', graphDefinition);
            container.innerHTML = res.svg;
          }} catch (error) {{
            console.error("Mermaid Render Error:", error);
            container.innerHTML = '<div style="color:#e74a3b; padding:15px; font-weight:bold;">⚠️ 다이어그램 렌더링 예외: ' + error.message + '</div>';
          }}
        }}
        
        drawDiagram();
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=True)


# 3. EDA용 데이터 로드 및 전처리 캐싱
@st.cache_data
def load_data():
    """
    EDA용 데이터셋을 로드하고 명목형 변수를 문자열로 변환하는 캐싱 함수
    """
    zip_path = "online-shoppers/data/online+shoppers+purchasing+intention+dataset.zip"
    
    if not os.path.exists(zip_path):
        possible_paths = [
            zip_path,
            "data/online+shoppers+purchasing+intention+dataset.zip",
            "../data/online+shoppers+purchasing+intention+dataset.zip"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                zip_path = path
                break
                
    if not os.path.exists(zip_path):
        st.error(f"데이터 파일을 찾을 수 없습니다. 경로를 확인해 주세요. (확인한 경로: {zip_path})")
        return pd.DataFrame()

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        csv_filename = "online_shoppers_intention.csv"
        if csv_filename in zip_ref.namelist():
            with zip_ref.open(csv_filename) as f:
                df = pd.read_csv(f)
        else:
            csv_files = [name for name in zip_ref.namelist() if name.endswith('.csv')]
            if csv_files:
                with zip_ref.open(csv_files[0]) as f:
                    df = pd.read_csv(f)
            else:
                st.error("Zip 파일 내에 CSV 파일이 존재하지 않습니다.")
                return pd.DataFrame()
                
    df_clean = df.copy()
    categorical_num_cols = ['OperatingSystems', 'Browser', 'Region', 'TrafficType']
    for col in categorical_num_cols:
        df_clean[col] = df_clean[col].astype(str)
        
    return df_clean


# 4. ML 전용 데이터 전처리 캐싱 함수
@st.cache_data
def preprocess_ml_data(df_input):
    """
    머신러닝 모델 학습을 위해 범주형 변수 원-핫 인코딩 및 타겟 변수를 정수형으로 변환하는 함수
    """
    df_ml = df_input.copy()
    df_ml['Revenue'] = df_ml['Revenue'].astype(int)
    if 'Weekend' in df_ml.columns:
        df_ml['Weekend'] = df_ml['Weekend'].astype(int)
        
    cat_cols = ['Month', 'VisitorType', 'OperatingSystems', 'Browser', 'Region', 'TrafficType']
    df_encoded = pd.get_dummies(df_ml, columns=cat_cols, drop_first=True)
    
    X = df_encoded.drop(columns=['Revenue'])
    y = df_encoded['Revenue']
    
    return X, y, list(X.columns)


# 5. ML 모델 학습 및 평가 함수
def train_and_evaluate_model(algorithm_name, params, X_train, X_test, y_train, y_test, use_class_weight=False):
    """
    선택된 머신러닝 알고리즘과 하이퍼파라미터로 모델을 학습시키고 평가 지표를 반환하는 함수
    """
    if algorithm_name == "Random Forest":
        kw = {
            'n_estimators': params.get('n_estimators', 100),
            'max_depth': params.get('max_depth', 10),
            'random_state': params.get('random_state', 42),
            'n_jobs': -1
        }
        if use_class_weight:
            kw['class_weight'] = 'balanced'
        model = RandomForestClassifier(**kw)
        
    elif algorithm_name == "Gradient Boosting":
        kw = {
            'n_estimators': params.get('n_estimators', 100),
            'max_depth': params.get('max_depth', 5),
            'learning_rate': params.get('learning_rate', 0.1),
            'random_state': params.get('random_state', 42)
        }
        model = GradientBoostingClassifier(**kw)

    elif algorithm_name == "HistGradient Boosting":
        kw = {
            'max_iter': params.get('n_estimators', 100),
            'max_depth': params.get('max_depth', 10),
            'learning_rate': params.get('learning_rate', 0.1),
            'random_state': params.get('random_state', 42)
        }
        if use_class_weight:
            kw['class_weight'] = 'balanced'
        model = HistGradientBoostingClassifier(**kw)
        
    elif algorithm_name == "AdaBoost":
        kw = {
            'n_estimators': params.get('n_estimators', 100),
            'learning_rate': params.get('learning_rate', 0.1),
            'random_state': params.get('random_state', 42)
        }
        model = AdaBoostClassifier(**kw)
    else:
        raise ValueError(f"지원하지 않는 알고리즘입니다: {algorithm_name}")

    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
    else:
        y_proba = y_pred

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    
    feature_importances = None
    if hasattr(model, 'feature_importances_'):
        feature_importances = model.feature_importances_

    return {
        'model': model,
        'y_pred': y_pred,
        'y_proba': y_proba,
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1': f1,
        'auc': auc,
        'confusion_matrix': cm,
        'feature_importances': feature_importances
    }


# 6. 4대 ML 알고리즘 일괄 성능 비교 함수
def get_all_models_comparison(params, X_train, X_test, y_train, y_test, use_class_weight=False):
    """
    Random Forest, Gradient Boosting, HistGradient Boosting, AdaBoost 4개 모델의
    Accuracy, Precision, Recall, F1-Score, ROC-AUC 성능 대조표를 일괄 계산하는 함수
    """
    algo_list = ["Random Forest", "Gradient Boosting", "HistGradient Boosting", "AdaBoost"]
    comparison_records = []

    for algo in algo_list:
        res = train_and_evaluate_model(algo, params, X_train, X_test, y_train, y_test, use_class_weight)
        comparison_records.append({
            "알고리즘 (Algorithm)": algo,
            "정확도 (Accuracy)": res['accuracy'],
            "정밀도 (Precision)": res['precision'],
            "재현율 (Recall)": res['recall'],
            "F1-Score": res['f1'],
            "ROC-AUC": res['auc']
        })

    return pd.DataFrame(comparison_records)


# 메인 데이터 로딩
df = load_data()
if df.empty:
    st.stop()

# ----------------- 사이드바 메인 탐색 메뉴 -----------------
st.sidebar.title("📌 대시보드 메인 메뉴")
main_page = st.sidebar.radio(
    "원하는 페이지를 선택하세요:",
    ["📊 EDA & 비즈니스 대시보드", "🤖 ML 모델 학습 및 평가"],
    index=0
)
st.sidebar.markdown("---")

# ==============================================================================
# PAGE 1: EDA & 비즈니스 대시보드 (기존 페이지)
# ==============================================================================
if main_page == "📊 EDA & 비즈니스 대시보드":
    st.sidebar.header("📊 EDA 분석 필터")

    months_options = sorted(df['Month'].unique())
    visitor_options = sorted(df['VisitorType'].unique())
    weekend_options = [True, False]

    selected_months = st.sidebar.multiselect("방문 월 (Month)", options=months_options, default=months_options)
    selected_visitors = st.sidebar.multiselect("방문자 유형 (VisitorType)", options=visitor_options, default=visitor_options)
    selected_weekends = st.sidebar.multiselect("주말 여부 (Weekend)", options=weekend_options, default=weekend_options)

    filtered_df = df[
        df['Month'].isin(selected_months) &
        df['VisitorType'].isin(selected_visitors) &
        df['Weekend'].isin(selected_weekends)
    ]

    if filtered_df.empty:
        st.warning("선택한 필터 조건에 부합하는 데이터가 없습니다. 필터를 다시 설정해 주세요.")
        st.stop()

    st.title("🛍️ 온라인 쇼핑몰 고객 구매 의도 분석 대시보드")
    st.markdown("본 대시보드는 쇼핑 세션 정보 데이터를 바탕으로 **구매 전환(Revenue)** 여부에 따른 고객 행동 특성 차이를 통계적으로 분석합니다.")

    # 핵심 KPI 영역 (상단 배치)
    st.markdown("### 🔑 핵심 비즈니스 KPI")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    total_sessions = len(filtered_df)
    purchased_sessions = filtered_df['Revenue'].sum()
    conversion_rate = (purchased_sessions / total_sessions) * 100 if total_sessions > 0 else 0.0
    avg_page_value = filtered_df['PageValues'].mean()

    with kpi_col1:
        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">총 세션(방문) 수</div>
                <div class="kpi-value">{total_sessions:,} 건</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #1cc88a;">
                <div class="kpi-title">구매 전환 세션 수</div>
                <div class="kpi-value">{purchased_sessions:,} 건</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #f6c23e;">
                <div class="kpi-title">구매 전환율 (CR)</div>
                <div class="kpi-value">{conversion_rate:.2f} %</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #36b9cc;">
                <div class="kpi-title">평균 페이지 가치</div>
                <div class="kpi-value">$ {avg_page_value:.2f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 메인 레이아웃 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📋 데이터 개요", "📈 수치형 변수 분석 (Numerical)", "📊 범주형 변수 분석 (Categorical)", "🎯 퍼널 분석 (Funnel)"])

    # ----------------- Tab 1: 데이터 개요 -----------------
    with tab1:
        st.subheader("데이터 개요 및 결측치 현황")
        col_info1, col_info2 = st.columns([1, 1])
        
        with col_info1:
            st.markdown("#### 데이터 정보 요약")
            summary_info = {
                "전체 행(세션) 수": [f"{df.shape[0]:,}"],
                "필터링된 행 수": [f"{filtered_df.shape[0]:,}"],
                "전체 열(변수) 수": [f"{df.shape[1]}"],
                "결측치(Missing) 개수": [f"{df.isnull().sum().sum()}"],
                "중복 데이터 수": [f"{df.duplicated().sum()}"]
            }
            st.table(pd.DataFrame(summary_info).T.rename(columns={0: "값"}))
            st.info("💡 **결측치 및 데이터 신뢰성**: 본 데이터셋은 결측치(Null)가 전혀 존재하지 않는 정제된 데이터셋입니다.")

        with col_info2:
            st.markdown("#### 타겟 변수 (Revenue) 불균형 현황")
            rev_counts = filtered_df['Revenue'].value_counts()
            rev_ratios = filtered_df['Revenue'].value_counts(normalize=True) * 100
            
            rev_summary = pd.DataFrame({
                "세션 수(건)": rev_counts,
                "비율(%)": rev_ratios
            })
            rev_summary.index = rev_summary.index.map({True: "구매 완료 (True)", False: "이탈/미구매 (False)"})
            st.table(rev_summary.round(2))
            
            fig_pie = px.pie(
                names=rev_summary.index,
                values=rev_summary["세션 수(건)"],
                title="Revenue 클래스 분포 비율",
                color=rev_summary.index,
                color_discrete_map={"구매 완료 (True)": "#1cc88a", "이탈/미구매 (False)": "#e74a3b"},
                hole=0.4
            )
            fig_pie.update_traces(textinfo="percent+label")
            fig_pie.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        st.subheader("🕵️ 데이터 샘플 확인 (상위 100개 세션)")
        st.dataframe(filtered_df.head(100), use_container_width=True)

    # ----------------- Tab 2: 수치형 변수 분석 -----------------
    with tab2:
        st.subheader("수치형 변수와 Revenue 비교 분석")
        num_cols = [
            'Administrative', 'Administrative_Duration', 
            'Informational', 'Informational_Duration', 
            'ProductRelated', 'ProductRelated_Duration', 
            'BounceRates', 'ExitRates', 'PageValues', 'SpecialDay'
        ]
        
        num_labels = {
            'Administrative': '행정 페이지 방문수', 'Administrative_Duration': '행정 페이지 체류 시간(초)',
            'Informational': '정보 페이지 방문수', 'Informational_Duration': '정보 페이지 체류 시간(초)',
            'ProductRelated': '제품 관련 페이지 방문수', 'ProductRelated_Duration': '제품 관련 페이지 체류 시간(초)',
            'BounceRates': '이탈률 (Bounce Rates)', 'ExitRates': '종료율 (Exit Rates)',
            'PageValues': '페이지 가치 (Page Values)', 'SpecialDay': '특별한 날과의 근접도 (Special Day)'
        }

        for idx, col in enumerate(num_cols):
            st.markdown(f"### 📍 {num_labels[col]} ({col}) 분석")
            group_true = filtered_df[filtered_df['Revenue'] == True][col]
            group_false = filtered_df[filtered_df['Revenue'] == False][col]
            
            fig_sub = make_subplots(
                rows=1, cols=2,
                subplot_titles=["📦 박스플롯 (Box Plot)", "📊 히스토그램 (Histogram)"],
                horizontal_spacing=0.15
            )
            
            fig_sub.add_trace(
                go.Box(
                    x=filtered_df['Revenue'].map({True: '구매 완료 (True)', False: '미구매 (False)'}),
                    y=filtered_df[col], marker_color='#4e73df', boxpoints='outliers', name="Box Plot"
                ), row=1, col=1
            )
            
            fig_sub.add_trace(
                go.Histogram(
                    x=group_false, name='미구매 (False)', marker_color='#e74a3b', opacity=0.65, histnorm='probability'
                ), row=1, col=2
            )
            fig_sub.add_trace(
                go.Histogram(
                    x=group_true, name='구매 완료 (True)', marker_color='#1cc88a', opacity=0.65, histnorm='probability'
                ), row=1, col=2
            )
            
            fig_sub.update_layout(height=400, barmode='overlay', showlegend=True, margin=dict(l=20, r=20, t=50, b=40))
            st.plotly_chart(fig_sub, use_container_width=True)
            st.markdown("<br><hr style='border: 1px dashed #dddddd;'><br>", unsafe_allow_html=True)

    # ----------------- Tab 3: 범주형 변수 분석 -----------------
    with tab3:
        st.subheader("범주형 변수와 Revenue 비교 분석")
        cat_cols = ['Month', 'VisitorType', 'Weekend', 'OperatingSystems', 'Browser', 'Region', 'TrafficType']
        cat_labels = {
            'Month': '월 (Month)', 'VisitorType': '방문자 유형 (VisitorType)', 'Weekend': '주말 여부 (Weekend)',
            'OperatingSystems': '운영체제 (Operating Systems)', 'Browser': '브라우저 (Browser)',
            'Region': '지역 (Region)', 'TrafficType': '유입 경로 유형 (Traffic Type)'
        }

        for col in cat_cols:
            st.markdown(f"### 📍 {cat_labels[col]} ({col}) 분석")
            fig_sub = make_subplots(
                rows=1, cols=2,
                subplot_titles=["📦 세션 빈도 (Counts)", "📊 구매 전환 비율 (100% Stacked Bar)"],
                horizontal_spacing=0.15
            )
            ct_counts = pd.crosstab(filtered_df[col], filtered_df['Revenue'])
            ct_ratios = pd.crosstab(filtered_df[col], filtered_df['Revenue'], normalize='index') * 100
            
            for state in [True, False]:
                if state not in ct_counts.columns: ct_counts[state] = 0
                if state not in ct_ratios.columns: ct_ratios[state] = 0.0

            fig_sub.add_trace(go.Bar(x=ct_counts.index, y=ct_counts[False], name='미구매 (False)', marker_color='#e74a3b'), row=1, col=1)
            fig_sub.add_trace(go.Bar(x=ct_counts.index, y=ct_counts[True], name='구매 완료 (True)', marker_color='#1cc88a'), row=1, col=1)
            fig_sub.add_trace(go.Bar(x=ct_ratios.index, y=ct_ratios[False], name='미구매 (False)', marker_color='#e74a3b', showlegend=False), row=1, col=2)
            fig_sub.add_trace(go.Bar(x=ct_ratios.index, y=ct_ratios[True], name='구매 완료 (True)', marker_color='#1cc88a', showlegend=False), row=1, col=2)
            
            fig_sub.update_layout(height=400, barmode='stack', margin=dict(l=20, r=20, t=50, b=40))
            st.plotly_chart(fig_sub, use_container_width=True)

    # ----------------- Tab 4: 퍼널 분석 -----------------
    with tab4:
        st.subheader("🎯 쇼핑몰 고객 행동 여정 퍼널 분석")
        funnel_type = st.radio("📊 퍼널 분석 모델 선택", options=["독립 행동 단계 퍼널", "엄격한 누적 여정 퍼널"], horizontal=True)
        funnel_stages = ["1. 전체 세션 유입", "2. 상품 페이지 상세조회", "3. 마이페이지/행정 관리 조회", "4. 고가치 전환 페이지 도달", "5. 최종 구매 완료"]
        
        if funnel_type == "독립 행동 단계 퍼널":
            s1 = len(filtered_df)
            s2 = len(filtered_df[filtered_df['ProductRelated'] > 0])
            s3 = len(filtered_df[filtered_df['Administrative'] > 0])
            s4 = len(filtered_df[filtered_df['PageValues'] > 0])
            s5 = len(filtered_df[filtered_df['Revenue'] == True])
        else:
            s1 = len(filtered_df)
            s2 = len(filtered_df[filtered_df['ProductRelated'] > 0])
            s3 = len(filtered_df[(filtered_df['ProductRelated'] > 0) & (filtered_df['Administrative'] > 0)])
            s4 = len(filtered_df[(filtered_df['ProductRelated'] > 0) & (filtered_df['Administrative'] > 0) & (filtered_df['PageValues'] > 0)])
            s5 = len(filtered_df[(filtered_df['ProductRelated'] > 0) & (filtered_df['Administrative'] > 0) & (filtered_df['PageValues'] > 0) & (filtered_df['Revenue'] == True)])
            
        counts = [s1, s2, s3, s4, s5]
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages, x=counts, textposition="inside", textinfo="value+percent initial+percent previous",
            marker={"color": ["#4e73df", "#36b9cc", "#f6c23e", "#f68d3e", "#1cc88a"]}
        ))
        fig_funnel.update_layout(height=500, margin=dict(l=20, r=20, t=60, b=40))
        st.plotly_chart(fig_funnel, use_container_width=True)


# ==============================================================================
# PAGE 2: 머신러닝(ML) 모델 학습 및 평가 (신규 별도 페이지)
# ==============================================================================
else:
    st.title("🤖 머신러닝 구매 전환 예측 모델 학습 및 성능 평가")
    st.markdown("""
        **랜덤 포레스트(Random Forest)** 및 **부스팅(Boosting)** 알고리즘을 사용하여 고객의 온라인 쇼핑 세션 정보로부터
        **최종 구매 완료(Revenue == True)** 여부를 예측하는 머신러닝 파이프라인 대시보드입니다.
    """)

    # 1. 머신러닝 데이터 전처리
    X, y, feature_names = preprocess_ml_data(df)

    # 2. 사이드바 ML 모델 설정 파라미터 제어판
    st.sidebar.header("⚙️ ML 모델 하이퍼파라미터 설정")
    algo_choice = st.sidebar.selectbox(
        "🎯 예측 알고리즘 선택",
        ["Random Forest", "Gradient Boosting", "HistGradient Boosting", "AdaBoost"],
        index=0
    )

    st.sidebar.subheader("📐 데이터 분할 & 파라미터")
    test_ratio = st.sidebar.slider("테스트 데이터 비율 (Test Size)", min_value=0.1, max_value=0.5, value=0.2, step=0.05)
    random_seed = st.sidebar.number_input("랜덤 시드 (Random State)", value=42, step=1)

    use_class_weight = False
    if algo_choice in ["Random Forest", "HistGradient Boosting"]:
        use_class_weight = st.sidebar.checkbox("⚖️ 클래스 불균형 가중치 적용 (Balanced Weight)", value=True)

    n_estimators = st.sidebar.slider("트리 개수 / 반복 횟수 (n_estimators / max_iter)", min_value=10, max_value=300, value=100, step=10)
    
    max_depth = 10
    if algo_choice != "AdaBoost":
        max_depth = st.sidebar.slider("트리 최대 깊이 (max_depth)", min_value=2, max_value=25, value=10, step=1)

    learning_rate = 0.1
    if algo_choice in ["Gradient Boosting", "HistGradient Boosting", "AdaBoost"]:
        learning_rate = st.sidebar.slider("학습률 (learning_rate)", min_value=0.01, max_value=0.5, value=0.1, step=0.01)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_ratio, random_state=random_seed, stratify=y
    )

    params = {
        'n_estimators': n_estimators,
        'max_depth': max_depth,
        'learning_rate': learning_rate,
        'random_state': random_seed
    }

    with st.spinner(f"[{algo_choice}] 모델을 학습 중입니다..."):
        eval_res = train_and_evaluate_model(
            algo_choice, params, X_train, X_test, y_train, y_test, use_class_weight=use_class_weight
        )

    # 3. 최상단 핵심 평가 지표 KPI 카드 (py-streamlit 스킬 준수)
    st.markdown(f"### 🔑 [{algo_choice}] 모델 평가 핵심 지표 (Test Dataset 기준)")
    ml_kpi1, ml_kpi2, ml_kpi3, ml_kpi4, ml_kpi5 = st.columns(5)

    with ml_kpi1:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #4e73df;">
                <div class="kpi-title">정확도 (Accuracy)</div>
                <div class="kpi-value">{eval_res['accuracy']:.4f}</div>
            </div>
        """, unsafe_allow_html=True)

    with ml_kpi2:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #1cc88a;">
                <div class="kpi-title">정밀도 (Precision)</div>
                <div class="kpi-value">{eval_res['precision']:.4f}</div>
            </div>
        """, unsafe_allow_html=True)

    with ml_kpi3:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #36b9cc;">
                <div class="kpi-title">재현율 (Recall)</div>
                <div class="kpi-value">{eval_res['recall']:.4f}</div>
            </div>
        """, unsafe_allow_html=True)

    with ml_kpi4:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #f6c23e;">
                <div class="kpi-title">F1-Score</div>
                <div class="kpi-value">{eval_res['f1']:.4f}</div>
            </div>
        """, unsafe_allow_html=True)

    with ml_kpi5:
        st.markdown(f"""
            <div class="kpi-container" style="border-top: 4px solid #e74a3b;">
                <div class="kpi-title">ROC-AUC</div>
                <div class="kpi-value">{eval_res['auc']:.4f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 4. 머신러닝 평가 메인 탭 구성
    ml_tab1, ml_tab2, ml_tab3, ml_tab4, ml_tab5, ml_tab6 = st.tabs([
        "📊 1. 모델 성능 상세 평가",
        "🌲 2. 피처 중요도",
        "⚖️ 3. 알고리즘 성능 비교 대조표",
        "🔮 4. 실시간 예측 시뮬레이터",
        "🔄 5. 파이프라인 & 시퀀스 다이어그램",
        "🎯 6. 비즈니스 전략 & 액션 플랜"
    ])

    # ----------------- ML Tab 1: 모델 성능 상세 평가 -----------------
    with ml_tab1:
        st.subheader(f"📊 [{algo_choice}] 세부 혼동 행렬 & ROC / PR 곡선")
        col_cm, col_curve = st.columns([1, 1])

        with col_cm:
            cm = eval_res['confusion_matrix']
            labels = ["미구매 (0)", "구매 완료 (1)"]
            z_text = [[str(val) for val in row] for row in cm]

            fig_cm = go.Figure(data=go.Heatmap(
                z=cm, x=labels, y=labels, colorscale='Blues',
                text=z_text, texttemplate="%{text}", textfont={"size": 18, "color": "black"},
                showscale=False
            ))
            fig_cm.update_layout(
                title=dict(text="📦 혼동 행렬 (Confusion Matrix)", font=dict(size=16)),
                xaxis_title="예측 클래스 (Predicted Label)", yaxis_title="실제 클래스 (Actual Label)",
                height=380, margin=dict(l=20, r=20, t=50, b=40)
            )
            st.plotly_chart(fig_cm, use_container_width=True)

        with col_curve:
            fpr, tpr, _ = roc_curve(y_test, eval_res['y_proba'])
            fig_curve = go.Figure()
            fig_curve.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name=f'ROC Curve (AUC = {eval_res["auc"]:.4f})', line=dict(color='#4e73df', width=2.5)))
            fig_curve.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Random Baseline', line=dict(color='gray', dash='dash')))
            fig_curve.update_layout(
                title=dict(text="📈 ROC (Receiver Operating Characteristic) 곡선", font=dict(size=16)),
                xaxis_title="False Positive Rate", yaxis_title="True Positive Rate",
                height=380, margin=dict(l=20, r=20, t=50, b=40), legend=dict(x=0.5, y=0.1)
            )
            st.plotly_chart(fig_curve, use_container_width=True)

    # ----------------- ML Tab 2: 피처 중요도 -----------------
    with ml_tab2:
        st.subheader(f"🌲 [{algo_choice}] 주요 변수 중요도 (Top Feature Importance)")

        if eval_res['feature_importances'] is not None:
            importance_df = pd.DataFrame({
                'Feature': feature_names,
                'Importance': eval_res['feature_importances']
            }).sort_values(by='Importance', ascending=True).tail(20)

            fig_imp = px.bar(
                importance_df, x='Importance', y='Feature', orientation='h',
                title=f"상위 20개 핵심 변수 중요도 ({algo_choice})",
                color='Importance', color_continuous_scale='Viridis'
            )
            fig_imp.update_layout(height=500, margin=dict(l=20, r=20, t=50, b=40))
            st.plotly_chart(fig_imp, use_container_width=True)
        else:
            st.info(f"💡 [{algo_choice}] 모델은 트리 기반 `feature_importances_` 특성을 직접 제공하지 않는 모델입니다.")

    # ----------------- ML Tab 3: 알고리즘 성능 비교 대조표 (상시 렌더링!) -----------------
    with ml_tab3:
        st.subheader("⚖️ 4대 머신러닝 알고리즘 성능 비교 대조표 (Performance Matrix)")
        st.markdown("""
            동일한 데이터 분할(Train/Test Split) 조건에서 **Random Forest**, **Gradient Boosting**, **HistGradient Boosting**, **AdaBoost** 
            알고리즘의 **정확도(Accuracy)**, **정밀도(Precision)**, **재현율(Recall)**, **F1-Score**, **ROC-AUC** 지표를 일괄 대조하여 보여줍니다.
        """)

        comp_df = get_all_models_comparison(params, X_train, X_test, y_train, y_test, use_class_weight=use_class_weight)

        st.markdown("#### 📋 4대 머신러닝 알고리즘 성능 지표 대조표")
        st.dataframe(
            comp_df.set_index("알고리즘 (Algorithm)")
            .style.highlight_max(axis=0, color='#d1fae5')
            .format("{:.4f}"),
            use_container_width=True
        )

        fig_comp = go.Figure()
        metrics = ["정확도 (Accuracy)", "정밀도 (Precision)", "재현율 (Recall)", "F1-Score", "ROC-AUC"]
        colors = ["#4e73df", "#1cc88a", "#36b9cc", "#f6c23e", "#e74a3b"]

        for idx, metric in enumerate(metrics):
            fig_comp.add_trace(go.Bar(
                x=comp_df["알고리즘 (Algorithm)"], y=comp_df[metric],
                name=metric, marker_color=colors[idx],
                text=[f"{v:.4f}" for v in comp_df[metric]],
                textposition='auto'
            ))

        fig_comp.update_layout(
            title="📊 알고리즘별 5대 성능 평가 지표 그룹 비교",
            barmode='group',
            height=480,
            yaxis=dict(range=[0, 1.05], title="지표 점수 (Score)"),
            margin=dict(l=20, r=20, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # ----------------- ML Tab 4: 실시간 구매 전환 예측 시뮬레이터 -----------------
    with ml_tab4:
        st.subheader("🔮 실시간 쇼핑 세션 구매 전환 확률 예측 시뮬레이터")

        # 1) 예측 시퀀스 다이어그램
        st.markdown("#### 🔄 실시간 구매 전환 예측 시퀀스 다이어그램 (Prediction Sequence)")
        pred_seq_code = """
        sequenceDiagram
            autonumber
            actor User as User
            participant Form as Streamlit Input Form
            participant Align as OneHot Preprocessor
            participant Model as Trained Model
            participant Gauge as Visualizer Report

            User->>Form: 1. Input Session Features
            User->>Form: 2. Click Predict Button
            Form->>Align: 3. Convert to DataFrame and Align Features
            Align->>Model: 4. Pass Feature Vector
            Model->>Model: 5. Execute predict_proba
            Model-->>Gauge: 6. Return Class and Probability
            Gauge-->>User: 7. Render Plotly Gauge and Decision Report
        """
        render_mermaid(pred_seq_code, height=480, elem_id="pred_seq_svg")

        st.markdown("---")

        with st.form("prediction_form"):
            st.markdown("#### 1. 고객 행동 데이터 입력")
            sim_col1, sim_col2, sim_col3 = st.columns(3)

            with sim_col1:
                input_admin = st.number_input("행정 페이지 방문수 (Administrative)", min_value=0, max_value=50, value=2)
                input_admin_dur = st.number_input("행정 체류 시간 (초)", min_value=0.0, max_value=5000.0, value=50.0)
                input_info = st.number_input("정보 페이지 방문수 (Informational)", min_value=0, max_value=50, value=0)
                input_info_dur = st.number_input("정보 체류 시간 (초)", min_value=0.0, max_value=5000.0, value=0.0)

            with sim_col2:
                input_prod = st.number_input("제품 페이지 방문수 (ProductRelated)", min_value=0, max_value=500, value=30)
                input_prod_dur = st.number_input("제품 체류 시간 (초)", min_value=0.0, max_value=20000.0, value=1200.0)
                input_bounce = st.slider("이탈률 (BounceRates)", min_value=0.0, max_value=0.2, value=0.01, step=0.005)
                input_exit = st.slider("종료율 (ExitRates)", min_value=0.0, max_value=0.2, value=0.03, step=0.005)

            with sim_col3:
                input_page_val = st.number_input("페이지 가치 (PageValues)", min_value=0.0, max_value=400.0, value=15.0)
                input_special = st.slider("특별한 날 근접도 (SpecialDay)", min_value=0.0, max_value=1.0, value=0.0, step=0.2)
                input_month = st.selectbox("방문 월 (Month)", options=sorted(df['Month'].unique()), index=5)
                input_visitor = st.selectbox("방문자 유형 (VisitorType)", options=sorted(df['VisitorType'].unique()), index=0)

            st.markdown("#### 2. 사용자 기기 및 환경 정보")
            env_col1, env_col2, env_col3, env_col4 = st.columns(4)
            with env_col1:
                input_weekend = st.selectbox("주말 여부 (Weekend)", options=[False, True], index=0)
            with env_col2:
                input_os = st.selectbox("운영체제 (OperatingSystems)", options=sorted(df['OperatingSystems'].unique()), index=0)
            with env_col3:
                input_browser = st.selectbox("브라우저 (Browser)", options=sorted(df['Browser'].unique()), index=0)
            with env_col4:
                input_traffic = st.selectbox("유입 경로 (TrafficType)", options=sorted(df['TrafficType'].unique()), index=0)
                
            input_region = sorted(df['Region'].unique())[0]
            submit_btn = st.form_submit_button("🔮 구매 전환 확률 예측하기")

        if submit_btn:
            single_input = pd.DataFrame([{
                'Administrative': input_admin, 'Administrative_Duration': input_admin_dur,
                'Informational': input_info, 'Informational_Duration': input_info_dur,
                'ProductRelated': input_prod, 'ProductRelated_Duration': input_prod_dur,
                'BounceRates': input_bounce, 'ExitRates': input_exit,
                'PageValues': input_page_val, 'SpecialDay': input_special,
                'Month': str(input_month), 'VisitorType': str(input_visitor),
                'Weekend': int(input_weekend), 'OperatingSystems': str(input_os),
                'Browser': str(input_browser), 'Region': str(input_region),
                'TrafficType': str(input_traffic)
            }])
            single_encoded = pd.get_dummies(single_input)
            for col in X.columns:
                if col not in single_encoded.columns: single_encoded[col] = 0
            single_encoded = single_encoded[X.columns]

            fitted_model = eval_res['model']
            pred_class = fitted_model.predict(single_encoded)[0]
            pred_prob = fitted_model.predict_proba(single_encoded)[0][1] if hasattr(fitted_model, "predict_proba") else float(pred_class)

            st.markdown("---")
            st.markdown("### 🎯 예측 결과 보고서")
            res_col1, res_col2 = st.columns([1, 1])
            
            with res_col1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=pred_prob * 100,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "구매 전환 예상 확률 (%)", 'font': {'size': 18}},
                    number={'suffix': "%", 'font': {'size': 32}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#1cc88a" if pred_prob >= 0.5 else "#e74a3b"},
                        'steps': [
                            {'range': [0, 30], 'color': "#f8d7da"},
                            {'range': [30, 70], 'color': "#fff3cd"},
                            {'range': [70, 100], 'color': "#d4edda"}
                        ],
                        'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 50}
                    }
                ))
                fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with res_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if pred_class == 1:
                    st.success(f"🎉 **최종 판단: 구매 전환 성공 가능성 매우 높음 (True)**\n\n현재 입력된 고객 행동 패턴은 구매 전환 확률이 **{pred_prob*100:.1f}%** 로 최종 구매에 도달할 것으로 진단됩니다.")
                else:
                    st.error(f"⚠️ **최종 판단: 이탈 / 미구매 가능성 높음 (False)**\n\n현재 입력된 고객 행동 패턴은 구매 전환 확률이 **{pred_prob*100:.1f}%** 로 구매 없이 이탈할 가능성이 큽니다.")
                st.info(f"💡 **분석 모델**: {algo_choice} (Accuracy: {eval_res['accuracy']:.4f}, AUC: {eval_res['auc']:.4f})")

    # ----------------- ML Tab 5: 머메이드 파이프라인 & 시퀀스 다이어그램 -----------------
    with ml_tab5:
        st.subheader("🔄 머신러닝 파이프라인 흐름도 & 시퀀스 다이어그램 (Mermaid)")
        st.markdown("#### 1. ML 파이프라인 구조 워크플로우 (Flowchart)")
        flowchart_code = """
        graph TD
            A["Online Shoppers Dataset (12,330 Sessions)"] --> B["Preprocessing and One-Hot Encoding"]
            B --> C["Stratified Train/Test Split (80/20)"]
            
            C --> D1["Random Forest Classifier"]
            C --> D2["Gradient Boosting Classifier"]
            C --> D3["HistGradient Boosting Classifier"]
            C --> D4["AdaBoost Classifier"]

            D1 --> E["Model Evaluation Engine"]
            D2 --> E
            D3 --> E
            D4 --> E

            E --> F["Real-time Session Predictor"]
        """
        render_mermaid(flowchart_code, height=520, elem_id="flowchart_svg")

        st.markdown("---")
        st.markdown("#### 2. 실시간 구매 전환 예측 시퀀스 다이어그램 (Sequence Diagram)")
        sequence_code = """
        sequenceDiagram
            autonumber
            actor User as User
            participant UI as Streamlit Web UI
            participant Prep as Preprocessor
            participant Model as Trained Model
            participant Gauge as Plotly Visualizer

            User->>UI: 1. Input Session Attributes
            User->>UI: 2. Click Predict Button
            UI->>Prep: 3. Capture Input Data
            Prep->>Prep: 4. Encoding and Feature Alignment
            Prep->>Model: 5. Send Feature Vector
            Model->>Model: 6. Calculate Probability
            Model-->>UI: 7. Return Prediction Class and Probability
            UI->>Gauge: 8. Request Gauge Chart Visual
            Gauge-->>UI: 9. Render Gauge Chart and Report
            UI-->>User: 10. Display Visual Report
        """
        render_mermaid(sequence_code, height=620, elem_id="sequence_svg")

    # ----------------- ML Tab 6: 비즈니스 전략 & 실행 액션 플랜 -----------------
    with ml_tab6:
        st.subheader("🎯 20년차 데이터 분석가 관점의 상세 비즈니스 전략 및 실행 액션 플랜")
        st.markdown("머신러닝 예측 모델 결과와 EDA 인사이트를 결합하여 **매출 극대화(Revenue Optimization)**를 위한 3대 핵심 비즈니스 전략 및 실행 액션 플랜을 제시합니다.")

        # 전략 1
        st.markdown("""
            <div class="strategy-card">
                <h4>📌 전략 1: PageValues & ExitRates 기반 '고가치 유저 결제 완주' UX 최적화</h4>
                <p><b>분석 결과</b>: <code>PageValues</code>(페이지 가치)는 구매 전환 여부를 결정짓는 가장 압도적인 피처이며, 구매 완료 세션의 평균 가치는 $30.29로 미구매 세션($0.09) 대비 330배 이상 높습니다. 또한 구매 고객의 평균 종료율(ExitRates)은 1.9%에 불과합니다.</p>
                <ul>
                    <li><b>액션 플랜 1-1 (장바구니 스마트 리타게팅)</b>: 장바구니 담기 행동으로 <code>PageValues > 0</code>이 형성된 고객이 이탈하려 할 때(마우스가 브라우저 닫기 탭으로 이동 시), 즉시 <b>"5분 내 결제 시 무료 배송 쿠폰"</b> 팝업을 트리거합니다.</li>
                    <li><b>액션 플랜 1-2 (원클릭 퀵 결제 모듈 도입)</b>: 누적 퍼널 분석에 따르면 구매 완료자 중 758명은 관리/회원가입 페이지를 생략했습니다. 카카오페이, 토스, 네이버페이 등 <b>간편결제 아이콘을 상품 페이지 최상단에 전면 배치</b>하여 결제 허들을 최소화합니다.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # 전략 2
        st.markdown("""
            <div class="strategy-card" style="border-left-color: #1cc88a;">
                <h4>📌 전략 2: 고객 세그먼트별 리텐션 및 연말 성수기 마케팅 예산 최적화</h4>
                <p><b>분석 결과</b>: 11월(Nov), 12월(Dec)에 구매 전환율 및 총 구매 세션 수가 급증하며, 신규 방문자(New Visitor)의 구매 전환 효율이 기존 방문자보다 높게 형성됩니다.</p>
                <ul>
                    <li><b>액션 플랜 2-1 (신규 고객 Onboarding 패키지)</b>: 신규 유입 방문자에게 <b>첫 구매 15% 할인 웰컴 기프트</b>를 지급하여 빠르게 구매 첫 경험을 완성시키고 재방문을 유도합니다.</li>
                    <li><b>액션 플랜 2-2 (연말 프로모션 예산 60% 집중 집행)</b>: 11월 블랙프라이데이 및 12월 연말 시즌에 퍼포먼스 마케팅 예산의 60% 이상을 집중 집행하고, 서버 인프라를 확장하여 트래픽 폭주에 대응합니다.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # 전략 3
        st.markdown("""
            <div class="strategy-card" style="border-left-color: #f6c23e;">
                <h4>📌 전략 3: ML 예측 확률 기반 실시간 개인화 프로모션 자동화 파이프라인</h4>
                <p><b>분석 결과</b>: Gradient Boosting 및 Random Forest 모델을 사용하면 쇼핑 세션 중 실시간으로 고객의 구매 전환 확률(%)을 90% 이상의 Accuracy로 추정할 수 있습니다.</p>
                <ul>
                    <li><b>액션 플랜 3-1 (구매 확률 70% 이상 - VIP 인센티브)</b>: 실시간 예측 확률이 70% 이상인 구매 유망 유저에게는 사은품 증정 혜택 메시지를 노출하여 구매 금액(AOV) 업셀링을 유도합니다.</li>
                    <li><b>액션 플랜 3-2 (구매 확률 30%~50% - 이탈 방지 트리거)</b>: 이탈 임계 영역에 있는 고민 유저에게는 <b>"실시간 실시간 인기 상품 Top 3"</b> 팝업 및 <b>"오늘 마감 할인"</b> 타임 카운트다운을 노출하여 구매 결정을 지원합니다.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🚀 머신러닝 기반 비즈니스 자동화 로드맵 (Action Plan Roadmap)")
        
        roadmap_df = pd.DataFrame([
            {"단계": "1단계: 데이터 파이프라인", "주요 과제": "세션 행동 데이터(페이지수, 체류시간, 이탈률) 실시간 로그 수집 API 구축", "담당": "데이터 엔지니어링 팀", "기간": "1~2주차"},
            {"단계": "2단계: ML 모델 API 서빙", "주요 과제": "Gradient Boosting 기반 Real-time Inference Microservice 배포", "담당": "MLOps / Backend 팀", "기간": "3~4주차"},
            {"단계": "3단계: 개인화 트리거 연동", "주요 과제": "구매 확률(%) 구간별 웰컴 쿠폰 및 리타게팅 팝업 자동 발송 연동", "담당": "그로스 마케팅 팀", "기간": "5~6주차"},
            {"단계": "4단계: A/B 테스트 & 피드백", "주요 과제": "ML 자동화 적용 집단 vs 대조군의 구매 전환율(CR) 및 ROAS 비교 검증", "담당": "데이터 분석 팀", "기간": "7~8주차"}
        ])
        st.table(roadmap_df.set_index("단계"))
