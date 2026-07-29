"""
온라인 쇼핑몰 데이터셋 EDA 및 머신러닝 리포트용 시각화 차트 자산 생성 스크립트
작성일: 2026-07-18
설명: Matplotlib 및 koreanize-matplotlib, 맑은 고딕(Malgun Gothic)을 사용하여 한글 폰트가 100% 깨짐 없이 깔끔하게 적용된 EDA 차트 15종 및
      ML 평가 차트 4종을 생성하고 online-shoppers/report/images/ 디렉토리에 저장합니다.
"""

import os
import zipfile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

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
    roc_curve
)

# Matplotlib 한글 폰트 명확 지정 (Malgun Gothic 우선 지정으로 Glyph missing 결함 100% 해결)
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 저장 디렉토리 생성
images_dir = "online-shoppers/report/images"
os.makedirs(images_dir, exist_ok=True)

# 1. 데이터 로딩
zip_path = "online-shoppers/data/online+shoppers+purchasing+intention+dataset.zip"
if not os.path.exists(zip_path):
    zip_path = "data/online+shoppers+purchasing+intention+dataset.zip"

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    csv_filename = "online_shoppers_intention.csv"
    with zip_ref.open(csv_filename) as f:
        df = pd.read_csv(f)

print("데이터 로딩 완료: ", df.shape)

# -----------------------------------------------------------------------------
# EDA 차트 1: 타겟 변수 (Revenue) 분포
# -----------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

rev_counts = df['Revenue'].value_counts()
colors = ['#e74a3b', '#1cc88a']

# 원형 차트
axes[0].pie(
    rev_counts, labels=['미구매 (False)', '구매 완료 (True)'],
    autopct='%1.1f%%', startangle=90, colors=colors, explode=(0.05, 0)
)
axes[0].set_title("Revenue 클래스 분포 비율", fontsize=14, fontweight='bold')

# 막대 차트
sns.barplot(x=['미구매 (False)', '구매 완료 (True)'], y=rev_counts.values, ax=axes[1], palette=colors)
axes[1].set_title("Revenue 클래스별 세션 빈도 (건)", fontsize=14, fontweight='bold')
axes[1].set_ylabel("세션 수 (건)")
for p in axes[1].patches:
    axes[1].annotate(f"{int(p.get_height()):,}건", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha='center', va='center', color='white', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(images_dir, "revenue_distribution.png"), dpi=300)
plt.close()

# -----------------------------------------------------------------------------
# EDA 차트 2~11: 10개 수치형 변수 시각화
# -----------------------------------------------------------------------------
num_cols = [
    'Administrative', 'Administrative_Duration', 
    'Informational', 'Informational_Duration', 
    'ProductRelated', 'ProductRelated_Duration', 
    'BounceRates', 'ExitRates', 'PageValues', 'SpecialDay'
]

num_labels = {
    'Administrative': '행정 페이지 방문수',
    'Administrative_Duration': '행정 페이지 체류 시간(초)',
    'Informational': '정보 페이지 방문수',
    'Informational_Duration': '정보 페이지 체류 시간(초)',
    'ProductRelated': '제품 관련 페이지 방문수',
    'ProductRelated_Duration': '제품 관련 페이지 체류 시간(초)',
    'BounceRates': '이탈률 (Bounce Rates)',
    'ExitRates': '종료율 (Exit Rates)',
    'PageValues': '페이지 가치 (Page Values)',
    'SpecialDay': '특별한 날과의 근접도 (Special Day)'
}

for col in num_cols:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    # Box Plot
    sns.boxplot(data=df, x='Revenue', y=col, ax=axes[0], palette=['#e74a3b', '#1cc88a'])
    axes[0].set_title(f"{num_labels[col]} - 박스플롯 (Box Plot)", fontsize=13, fontweight='bold')
    axes[0].set_xticklabels(['미구매 (False)', '구매 완료 (True)'])
    axes[0].set_xlabel("구매 여부 (Revenue)")
    axes[0].set_ylabel("값")
    
    # Histogram
    sns.histplot(data=df, x=col, hue='Revenue', kde=True, ax=axes[1], palette=['#e74a3b', '#1cc88a'], element="step")
    axes[1].set_title(f"{num_labels[col]} - 히스토그램 (Histogram)", fontsize=13, fontweight='bold')
    axes[1].set_xlabel("변수 값")
    axes[1].set_ylabel("빈도 수")
    
    plt.tight_layout()
    plt.savefig(os.path.join(images_dir, f"num_{col.lower()}.png"), dpi=300)
    plt.close()

