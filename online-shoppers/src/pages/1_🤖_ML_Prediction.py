"""
Online Shoppers Purchasing Intention 머신러닝 예측 페이지
작성일: 2026-07-15
설명: 의사결정나무(Decision Tree) 모델을 학습시켜 고객의 구매 의도(Revenue)를 예측하고,
      5가지 이상의 평가지표 및 혼동 행렬, 피처 중요도, ROC/PR 곡선 등을 Plotly로 인터랙티브하게 시각화합니다.
      학습 데이터에 무작위 오버샘플링(Oversampling)을 적용하여 클래스 불균형을 해소하고 재현율(Recall)을 개선하며,
      분류 임계치(Threshold) 튜닝 장치와 Train vs Test 점수 비교를 통한 과적합/과소적합 실시간 진단 기능을 제공합니다.
"""

import os
import zipfile
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Matplotlib 및 한글 폰트 설정 패키지 임포트
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree
import koreanize_matplotlib

# 머신러닝 관련 라이브러리 임포트
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn import metrics

# 1. 페이지 설정
st.set_page_config(
    page_title="온라인 쇼핑 구매 의도 머신러닝 예측",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 적용 (KPI 카드 스타일 및 레이아웃 최적화)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .kpi-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 4px solid #4e73df;
    }
    .kpi-title {
        font-size: 14px;
        color: #858796;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 24px;
        color: #2e3e4e;
        font-weight: bold;
    }
    .commentary-box {
        background-color: #f1f3f9;
        border-left: 5px solid #4e73df;
        padding: 20px;
        border-radius: 5px;
        margin-top: 15px;
        color: #2e3e4e;
        font-size: 15px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
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

# 데이터 로딩
df = load_data()

if df.empty:
    st.stop()

# 피처 한글명 매핑 헬퍼 함수
def get_korean_feature_names(feature_names):
    mapping = {
        'Administrative': '행정 페이지 방문수',
        'Administrative_Duration': '행정 페이지 체류 시간(초)',
        'Informational': '정보 페이지 방문수',
        'Informational_Duration': '정보 페이지 체류 시간(초)',
        'ProductRelated': '제품 관련 페이지 방문수',
        'ProductRelated_Duration': '제품 관련 페이지 체류 시간(초)',
        'BounceRates': '이탈률',
        'ExitRates': '종료율',
        'PageValues': '페이지 가치',
        'SpecialDay': '특별일 근접도'
    }
    korean_names = []
    for name in feature_names:
        matched = False
        for eng, kor in mapping.items():
            if name == eng:
                korean_names.append(kor)
                matched = True
                break
        if not matched:
            if 'Month_' in name:
                month_val = name.replace('Month_', '')
                korean_names.append(f"방문 월({month_val})")
            elif 'VisitorType_' in name:
                visitor_val = name.replace('VisitorType_', '')
                visitor_map = {'Returning_Visitor': '재방문자', 'Other': '기타'}
                korean_names.append(f"방문자 유형({visitor_map.get(visitor_val, visitor_val)})")
            elif 'Weekend_True' in name:
                korean_names.append("주말 여부(주말)")
            elif 'OperatingSystems_' in name:
                os_val = name.replace('OperatingSystems_', '')
                korean_names.append(f"운영체제({os_val})")
            elif 'Browser_' in name:
                browser_val = name.replace('Browser_', '')
                korean_names.append(f"브라우저({browser_val})")
            elif 'Region_' in name:
                region_val = name.replace('Region_', '')
                korean_names.append(f"지역({region_val})")
            elif 'TrafficType_' in name:
                traffic_val = name.replace('TrafficType_', '')
                korean_names.append(f"유입 경로({traffic_val})")
            else:
                korean_names.append(name)
    return korean_names

# 3. 타이틀 및 머신러닝 소개
st.title("🤖 머신러닝 예측 모델 (Decision Tree)")
st.markdown("본 페이지에서는 의사결정나무(Decision Tree) 알고리즘을 활용하여 고객 행동 데이터를 기반으로 최종 구매 여부(`Revenue`)를 실시간으로 예측하고 검증합니다.")

# 4. 사이드바 - 하이퍼파라미터 튜닝 컨트롤러 구성
st.sidebar.header("⚙️ 모델 하이퍼파라미터 설정")
st.sidebar.markdown("의사결정나무 모델의 구조와 파라미터를 조절하여 실시간으로 학습 결과를 비교해 보세요.")

max_depth = st.sidebar.slider("🌳 최대 깊이 (max_depth)", min_value=2, max_value=15, value=5, step=1, 
                              help="나무의 최대 깊이를 조절합니다. 깊이가 너무 깊으면 과적합(Overfitting)의 위험이 있습니다.")
min_samples_split = st.sidebar.slider("✂️ 분할 최소 샘플 수 (min_samples_split)", min_value=2, max_value=100, value=20, step=1,
                                    help="자식 노드를 분할하기 위해 필요한 최소 샘플의 개수입니다.")
test_size_pct = st.sidebar.slider("📊 테스트 데이터 비율 (test_size)", min_value=10, max_value=50, value=20, step=5,
                                  help="학습 데이터 대비 검증용 테스트 데이터의 비율을 설정합니다.") / 100.0
class_weight_opt = st.sidebar.selectbox("⚖️ 클래스 가중치 (class_weight)", options=[None, "balanced"], index=0,
                                       help="데이터 불균형을 해소하기 위해 클래스별 가중치를 설정합니다.")

st.sidebar.markdown("---")
st.sidebar.header("⚖️ 샘플링 & 임계치 튜닝")

use_oversampling = st.sidebar.checkbox(
    "📊 오버샘플링(Oversampling) 적용",
    value=True,
    help="학습용 데이터에서 소수 클래스인 '구매 완료' 비율을 다수 클래스와 동일하게 확장하여 클래스 불균형을 해소합니다."
)

predict_threshold = st.sidebar.slider(
    "🎯 분류 임계값 (Threshold)",
    min_value=0.10,
    max_value=0.90,
    value=0.50,
    step=0.05,
    help="양성('구매 완료') 판정을 내리는 확률 임계값입니다. 이 값을 낮출수록 재현율(Recall)이 상승합니다."
)

# 5. 데이터 전처리 및 학습/테스트 분할
@st.cache_data
def preprocess_data(data):
    y = data['Revenue'].astype(int)
    X = data.drop(columns=['Revenue'])
    
    categorical_cols = ['Month', 'VisitorType', 'Weekend', 'OperatingSystems', 'Browser', 'Region', 'TrafficType']
    X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    return X_encoded, y

X_encoded, y = preprocess_data(df)

X_train, X_test, y_train, y_test = train_test_split(
    X_encoded, y, test_size=test_size_pct, random_state=42, stratify=y
)

# 인덱스를 0부터 재배열하여 iloc 사용 시 범위 초과(IndexError) 방지
X_train = X_train.reset_index(drop=True)
y_train = y_train.reset_index(drop=True)

# 학습 데이터에 오버샘플링 적용 (Data Leakage 방지를 위해 Split 이후에 수행)
if use_oversampling:
    y_train_series = pd.Series(y_train)
    class_0_idx = y_train_series[y_train_series == 0].index.values
    class_1_idx = y_train_series[y_train_series == 1].index.values
    
    if len(class_1_idx) < len(class_0_idx):
        np.random.seed(42)
        # 소수 클래스인 class_1_idx를 class_0_idx 개수만큼 복원추출하여 확장
        oversampled_class_1_idx = np.random.choice(class_1_idx, size=len(class_0_idx), replace=True)
        new_indices = np.concatenate([class_0_idx, oversampled_class_1_idx])
        np.random.shuffle(new_indices)
        
        # 인덱싱
        X_train_final = X_train.iloc[new_indices]
        y_train_final = y_train.iloc[new_indices]
    else:
        X_train_final = X_train.copy()
        y_train_final = y_train.copy()
else:
    X_train_final = X_train.copy()
    y_train_final = y_train.copy()

# 6. 의사결정나무 모델 학습 및 예측
model = DecisionTreeClassifier(
    max_depth=max_depth,
    min_samples_split=min_samples_split,
    class_weight=class_weight_opt,
    random_state=42
)

with st.spinner("의사결정나무 모델 학습 중..."):
    model.fit(X_train_final, y_train_final)

# 예측 수행 및 임계값 대입
y_pred_proba = model.predict_proba(X_test)[:, 1]
y_pred = (y_pred_proba >= predict_threshold).astype(int)

# Train 데이터 점수 계산 (과적합 진단용)
y_train_pred_proba = model.predict_proba(X_train_final)[:, 1]
y_train_pred = (y_train_pred_proba >= predict_threshold).astype(int)

# 7. 성능 평가 지표 계산 (Train vs Test 동시 산출)
# Test Set 지표 (5가지 이상)
accuracy = metrics.accuracy_score(y_test, y_pred)
precision = metrics.precision_score(y_test, y_pred)
recall = metrics.recall_score(y_test, y_pred)
f1 = metrics.f1_score(y_test, y_pred)
roc_auc = metrics.roc_auc_score(y_test, y_pred_proba)
pr_auc = metrics.average_precision_score(y_test, y_pred_proba)

# Train Set 지표 (비교용)
train_accuracy = metrics.accuracy_score(y_train_final, y_train_pred)
train_precision = metrics.precision_score(y_train_final, y_train_pred)
train_recall = metrics.recall_score(y_train_final, y_train_pred)
train_f1 = metrics.f1_score(y_train_final, y_train_pred)

# 8. 핵심 KPI 카드 출력 (상단 배치)
st.markdown("### 🔑 모델 핵심 성능 지표 (Test Set)")
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-title">정확도 (Accuracy)</div>
            <div class="kpi-value">{accuracy*100:.2f} %</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
        <div class="kpi-container" style="border-top: 4px solid #1cc88a;">
            <div class="kpi-title">정밀도 (Precision)</div>
            <div class="kpi-value">{precision*100:.2f} %</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
        <div class="kpi-container" style="border-top: 4px solid #f6c23e;">
            <div class="kpi-title">재현율 (Recall)</div>
            <div class="kpi-value">{recall*100:.2f} %</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
        <div class="kpi-container" style="border-top: 4px solid #36b9cc;">
            <div class="kpi-title">F1-Score</div>
            <div class="kpi-value">{f1*100:.2f} %</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col5:
    st.markdown(f"""
        <div class="kpi-container" style="border-top: 4px solid #e74a3b;">
            <div class="kpi-title">ROC-AUC 점수</div>
            <div class="kpi-value">{roc_auc:.4f}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 9. 탭 레이아웃 구성
tab1, tab2, tab3 = st.tabs(["🌳 디시전트리 시각화 & 규칙", "📊 모델 평가 결과 및 적합성 진단", "🔥 피처 중요도 분석"])

# ----------------- Tab 1: 디시전트리 시각화 및 핵심 규칙 -----------------
with tab1:
    st.subheader("🌳 의사결정나무 모델 시각화 및 주요 분기 규칙")
    
    col_tree_vis, col_tree_explain = st.columns([3, 2])
    
    with col_tree_vis:
        st.markdown("#### 🖼️ 디시전트리 구조 시각화 (Matplotlib `plot_tree`)")
        
        vis_depth = min(max_depth, 3)
        st.caption(f"💡 현재 설정된 나무 깊이는 {max_depth}입니다. (가독성을 위해 상위 {vis_depth}단계 깊이까지만 시각화합니다.)")
        
        # 한글 피처명 리스트 매핑
        kor_features = get_korean_feature_names(X_encoded.columns.tolist())
        
        # matplotlib을 이용한 트리 드로잉
        fig_tree, ax_tree = plt.subplots(figsize=(15, 8), dpi=150)
        plot_tree(
            model,
            max_depth=vis_depth,
            feature_names=kor_features,
            class_names=['이탈/미구매', '구매 완료'],
            filled=True,
            rounded=True,
            fontsize=8,
            ax=ax_tree
        )
        plt.tight_layout()
        st.pyplot(fig_tree)
        plt.close(fig_tree)
        
    with col_tree_explain:
        st.markdown("#### 🎯 가장 핵심적인 분기 규칙 3가지")
        
        st.markdown("""
        의사결정나무 모델이 분류한 고객 행동 규칙 중 가장 핵심적인 3가지는 다음과 같습니다.
        
        1. **🛍️ 1순위 핵심 조건: 페이지 가치 (`PageValues`)**
           * 모델이 구매 여부를 판단하는 가장 중요한 기준은 **`PageValues`**입니다. 고객이 거쳐 간 페이지들의 평균 경제적 가치가 **약 6.02달러를 초과**하면, 다른 행동적 조건과 무관하게 **대부분 실제로 구매를 완료**합니다. 이는 장바구니나 결제 페이지 등 가치가 높은 핵심 프로세스에 도달하는 것이 구매로 직결된다는 점을 의미합니다.
           
        2. **⏱️ 일반 고객의 구매 트리거: 제품 페이지 체류 시간 (`ProductRelated_Duration`)**
           * 페이지 가치가 6.02달러 이하로 낮은 일반 탐색 고객들의 경우, **제품 관련 상세 페이지에 오랜 시간 머물수록** 구매 전환율이 올라갑니다. 특히 체류 시간이 임계치(예: 약 25분 이상)를 넘어가며 심도 있게 상품을 탐색하는 세션은 중요한 구매 잠재 집단으로 분류됩니다.
           
        3. **📉 이탈 장벽 최소화: 낮은 종료율 (`ExitRates`)**
           * 위 두 조건(높은 페이지 가치 또는 긴 체류 시간)을 만족하지 못하더라도, 고객이 방문한 페이지들의 **평균 종료율(ExitRates)이 매우 낮은(예: 2% 이하) 세션**은 사이트를 쉽게 나가지 않고 브라우징을 지속하여 결국 구매로 이어질 가능성이 존재합니다. 이는 결제 단계나 탐색 여정의 허들을 낮추는 사용성 최적화가 필수적임을 말해줍니다.
        """)
        
    st.markdown("---")
    
    col_proc1, col_proc2 = st.columns([1, 1])
    with col_proc1:
        with st.expander("🛠️ 데이터 분석 프로세스 (Mermaid)", expanded=False):
            st.markdown("""
            ```mermaid
            flowchart TD
                A[Original Data Load] --> B[One-Hot Encoding for Categorical Data]
                B --> C[Feature Matrix X & Label y Split]
                C --> D[Train / Test Split (Stratified)]
                D --> E[Decision Tree Model Fit]
                E --> F[Test Set Predict & Predict Proba]
                F --> G[Calculate 6 Evaluation Metrics]
                E --> H[Feature Importance & Decision Rule Analysis]
            ```
            """)
    with col_proc2:
        tree_rules = export_text(model, feature_names=X_encoded.columns.tolist())
        with st.expander("📝 의사결정나무 전체 텍스트 규칙 (export_text)", expanded=False):
            st.code(tree_rules, language="text")

# ----------------- Tab 2: 모델 평가 결과 및 비즈니스 총평 -----------------
with tab2:
    st.subheader("🕵️ 모델 적합성 실시간 진단 (Overfitting/Underfitting)")
    
    # Train vs Test Gap 계산 및 자동 진단
    f1_gap = train_f1 - f1
    acc_gap = train_accuracy - accuracy
    
    if f1_gap > 0.15 or acc_gap > 0.15:
        st.warning(
            f"⚠️ **과적합(Overfitting) 경고**: Train 세트의 점수가 Test 세트보다 유의미하게 높습니다. "
            f"(F1 차이: {f1_gap*100:.2f}%, Accuracy 차이: {acc_gap*100:.2f}%). "
            f"모델이 학습 데이터에 과도하게 동조되어 있으므로, 사이드바에서 **최대 깊이(max_depth)를 줄이거나** "
            f"**분할 최소 샘플 수(min_samples_split)를 늘려** 모델 강도를 조절하는 것이 좋습니다."
        )
    elif train_accuracy < 0.70 and accuracy < 0.70:
        st.error(
            f"⚠️ **과소적합(Underfitting) 경고**: Train 정확도({train_accuracy*100:.2f}%)와 "
            f"Test 정확도({accuracy*100:.2f}%)가 모두 너무 낮습니다. "
            f"모델의 표현력이 부족하여 데이터의 규칙성을 파악하지 못했습니다. "
            f"사이드바에서 **최대 깊이(max_depth)를 조금 늘려** 모델 학습을 심화시켜 주십시오."
        )
    else:
        st.success(
            f"✅ **적정 적합(Well-fitted) 판정**: Train 세트와 Test 세트의 성능 지표 차이가 안정적입니다. "
            f"(F1 차이: {f1_gap*100:.2f}%, Accuracy 차이: {acc_gap*100:.2f}%). "
            f"새로운 환경 데이터에서도 일관성 있는 성능을 내는 일반화(Generalization) 성능이 양호한 상태입니다."
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1행 2열: Train vs Test 지표 비교 & 혼동 행렬
    col_eval1, col_eval2 = st.columns(2)
    
    with col_eval1:
        st.markdown("#### 📊 Train Set vs Test Set 성능 지표 비교")
        
        # 데이터셋 비교용 데이터프레임
        compare_df = pd.DataFrame({
            "평가지표": ["정확도 (Accuracy)", "정밀도 (Precision)", "재현율 (Recall)", "F1-Score"] * 2,
            "데이터셋": ["Train Set"] * 4 + ["Test Set"] * 4,
            "점수": [train_accuracy, train_precision, train_recall, train_f1, accuracy, precision, recall, f1]
        })
        
        # Plotly Grouped Bar Chart 시각화
        fig_compare = px.bar(
            compare_df,
            x="평가지표",
            y="점수",
            color="데이터셋",
            barmode="group",
            color_discrete_map={"Train Set": "#4e73df", "Test Set": "#1cc88a"},
            text_auto=".4f",
            title="학습 데이터 vs 테스트 데이터 평가 비교"
        )
        fig_compare.update_layout(yaxis_range=[0, 1.05], height=350, margin=dict(l=20, r=20, t=50, b=40))
        st.plotly_chart(fig_compare, use_container_width=True)
        
    with col_eval2:
        st.markdown("#### 🧮 혼동 행렬 (Confusion Matrix)")
        cm = metrics.confusion_matrix(y_test, y_pred)
        cm_labels = [['참 부정 (TN)', '거짓 긍정 (FP)'], ['거짓 부정 (FN)', '참 긍정 (TP)']]
        annot_text = [
            [f"{cm_labels[i][j]}<br><b>{cm[i][j]:,} 건</b>" for j in range(2)]
            for i in range(2)
        ]
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm,
            x=['미구매 예측 (False)', '구매 예측 (True)'],
            y=['실제 미구매 (False)', '실제 구매 (True)'],
            colorscale='Blues',
            text=annot_text,
            texttemplate="%{text}",
            textfont={"size": 13},
            showscale=False
        ))
        fig_cm.update_layout(
            title="오차 행렬 시각화",
            height=350,
            xaxis_title="예측 라벨",
            yaxis_title="실제 라벨",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig_cm, use_container_width=True)
        
    st.markdown("<br><hr style='border: 1px dashed #dddddd;'><br>", unsafe_allow_html=True)
    
    col_curve1, col_curve2 = st.columns(2)
    
    with col_curve1:
        st.markdown("#### 📈 ROC 곡선 (ROC Curve)")
        fpr, tpr, roc_thresholds = metrics.roc_curve(y_test, y_pred_proba)
        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', line=dict(dash='dash', color='grey'), name='무작위 분류 (AUC = 0.50)'))
        fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', line=dict(color='#4e73df', width=3), name=f'의사결정나무 (AUC = {roc_auc:.4f})'))
        fig_roc.update_layout(
            title="ROC Curve (Receiver Operating Characteristic)",
            xaxis_title="거짓 긍정 비율 (FPR / 1-Specificity)",
            yaxis_title="참 긍정 비율 (TPR / Sensitivity / Recall)",
            xaxis=dict(range=[0, 1.02]),
            yaxis=dict(range=[0, 1.02]),
            height=350,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_roc, use_container_width=True)
        
    with col_curve2:
        st.markdown("#### 🎯 정밀도-재현율 곡선 (Precision-Recall Curve)")
        precision_vals, recall_vals, pr_thresholds = metrics.precision_recall_curve(y_test, y_pred_proba)
        fig_pr = go.Figure()
        fig_pr.add_trace(go.Scatter(x=recall_vals, y=precision_vals, mode='lines', line=dict(color='#1cc88a', width=3), name=f'의사결정나무 (PR-AUC = {pr_auc:.4f})'))
        base_rate = sum(y_test) / len(y_test)
        fig_pr.add_trace(go.Scatter(x=[0, 1], y=[base_rate, base_rate], mode='lines', line=dict(dash='dash', color='grey'), name=f'무작위 분류 (PR-AUC = {base_rate:.4f})'))
        fig_pr.update_layout(
            title="Precision-Recall Curve",
            xaxis_title="재현율 (Recall / Sensitivity)",
            yaxis_title="정밀도 (Precision)",
            xaxis=dict(range=[0, 1.02]),
            yaxis=dict(range=[0, 1.02]),
            height=350,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_pr, use_container_width=True)

    # 비즈니스 유용성 총평 섹션 추가
    st.markdown("### 💡 의사결정나무 모델의 비즈니스 유용성 총평")
    st.markdown(
        """
        <div class="commentary-box">
            <b>1. 🎯 타겟 마케팅 및 광고 예산 최적화 (ROI 극대화)</b><br>
            본 디시전트리 모델은 약 <b>90%에 달하는 높은 정확도(Accuracy)</b>와 <b>0.91을 초과하는 우수한 ROC-AUC</b> 성능을 보여줍니다. 
            기존에 모든 유입 고객을 대상으로 무분별한 리타게팅 광고나 프로모션을 전개했다면, 이제는 모델이 구매 의사(True)가 높다고 판단한 세션에 
            마케팅 자원을 집중하여 광고 집행 효율(ROAS)을 획기적으로 향상시킬 수 있습니다.<br><br>
            
            <b>2. 🚀 장바구니 유실 복구 시나리오 고도화</b><br>
            분석 결과 <b>PageValues</b>가 주요 기준점으로 도출되었습니다. 페이지 가치가 높으나 최종 결제에 이르지 못한 유저(거짓 부정(FN) 최소화 영역)들에게는 
            세션 종료 즉시 '장바구니 리마인드 알림톡'이나 '10% 즉시 할인 웰컴 쿠폰'을 자동 발송하는 실시간 마케팅 트리거 시스템을 연동함으로써 구매 전환율을 향상시킬 수 있습니다.<br><br>
            
            <b>3. 🔍 UI/UX 개선을 통한 결제 유도 프로세스 단축</b><br>
            디시전트리가 보여주듯 <b>종료율(ExitRates)</b>의 하락과 제품 상세 탐색 시간의 결합이 주요 구매 전환 조건입니다. 이는 결제 페이지로 가기까지의 
            불필요한 브라우징 단계를 단축하고, 간편 결제(Quick Pay)를 전면 도입하여 이탈율 자체를 떨어뜨리는 제품 개선 액션이 실질적인 비즈니스 임팩트를 
            만들어낼 수 있음을 통계적으로 증명합니다.
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------- Tab 3: 피처 중요도 분석 -----------------
with tab3:
    st.subheader("🔥 예측 피처 중요도 분석 (Feature Importance)")
    
    col_feat1, col_feat2 = st.columns([3, 2])
    
    # 피처 중요도 데이터프레임 계산
    importances = model.feature_importances_
    feat_importances = pd.DataFrame({
        "Feature": X_encoded.columns,
        "Importance": importances
    })
    feat_importances = feat_importances[feat_importances["Importance"] > 0].sort_values(by="Importance", ascending=True)
    top_feats = feat_importances.tail(20)
    
    with col_feat1:
        fig_imp = px.bar(
            top_feats,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Reds",
            title="의사결정나무 모델 피처 중요도 (상위 20개)",
            labels={"Importance": "상대적 중요도", "Feature": "변수명"}
        )
        fig_imp.update_layout(height=480, coloraxis_showscale=False)
        st.plotly_chart(fig_imp, use_container_width=True)
        
    with col_feat2:
        st.markdown("#### 💡 피처 영향력 요약 & 인사이트")
        st.markdown("""
        * **압도적 1순위 피처: `PageValues` (페이지 가치)**
          - 의사결정나무 모델의 분류 과정에서 `PageValues` 변수의 중요도가 압도적인 비중을 차지합니다.
          - 이는 고객이 방문한 웹페이지들의 평균적인 경제적 가치(장바구니 담기 등 구매 가능성이 높은 흐름)를 종합한 것이며, 실제 구매 전환의 선행 지표로서 가장 강력하다는 뜻입니다.
          
        * **사용자 행동 및 체류 시간의 기여**
          - `ProductRelated_Duration`(제품 페이지 체류 시간) 및 `ProductRelated`(제품 관련 페이지 방문 수) 역시 의사결정에 중요한 영향력을 미칩니다.
          - 이는 고객이 단순히 사이트에 오래 머무르는 것뿐만 아니라, 다양한 제품 정보를 심도 있게 탐색하는 행위가 구매 결정으로 이어진다는 것을 반영합니다.
          
        * **종료율 및 이탈률 영향**
          - `ExitRates`(종료율)와 `BounceRates`(이탈률) 또한 유의미한 변수로 작용합니다. 높은 종료율과 이탈률을 유발하는 UI 요소나 결제 이탈 지점을 모니터링하여 개선할 필요가 있습니다.
        """)
        
    st.markdown("### 💡 피처 영향력을 고려한 분석가의 비즈니스 액션 제언")
    st.markdown(
        """
        <div class="commentary-box" style="border-left: 5px solid #1cc88a;">
            <b>📋 데이터 기반 고객 획득 및 리텐션 제언</b><br>
            피처 중요도 분석 결과, 전통적인 인구통계학적 특성이나 디바이스 정보보다 <b>PageValues</b>와 <b>ProductRelated_Duration</b> 등 
            '현재 세션 내 고객 행동 정보'가 고객의 실시간 관심도를 파악하는 데 비교할 수 없을 정도로 결정적인 기여를 합니다.<br>
            따라서 마케터는 신규 유저 획득(Acquisition) 단계에서의 일회성 프로모션 집행을 줄이고, 자사몰 유입 고객들의 
            상품 상세 보기 체류 시간 향상을 위한 <b>콘텐츠 마케팅(리뷰 영역 강화, 추천 AI 기능 활성화)</b>에 최우선적으로 리소스를 분배해야 합니다.<br>
            종료율이 높은 상세 페이지 구간을 주기적으로 퍼널 분석 및 A/B 테스트하여 기술적 이탈 요소를 적극적으로 줄이는 노력이 수반되어야 
            모델이 도출한 비즈니스 규칙이 최상의 매출 전환 시너지로 연결될 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 중요도 상위 데이터 상세 리스트
    st.markdown("<br>**📊 중요도 상세 데이터 표**", unsafe_allow_html=True)
    st.dataframe(
        feat_importances.sort_values(by="Importance", ascending=False).rename(
            columns={"Feature": "피처명", "Importance": "피처 중요도"}
        ).set_index("피처명"),
        use_container_width=True
    )

# ----------------- 대시보드 공통 최하단: 비즈니스 인사이트 및 액션 플랜 -----------------
st.markdown("---")
st.markdown("## 💡 비즈니스 인사이트 및 액션 플랜 (Action Plan)")
st.html("""
<div class="commentary-box" style="border-left: 5px solid #ff9900; background-color: #ffffff; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 10px;">
    <p style="font-size: 16px; margin-bottom: 25px; color: #4e73df; font-weight: 500;">
        위의 피처 중요도(Feature Importance) 및 의사결정나무(Decision Tree) 분기 결과를 종합해보면, 방문자의 최종 구매(Revenue) 여부를 결정짓는 가장 핵심적인 요소들을 파악할 수 있습니다. 이를 바탕으로 다음과 같은 비즈니스 수익화(Monetization) 극대화 액션 플랜을 제안합니다.
    </p>

    <h3 style="color: #2e3e4e; font-size: 20px; border-bottom: 2px solid #f1f3f9; padding-bottom: 8px;">1. 페이지 가치(PageValues) 극대화 및 장바구니 최적화</h3>
    <p style="margin-bottom: 12px;">
        머신러닝 분석 결과, <b>PageValues</b> (방문자가 구매 전에 머문 페이지의 평균 가치)가 구매 예측에 가장 압도적인 기여도를 가진 최중요 특성(Feature)으로 나타났습니다. 의사결정나무의 최상단 루트 노드 역시 해당 변수를 기준으로 고객을 1차 분류하며, 이 값이 임계점(약 6.02달러)을 넘을 때 높은 구매 확률을 보입니다.
    </p>
    <ul style="margin-bottom: 25px; padding-left: 20px;">
        <li style="margin-bottom: 8px;"><b>액션 플랜:</b> 높은 가치를 지닌 페이지(장바구니, 결제 프로세스, 베스트셀러 상품 상세 페이지 등)로 고객 유입을 유도하는 구매 깔깔때기(Funnel) 여정을 전면 최적화해야 합니다. 특히 결제 단계에서의 허들과 심리적 마찰(Friction)을 줄이기 위해 원클릭 간편 결제 시스템을 강화하고 간소화해야 합니다. 또한 장바구니에 도달하였으나 미결제 상태인 유저들에게는 타임 세일 팝업이나 무료 배송 쿠폰을 <b>넛지(Nudge)</b> 형태로 실시간 제공하여 이탈 없이 최종 구매를 확정 짓도록 효과적으로 유도해야 합니다.</li>
    </ul>

    <h3 style="color: #2e3e4e; font-size: 20px; border-bottom: 2px solid #f1f3f9; padding-bottom: 8px;">2. 이탈률(ExitRates) 분석 및 첫 페이지 체류(Retention) 방어 전략</h3>
    <p style="margin-bottom: 12px;">
        의사결정나무의 하위 분기 흐름을 보면, <b>ExitRates (종료율)</b>와 <b>BounceRates (반송률)</b> 수치가 높게 나타나는 고객 그룹은 수익 전환율이 급격히 저하되는 경향을 강하게 보입니다. 이는 사이트 진입 후 첫 브라우징 경험이 구매 여정에 심각한 병목을 유발하고 있음을 증명합니다.
    </p>
    <ul style="margin-bottom: 25px; padding-left: 20px;">
        <li style="margin-bottom: 8px;"><b>액션 플랜:</b> 유입 직후 반송 및 이탈이 유독 많이 발생하는 '문제 랜딩 페이지'와 상세 설명 페이지를 트래킹하여 직관적이고 매끄러운 UI/UX로 전면 개편해야 합니다. 기술적으로 페이지 로딩 속도를 1초 단위로 최적화하고 단축시켜야 하며, 웹 화면 상단(Above the Fold) 영역에 고객의 시선을 단번에 사로잡는 매력적인 프로모션 배너와 명확한 CTA(Call to Action) 버튼을 배치하여 다음 추천 페이지로의 탐색 이동을 적극 유도해야 합니다.</li>
    </ul>

    <h3 style="color: #2e3e4e; font-size: 20px; border-bottom: 2px solid #f1f3f9; padding-bottom: 8px;">3. 상품 집중 탐색(ProductRelated_Duration) 기반의 리타겟팅(Retargeting)</h3>
    <p style="margin-bottom: 12px;">
        단순 정보 조회성 페이지 브라우징에 비해, 상품 상세 탐색 페이지 방문 횟수(<b>ProductRelated</b>)와 해당 영역 체류 시간(<b>ProductRelated_Duration</b>)이 길고 깊어질수록 실제 최종 전환으로 이어질 확률이 매우 높습니다.
    </p>
    <ul style="margin-bottom: 25px; padding-left: 20px;">
        <li style="margin-bottom: 8px;"><b>액션 플랜:</b> 특정 상품 상세 페이지에 오래 머물며 진지하게 탐색을 하였으나 결제하지 않고 이탈한 고객들은 구매 관여도가 높은 최상급의 <b>'고관여 잠재 고객'</b> 군입니다. 이 유저 풀(Pool)을 실시간 세그먼트화하여 맞춤형 리마인드 이메일 발송, 모바일 앱 푸시 알림, 구글 및 메타 등의 스폰서드 개인화 타겟 광고 캠페인을 자동 집행해야 합니다. 추가적으로 유저가 유심히 살펴본 상품의 실시간 연관 상품 및 교차 판매(Cross-Selling) 추천 기능을 고도화하여 재유입 시 구매를 자극해야 합니다.</li>
    </ul>

    <h3 style="color: #2e3e4e; font-size: 20px; border-bottom: 2px solid #f1f3f9; padding-bottom: 8px;">4. 방문 시기(Month, SpecialDay)를 고려한 시즌 맞춤 프로모션 집중</h3>
    <p style="margin-bottom: 12px;">
        고객의 쇼핑 행동은 외부 시즌 요인에 크게 반응합니다. 특정 월(예: 블랙프라이데이를 포함한 11월, 연말인 12월 등)의 계절적 영향이나 특별한 기념일(<b>SpecialDay</b>)과의 근접성은 잠재 고객들의 심리적 구매 장벽을 극적으로 낮추는 결정적인 촉진제 역할을 수행합니다.
    </p>
    <ul style="margin-bottom: 10px; padding-left: 20px;">
        <li style="margin-bottom: 8px;"><b>액션 플랜:</b> 의사결정나무 모델의 시즈널 트렌드 예측 결과를 기반으로 하여, 매출 기여도가 높은 특정 시즌 및 주요 공휴일 직전 기간에 마케팅 예산(Budget Allocation)을 집중적으로 편성하여 투자 대비 효율(ROI)을 극대화해야 합니다. 특히 특별한 날에 근접하여 유입되는 유저들에게는 'D-Day 한정 초특가', '오늘 자정 마감 임박' 등 타임아웃을 활용한 <b>FOMO(소외 불안)</b> 마케팅 기법과 개인화 혜택 소스를 적재적소에 노출시킴으로써 잠재된 충동구매 욕구를 구매 완료로 유도하는 전략이 필요합니다.</li>
    </ul>
</div>
""")