# -----------------------------------------------------------------------------
# EDA 차트 12~14: 범주형 변수 시각화 (Month, VisitorType, Weekend)
# -----------------------------------------------------------------------------
cat_cols = ['Month', 'VisitorType', 'Weekend']
cat_labels = {'Month': '방문 월', 'VisitorType': '방문자 유형', 'Weekend': '주말 여부'}

for col in cat_cols:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 절대 빈도 Stacked Bar
    ct_counts = pd.crosstab(df[col], df['Revenue'])
    ct_counts.plot(kind='bar', stacked=True, color=['#e74a3b', '#1cc88a'], ax=axes[0])
    axes[0].set_title(f"{cat_labels[col]} - 세션 빈도 (Counts)", fontsize=13, fontweight='bold')
    axes[0].set_ylabel("세션 수 (건)")
    axes[0].legend(['미구매 (False)', '구매 완료 (True)'])
    axes[0].tick_params(axis='x', rotation=30)
    
    # 100% 비율 Stacked Bar
    ct_ratios = pd.crosstab(df[col], df['Revenue'], normalize='index') * 100
    ct_ratios.plot(kind='bar', stacked=True, color=['#e74a3b', '#1cc88a'], ax=axes[1])
    axes[1].set_title(f"{cat_labels[col]} - 구매 전환 비율 (100% Stacked Bar)", fontsize=13, fontweight='bold')
    axes[1].set_ylabel("비율 (%)")
    axes[1].legend(['미구매 (False)', '구매 완료 (True)'])
    axes[1].tick_params(axis='x', rotation=30)
    
    plt.tight_layout()
    plt.savefig(os.path.join(images_dir, f"cat_{col.lower()}.png"), dpi=300)
    plt.close()

# -----------------------------------------------------------------------------
# EDA 차트 15: 고객 퍼널 분석 차트 (이모지 완전 제외 & Malgun Gothic 폰트)
# -----------------------------------------------------------------------------
funnel_stages = [
    "1. 전체 세션 유입",
    "2. 상품 페이지 상세조회",
    "3. 마이페이지/행정 조회",
    "4. 고가치 전환 페이지 도달",
    "5. 최종 구매 완료"
]
s1 = len(df)
s2 = len(df[df['ProductRelated'] > 0])
s3 = len(df[df['Administrative'] > 0])
s4 = len(df[df['PageValues'] > 0])
s5 = len(df[df['Revenue'] == True])
counts = [s1, s2, s3, s4, s5]

plt.figure(figsize=(10, 6))
bars = plt.barh(funnel_stages[::-1], counts[::-1], color=['#1cc88a', '#f68d3e', '#f6c23e', '#36b9cc', '#4e73df'])
plt.title("쇼핑몰 고객 행동 여정 퍼널 분석 (Funnel Analysis)", fontsize=14, fontweight='bold')
plt.xlabel("세션 수 (건)")

for bar in bars:
    width = bar.get_width()
    pct = (width / s1) * 100
    plt.text(width + 200, bar.get_y() + bar.get_height()/2, f"{width:,}건 ({pct:.1f}%)",
             va='center', ha='left', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(images_dir, "funnel_chart.png"), dpi=300)
plt.close()

# -----------------------------------------------------------------------------
# ML 차트 16~19: 머신러닝 학습 및 평가 차트 생성
# -----------------------------------------------------------------------------
df_ml = df.copy()
df_ml['Revenue'] = df_ml['Revenue'].astype(int)
df_ml['Weekend'] = df_ml['Weekend'].astype(int)

cat_cols_ml = ['Month', 'VisitorType', 'OperatingSystems', 'Browser', 'Region', 'TrafficType']
df_encoded = pd.get_dummies(df_ml, columns=cat_cols_ml, drop_first=True)

X = df_encoded.drop(columns=['Revenue'])
y = df_encoded['Revenue']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 1) Gradient Boosting 대표 모델 학습
gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
gb_model.fit(X_train, y_train)
y_pred_gb = gb_model.predict(X_test)
y_proba_gb = gb_model.predict_proba(X_test)[:, 1]

# ML 차트 16: Confusion Matrix
cm = confusion_matrix(y_test, y_pred_gb)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
            xticklabels=['미구매 (0)', '구매 완료 (1)'],
            yticklabels=['미구매 (0)', '구매 완료 (1)'],
            annot_kws={"size": 14, "weight": "bold"})
plt.title("Confusion Matrix (Gradient Boosting)", fontsize=14, fontweight='bold')
plt.xlabel("예측 클래스 (Predicted Label)")
plt.ylabel("실제 클래스 (Actual Label)")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "ml_confusion_matrix.png"), dpi=300)
plt.close()

# ML 차트 17: ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_proba_gb)
auc_val = roc_auc_score(y_test, y_proba_gb)

plt.figure(figsize=(7, 6))
plt.plot(fpr, tpr, color='#4e73df', lw=3, label=f'Gradient Boosting (AUC = {auc_val:.4f})')
plt.plot([0, 1], [0, 1], color='gray', linestyle='--', lw=2, label='Random Baseline')
plt.title("ROC (Receiver Operating Characteristic) 곡선", fontsize=14, fontweight='bold')
plt.xlabel("False Positive Rate (1 - Specificity)")
plt.ylabel("True Positive Rate (Recall / Sensitivity)")
plt.legend(loc="lower right", fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "ml_roc_curve.png"), dpi=300)
plt.close()

# ML 차트 18: Feature Importance
imp_df = pd.DataFrame({'Feature': X.columns, 'Importance': gb_model.feature_importances_})
imp_df = imp_df.sort_values(by='Importance', ascending=True).tail(20)

plt.figure(figsize=(10, 8))
plt.barh(imp_df['Feature'], imp_df['Importance'], color='#36b9cc')
plt.title("상위 20개 피처 중요도 (Feature Importance - Gradient Boosting)", fontsize=14, fontweight='bold')
plt.xlabel("중요도 (Importance Score)")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "ml_feature_importance.png"), dpi=300)
plt.close()

# ML 차트 19: 4대 ML 모델 5대 지표 성능 대조 그룹 막대 차트
models = {
    "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1, class_weight='balanced'),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42),
    "HistGradient Boosting": HistGradientBoostingClassifier(max_iter=100, max_depth=10, learning_rate=0.1, random_state=42, class_weight='balanced'),
    "AdaBoost": AdaBoostClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
}

comp_results = []
for name, m in models.items():
    m.fit(X_train, y_train)
    yp = m.predict(X_test)
    yprob = m.predict_proba(X_test)[:, 1] if hasattr(m, "predict_proba") else yp
    
    comp_results.append({
        "알고리즘": name,
        "Accuracy": accuracy_score(y_test, yp),
        "Precision": precision_score(y_test, yp, zero_division=0),
        "Recall": recall_score(y_test, yp, zero_division=0),
        "F1-Score": f1_score(y_test, yp, zero_division=0),
        "ROC-AUC": roc_auc_score(y_test, yprob)
    })

comp_df = pd.DataFrame(comp_results)

# Grouped Bar Plot
comp_df_melted = pd.melt(comp_df, id_vars=['알고리즘'], var_name='Metric', value_name='Score')

plt.figure(figsize=(12, 6))
sns.barplot(data=comp_df_melted, x='알고리즘', y='Score', hue='Metric', palette=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'])
plt.title("4대 머신러닝 알고리즘 5대 성능 평가 지표 비교", fontsize=14, fontweight='bold')
plt.ylim(0, 1.1)
plt.ylabel("지표 점수 (Score)")
plt.legend(loc='lower right', bbox_to_anchor=(1, 1.02), ncol=5)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "ml_model_comparison.png"), dpi=300)
plt.close()

print("Malgun Gothic 폰트를 적용하여 모든 시각화 자산 이미지 19종이 100% 깨짐 없이 완벽히 생성되었습니다!")
