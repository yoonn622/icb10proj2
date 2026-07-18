"""
뉴트리핏(NutriFit) 초개인화 영양제 추천 및 트렌드 대시보드 애플리케이션입니다.
- [가독성 개선] 다크모드/라이트모드 호환 BMI 수치 박스 및 전체 텍스트 명도/가독성 대폭 향상
- [기능 추가] 내 영양제 보관함 목록 및 상단 바에 원클릭 바로 구매(쿠팡/올리브영/아이허브) 링크 연동
"""

import os
import sys
import re
from urllib.parse import quote_plus
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 0. 페이지 기본 설정 및 커스텀 CSS (Clean Green & White + High Contrast)
# ==========================================
st.set_page_config(
    page_title="NutriFit | AI 초개인화 영양제 큐레이션",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
    .main {
        background-color: #f8faf9;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    .header-container {
        background: linear-gradient(135deg, #0e462d 0%, #1b7a4e 100%);
        color: white;
        padding: 2.2rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(14, 70, 45, 0.15);
    }
    .header-container h1 {
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 0.5rem;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .header-container p {
        font-size: 1.1rem;
        color: #f0fdf4 !important;
        opacity: 0.95;
        margin: 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        justify-content: center;
        border-bottom: 2px solid #e1e9e5;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 52px;
        white-space: nowrap !important;
        background-color: #ffffff;
        border-radius: 12px 12px 0px 0px;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
        border: 1px solid #d5e3dc;
        color: #374151 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1b7a4e !important;
        color: #ffffff !important;
        border-color: #1b7a4e !important;
        box-shadow: 0 4px 12px rgba(27, 122, 78, 0.2);
    }

    .custom-card {
        background-color: #ffffff !important;
        color: #1f2937 !important;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        border: 1px solid #e1e9e5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* 🌟 BMI 박스 고대비 가독성 극대화 */
    .bmi-box {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 2px solid #1b7a4e !important;
        border-left: 6px solid #1b7a4e !important;
        padding: 1.2rem 1.4rem;
        border-radius: 12px;
        margin-top: 0.5rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }
    
    .badge-green {
        background-color: #e8f5e9;
        color: #1b7a4e !important;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .badge-goal {
        background-color: #fef3c7;
        color: #92400e !important;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .badge-platform {
        background-color: #e0f2fe;
        color: #0369a1 !important;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .badge-price {
        background-color: #f3e8ff;
        color: #6b21a8 !important;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    
    .top-product-card {
        background: #ffffff !important;
        color: #1f2937 !important;
        border: 2px solid #1b7a4e;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 16px rgba(27, 122, 78, 0.12);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 560px;
    }

    .product-img-box {
        width: 100%;
        height: 170px;
        object-fit: contain;
        border-radius: 12px;
        background-color: #ffffff;
        padding: 0.5rem;
        margin-bottom: 0.8rem;
        border: 1px solid #e5e7eb;
    }

    .buy-btn {
        display: block;
        width: 100%;
        text-align: center;
        background-color: #1b7a4e;
        color: #ffffff !important;
        font-weight: 700;
        padding: 0.65rem 1rem;
        border-radius: 10px;
        text-decoration: none;
        margin-top: 0.4rem;
        margin-bottom: 0.4rem;
        transition: background-color 0.2s ease;
    }
    .buy-btn:hover {
        background-color: #0e462d;
        color: #ffffff !important;
        text-decoration: none;
    }
    
    .cart-buy-btn {
        display: inline-block;
        width: 100%;
        text-align: center;
        background-color: #0284c7;
        color: #ffffff !important;
        font-weight: 700;
        padding: 0.5rem 0.8rem;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.88rem;
        transition: background-color 0.2s ease;
    }
    .cart-buy-btn:hover {
        background-color: #0369a1;
        color: #ffffff !important;
        text-decoration: none;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

DEFAULT_IMG = "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?auto=format&fit=crop&w=400&q=80"

# ==========================================
# 1. 세션 스테이트 & 헬퍼
# ==========================================
if "cart" not in st.session_state:
    st.session_state.cart = {}

if "diagnosed" not in st.session_state:
    st.session_state.diagnosed = False

if "recommendations" not in st.session_state:
    st.session_state.recommendations = []

if "filter_reasons" not in st.session_state:
    st.session_state.filter_reasons = []

if "selected_goals" not in st.session_state:
    st.session_state.selected_goals = []

def get_product_img(url, platform=''):
    url_str = str(url).strip() if pd.notna(url) else ""
    plat_str = str(platform).lower()
    
    if 'iherb' in plat_str or 'iherb.com' in url_str.lower():
        return DEFAULT_IMG
        
    if not url_str or url_str.lower() in ['nan', 'none', '0', 'undefined'] or not url_str.startswith('http'):
        return DEFAULT_IMG
        
    return url_str

def add_to_cart(row):
    row_dict = dict(row) if hasattr(row, 'to_dict') else dict(row)
    pid = str(row_dict['product_id'])
    row_dict['img_url'] = get_product_img(row_dict.get('img_url', ''), row_dict.get('platform', ''))
    st.session_state.cart[pid] = row_dict
    st.toast(f"🛒 '{str(row_dict['product_name'])[:18]}...' 보관함에 추가되었습니다!", icon="✅")

def remove_from_cart(pid):
    pid = str(pid)
    if pid in st.session_state.cart:
        removed_name = str(st.session_state.cart[pid]['product_name'])
        del st.session_state.cart[pid]
        st.toast(f"🗑️ '{removed_name[:18]}...' 보관함에서 삭제되었습니다.", icon="ℹ️")

def clear_cart():
    st.session_state.cart.clear()
    st.toast("🧹 보관함이 비워졌습니다.", icon="🧹")

def get_purchase_url(platform, product_name):
    encoded_name = quote_plus(str(product_name))
    plat_str = str(platform).lower()
    if 'coupang' in plat_str:
        return f"https://www.coupang.com/np/search?q={encoded_name}"
    elif 'oliveyoung' in plat_str:
        return f"https://www.oliveyoung.co.kr/store/search/getSearchMain.do?query={encoded_name}"
    elif 'iherb' in plat_str:
        return f"https://kr.iherb.com/search?kw={encoded_name}"
    else:
        return f"https://search.shopping.naver.com/search/all?query={encoded_name}"

# ==========================================
# 2. 데이터 로드 및 1일 섭취비용 산정
# ==========================================
@st.cache_data
def load_data():
    possible_paths = [
        os.path.join("project2", "data", "ec_mapped_with_api.csv"),
        os.path.join("data", "ec_mapped_with_api.csv"),
        "ec_mapped_with_api.csv"
    ]
    csv_path = None
    for p in possible_paths:
        if os.path.exists(p):
            csv_path = p; break
            
    if not csv_path:
        st.error("❌ 'ec_mapped_with_api.csv' 데이터 파일을 찾을 수 없습니다.")
        return pd.DataFrame()
        
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    df['product_name'] = df['product_name'].fillna('')
    df['brand'] = df['brand'].fillna('자체브랜드/기타')
    df['price'] = df['price'].fillna(0)
    df['rating'] = df['rating'].fillna(0.0)
    df['review_count'] = df['review_count'].fillna(0)
    df['matched_ingredient'] = df['matched_ingredient'].fillna('미분류 일반식품군')
    df['functionality_raw'] = df['functionality_raw'].fillna('일반 영양 공급')
    df['hard_filter_trigger'] = df['hard_filter_trigger'].fillna('None')
    df['platform'] = df['platform'].fillna('unknown')
    
    df['img_url'] = df.apply(lambda r: get_product_img(r.get('img_url', ''), r.get('platform', '')), axis=1)
    df['popularity_score'] = df['review_count'] * df['rating']
    
    def extract_form(row):
        if 'form_type' in row and pd.notna(row['form_type']) and row['form_type'] != '정제':
            return row['form_type']
        p_name = str(row['product_name']).lower()
        if any(k in p_name for k in ['구미', '젤리', 'gummy']): return '구미/젤리'
        elif any(k in p_name for k in ['액상', '드링크', '앰플', '샷', '워터', '액']): return '액상/드링크'
        elif any(k in p_name for k in ['포', '분말', '가루', '스틱', '스틱포']): return '분말/포'
        elif any(k in p_name for k in ['스트립', '필름', 'odf']): return '스트립/필름'
        elif any(k in p_name for k in ['캡슐', '소프트캡슐', '하드캡슐']): return '캡슐'
        return '정제'

    df['form_type'] = df.apply(extract_form, axis=1)

    def calc_daily_cost(row):
        price = row['price']
        if price <= 0: return 0
        p_name = str(row['product_name'])
        
        match_days = re.search(r'(\d+)\s*(일분|개월분|개월)', p_name)
        if match_days:
            num = int(match_days.group(1))
            unit = match_days.group(2)
            days = num * 30 if '개월' in unit else num
            if days > 0: return int(price / days)
            
        match_count = re.search(r'(\d+)\s*(정|캡슐|포|스틱|병|개)', p_name)
        if match_count:
            count = int(match_count.group(1))
            if count >= 10:
                days = count / 2.0
                return int(price / days)
                
        return int(price / 30.0)

    df['daily_cost'] = df.apply(calc_daily_cost, axis=1)
    return df


# ==========================================
# 3. 메인 대시보드 레이아웃
# ==========================================
def main():
    st.markdown("""
        <div class="header-container">
            <h1>🧬 NutriFit 초개인화 AI 영양제 큐레이션</h1>
            <p>공공데이터(식약처/DUR) 기반 스마트 안전 진단 & 맞춤형 영양제 추천 시스템</p>
        </div>
    """, unsafe_allow_html=True)
    
    df = load_data()
    if df.empty:
        return

    # 🛒 상단 스마트 보관함 요약 바 (Cart Summary + 바로 구매 링크 연동)
    cart_count = len(st.session_state.cart)
    if cart_count > 0:
        with st.expander(f"🛒 내 영양제 보관함 ({cart_count}개 담김) - 클릭하여 합산 비용 및 구매 링크 보기", expanded=True):
            cart_rows = list(st.session_state.cart.values())
            cart_df = pd.DataFrame(cart_rows)
            
            total_price = cart_df['price'].sum()
            total_daily = cart_df['daily_cost'].sum()
            
            mc1, mc2, mc3 = st.columns([1, 1, 1])
            with mc1: st.metric("💰 담은 영양제 총 금액", f"{int(total_price):,}원")
            with mc2: st.metric("🗓️ 1일 총 합산 복용 비용", f"약 {int(total_daily):,}원 / 일")
            with mc3:
                if st.button("🧹 보관함 전체 비우기", type="secondary", key="clear_top_cart_v9"):
                    clear_cart()
                    st.rerun()

            ing_counts = cart_df['matched_ingredient'].value_counts()
            duplicated_ings = ing_counts[ing_counts > 1]
            if not duplicated_ings.empty:
                st.warning(f"⚠️ **성분 중복 과다 섭취 주의**: 현재 보관함에 다음 성분이 2개 이상 중복 포함되어 있습니다.")
                for ing_name, cnt in duplicated_ings.items():
                    if ing_name != "미분류 일반식품군":
                        st.write(f"• **{ing_name}** ({cnt}개 제품 중복) - 동일 성분 중복 복용 시 1일 권장 섭취량 초과 가능성이 있으니 함량을 확인하세요.")
            else:
                st.success("✅ 현재 담으신 영양제들의 주요 기능성 원료 중복 및 과다 섭취 위험이 없습니다!")

            # 바로 구매 URL 컬럼 포함 데이터프레임
            display_cart_df = cart_df.copy()
            display_cart_df['구매_링크'] = display_cart_df.apply(lambda r: get_purchase_url(r['platform'], r['product_name']), axis=1)
            
            st.markdown("##### 🛒 담은 영양제 목록 및 구매 링크")
            st.dataframe(
                display_cart_df[['brand', 'product_name', 'price', 'daily_cost', 'matched_ingredient', 'platform', '구매_링크']].reset_index(drop=True),
                column_config={
                    "구매_링크": st.column_config.LinkColumn("🛒 구매 링크", help="클릭 시 구매 페이지로 이동", display_text="구매하러 가기")
                },
                use_container_width=True
            )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🧬 뉴트리핏 스마트 문진 및 AI 진단",
        "🏷️ 카테고리별 인기 영양제",
        "🎂 연령대별 인기 영양제",
        "🛒 내 영양제 보관함 분석",
        "💊 영양제 시너지 & 복용 타임 가이드",
        "🔍 영양제 검색 & 스펙 비교"
    ])
    
    # ==========================================
    # [탭 1] 스마트 문진 및 AI 진단 (BMI 고대비 가독성 개선)
    # ==========================================
    with tab1:
        st.subheader("📋 개인 맞춤형 영양 문진 및 의료 안전 필터 진단")
        st.warning(
            "⚠️ **서비스 안내 및 면책 공지**: 본 서비스는 의학적 치료나 질병 진단을 대체하는 의료 행위가 아니며, "
            "식약처 공공데이터 및 이커머스 상품 정보를 바탕으로 제공되는 헬스케어 참고용 추천 시스템입니다. "
            "특이 체질이나 지병이 있으신 경우 전문의 또는 약사와 상담을 권장합니다."
        )
        
        st.markdown("##### 🔒 필수 약관 동의")
        agree_cols = st.columns(3)
        with agree_cols[0]: agree_terms = st.checkbox("[필수] 서비스 이용약관 및 일반 개인정보 수집·이용 동의")
        with agree_cols[1]: agree_age = st.checkbox("[필수] 만 14세 이상 이용 확인 (만 14세 미만 제한)")
        with agree_cols[2]: agree_health = st.checkbox("[필수] 건강 상태 및 라이프스타일(민감정보) 수집·이용 동의")
            
        all_agreed = agree_terms and agree_age and agree_health
        st.divider()
        
        if not all_agreed:
            st.info("💡 위 3가지 필수 이용 약관 항목에 모두 동의해주셔야 스마트 문진 및 진단이 활성화됩니다.")
        else:
            # STEP 1
            st.markdown("### 👤 STEP 1. 기본 정보 (Demographics)")
            c1, c2, c3 = st.columns([1.1, 1, 1.2])
            with c1:
                gender = st.radio("1-1. 성별", ["남성", "여성", "응답하지 않음"], horizontal=True, key="gender_v9")
                male_concerns = []
                female_status = "해당 없음"
                if gender == "남성":
                    male_concerns = st.multiselect("남성 특화 추가 고민 선택", ["전립선 건강", "남성형 탈모 고민", "근육량 유지/운동"], key="male_concerns_v9")
                elif gender == "여성":
                    female_status = st.radio("여성 생애주기/상태 선택", ["해당 없음", "임신 준비 중", "임신 중", "수유 중", "폐경기"], key="female_status_v9")
            with c2:
                age_group = st.selectbox("1-2. 연령대", ["20대 미만", "20대", "30대", "40대", "50대 이상"], index=2)
            with c3:
                height = st.number_input("1-3. 키 (cm)", min_value=100.0, max_value=230.0, value=160.0, step=0.5, key="height_v9")
                weight = st.number_input("몸무게 (kg)", min_value=30.0, max_value=200.0, value=50.0, step=0.5, key="weight_v9")
                
                height_m = height / 100.0
                bmi = weight / (height_m * height_m)
                if bmi < 18.5: bmi_status = "저체중 (체중 관리 필요)"; bmi_color = "#0284c7"
                elif 18.5 <= bmi < 23.0: bmi_status = "정상 체중"; bmi_color = "#16a34a"
                elif 23.0 <= bmi < 25.0: bmi_status = "과체중 (주의)"; bmi_color = "#d97706"
                else: bmi_status = "비만 (경계/관리 필요)"; bmi_color = "#dc2626"
                
                # 🌟 BMI 수치 박스 고대비 가독성 극대화 (다크모드/라이트모드 완벽 대응)
                st.markdown(f"""
                <div class="bmi-box">
                    <div style="margin-bottom:0.3rem;">
                        <span style="color:#111827; font-size:1.05rem; font-weight:800;">📐 실시간 계산 BMI 지수:</span> 
                        <span style="color:#0e462d; font-size:1.2rem; font-weight:800; background-color:#e8f5e9; padding:0.1rem 0.5rem; border-radius:6px;">{bmi:.1f} kg/m²</span>
                    </div>
                    <div>
                        <span style="color:#111827; font-size:1.05rem; font-weight:800;">📊 상태 진단:</span> 
                        <span style="color:{bmi_color}; font-size:1.2rem; font-weight:800; background-color:#f9fafb; padding:0.1rem 0.5rem; border-radius:6px; border:1px solid #e5e7eb;">{bmi_status}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.divider()
            
            # STEP 2
            st.markdown("### 🏃‍♂️ STEP 2. 라이프스타일 & 일상 습관 (Lifestyle)")
            l1, l2, l3 = st.columns(3)
            with l1:
                workout_goals = st.multiselect(
                    "2-1. 운동 종류 및 목적 (복수 선택)",
                    ["근력 운동/웨이트", "유산소/러닝", "요가/필라테스", "골프/수영/등산", "운동 하지 않음", "체중 조절/다이어트"]
                )
            with l2:
                drinking = st.selectbox("2-2. 음주 빈도", ["마시지 않음", "주 1~2회", "주 3회 이상"])
                caffeine = st.selectbox("하루 카페인 섭취량", ["커피 안 마심", "하루 1잔", "하루 2~3잔 이상 (고카페인)"])
            with l3:
                st.markdown("2-3. 자가 평가 (1: 매우 낮음 ~ 5: 매우 높음)")
                diet_score = st.slider("균형 잡힌 식습관 정도", 1, 5, 3)
                sleep_score = st.slider("수면 만족도 및 유의성", 1, 5, 3)
                stress_score = st.slider("스트레스 인지 수준", 1, 5, 3)
                
            st.divider()
            
            # STEP 3
            st.markdown("### 🩺 STEP 3. 건강 상태 & 안전성 필터 (Medical & Safety) ★")
            m1, m2, m3 = st.columns(3)
            with m1:
                smoking = st.radio("3-1. 흡연 여부", ["비흡연", "흡연"], horizontal=True)
            with m2:
                allergies = st.multiselect(
                    "3-2. 알레르기 유발 성분 선택",
                    ["갑각류(게/새우)", "대두/콩", "우유/유제품", "계란", "견과류", "밀/글루텐", "해산물/어류"]
                )
                side_effect_input = st.text_input("부작용 경험 성분 직접 입력 (예: 속쓰림, 붉은 반점 등)")
            with m3:
                diseases = st.multiselect(
                    "3-3. 지병 및 복용 약물 (공공데이터 안전 필터 연동)",
                    ["고혈압", "당뇨", "이상지질혈증(고지혈증)", "만성 위장 질환", "혈전 관련 질환/아스피린 복용", "간/신장 질환", "없음"]
                )
                
            st.divider()
            
            # STEP 4
            st.markdown("### 🎯 STEP 4. 건강 고민 및 목표 (Health Goals)")
            health_goals = st.multiselect(
                "4-1. 가장 개선하고 싶은 건강 고민 (⚠️ 최대 2개 선택 가능)",
                ["만성 피로", "눈 건조", "장 건강", "피부 탄력", "체지방 감소", "면역력 저하", "관절 보호", "수면 부족", "항노화", "생리 불순"],
                default=["만성 피로", "관절 보호"],
                max_selections=2
            )
            if len(health_goals) == 0:
                st.caption("💡 최소 1개 이상의 건강 고민을 선택하시면 맞춤 추천 정확도가 상승합니다.")
            elif len(health_goals) > 2:
                st.error("⚠️ 건강 고민은 최대 2개까지만 선택할 수 있습니다.")
                
            st.divider()
            
            # STEP 5
            st.markdown("### 💊 STEP 5. 섭취 편의성 및 구매 성향 (Preference)")
            p1, p2, p3 = st.columns(3)
            with p1:
                pill_difficulty = st.radio("5-1. 알약(정제/캡슐) 삼킬 때 불편함", ["상관없음", "매우 불편함"], horizontal=True)
                preferred_forms = []
                if pill_difficulty == "매우 불편함":
                    st.info("👉 알약 삼킴이 불편하신 분을 위해 대안 제형 제품만 선별해 드립니다.")
                    preferred_forms = st.multiselect(
                        "선호하는 대안 제형 (복수 선택)",
                        ["구미/젤리", "액상/드링크", "분말/포", "소형 알약", "스트립/필름"],
                        default=["구미/젤리", "액상/드링크"]
                    )
            with p2:
                important_values = st.multiselect(
                    "5-2. 중요하게 생각하는 가치 (최대 2개)",
                    ["가성비", "식약처 인증 성분", "브랜드 신뢰도", "섭취 편의성", "높은 후기/평점"],
                    max_selections=2
                )
            with p3:
                budget_range = st.selectbox("5-3. 월 예산 범위", ["제한 없음", "3만원 이하", "3만원~5만원", "5만원~10만원", "10만원 이상"], index=2)
                preferred_form_all = st.multiselect("5-4. 일반 선호 제형 추가 선택", ["정제", "캡슐", "구미/젤리", "액상/드링크", "분말/포", "스트립/필름"])

            st.markdown("<br/>", unsafe_allow_html=True)
            diagnose_click = st.button("🚀 AI 맞춤 영양제 진단 및 큐레이션 받기", type="primary", use_container_width=True)
            
            if diagnose_click:
                df_filtered = df.copy()
                filter_reasons = []
                
                if smoking == "흡연":
                    before_cnt = len(df_filtered)
                    mask = df_filtered['matched_ingredient'].str.contains('비타민 A|비타민A|베타카로틴', na=False) | \
                           df_filtered['product_name'].str.contains('비타민 A|비타민A|베타카로틴|레티놀', na=False)
                    df_filtered = df_filtered[~mask]
                    filter_reasons.append(f"흡연자 폐질환 위험 방지를 위해 비타민A/베타카로틴 성분 제외 ({before_cnt - len(df_filtered)}건 필터링)")
                    
                if female_status in ["임신 중", "수유 중"] or "혈전 관련 질환/아스피린 복용" in diseases:
                    before_cnt = len(df_filtered)
                    mask = (df_filtered['hard_filter_trigger'] == 'PREGNANCY_HAZARD') | \
                           df_filtered['matched_ingredient'].str.contains('오메가|비타민 K|비타민K', na=False) | \
                           df_filtered['product_name'].str.contains('오메가|비타민K', na=False)
                    df_filtered = df_filtered[~mask]
                    filter_reasons.append(f"임산부/혈전 주의를 위해 고함량 비타민A 및 오메가3/비타민K 성분 제외 ({before_cnt - len(df_filtered)}건 필터링)")

                if "갑각류(게/새우)" in allergies:
                    df_filtered = df_filtered[df_filtered['hard_filter_trigger'] != 'ALLERGY_CRUSTACEAN']
                    df_filtered = df_filtered[~df_filtered['product_name'].str.contains('키토산|갑각류|게|새우', na=False)]
                if "대두/콩" in allergies:
                    df_filtered = df_filtered[df_filtered['hard_filter_trigger'] != 'ALLERGY_SOY']
                if "우유/유제품" in allergies:
                    df_filtered = df_filtered[df_filtered['hard_filter_trigger'] != 'ALLERGY_MILK']
                    
                if pill_difficulty == "매우 불편함":
                    before_cnt = len(df_filtered)
                    allowed_forms = preferred_forms if preferred_forms else ["구미/젤리", "액상/드링크", "분말/포", "스트립/필름"]
                    df_filtered = df_filtered[df_filtered['form_type'].isin(allowed_forms)]
                    filter_reasons.append(f"삼킴 불편 해소를 위한 대안 제형({', '.join(allowed_forms)})만 선별 ({before_cnt - len(df_filtered)}건 필터링)")
                elif preferred_form_all:
                    df_filtered = df_filtered[df_filtered['form_type'].isin(preferred_form_all)]

                goal_ingredient_map = {
                    "만성 피로": ["비타민 B", "밀크씨슬", "홍삼", "아르기닌"],
                    "눈 건조": ["루테인", "아스타잔틴", "지아잔틴"],
                    "장 건강": ["유산균", "프로바이오틱스"],
                    "피부 탄력": ["콜라겐", "히알루론산", "엘라스틴"],
                    "체지방 감소": ["가르시니아", "카테킨", "시네프린", "키토산"],
                    "면역력 저하": ["아연", "프로폴리스", "비타민 C", "비타민 D"],
                    "관절 보호": ["콘드로이친", "MSM", "글루코사민", "칼슘"],
                    "수면 부족": ["테아닌", "마그네슘", "타트체리"],
                    "항노화": ["코엔자임Q10", "항산화"],
                    "생리 불순": ["이소플라본", "감마리놀렌산", "엽산", "철분"]
                }

                final_recommendations = []
                used_product_ids = set()
                for goal in health_goals:
                    target_ings = goal_ingredient_map.get(goal, [])
                    def goal_score(row):
                        score = 0.0
                        p_name = str(row['product_name']).lower()
                        m_ing = str(row['matched_ingredient']).lower()
                        for ing in target_ings:
                            if ing.lower() in p_name or ing.lower() in m_ing:
                                score += 20.0
                        score += min(row['popularity_score'] / 10000.0, 10.0)
                        return score

                    df_filtered['temp_goal_score'] = df_filtered.apply(goal_score, axis=1)
                    df_candidates = df_filtered[~df_filtered['product_id'].isin(used_product_ids)]
                    df_goal_top = df_candidates.sort_values(by='temp_goal_score', ascending=False).head(2 if len(health_goals) > 1 else 3)
                    for _, r in df_goal_top.iterrows():
                        r_dict = r.to_dict()
                        r_dict['img_url'] = get_product_img(r_dict.get('img_url', ''), r_dict.get('platform', ''))
                        final_recommendations.append((goal, r_dict))
                        used_product_ids.add(r['product_id'])
                        
                st.session_state.diagnosed = True
                st.session_state.recommendations = final_recommendations
                st.session_state.filter_reasons = filter_reasons
                st.session_state.selected_goals = health_goals
                st.rerun()

            if st.session_state.diagnosed and st.session_state.recommendations:
                st.markdown("---")
                st.markdown("## 🔍 AI 추천 엔진 진단 및 고민별 맞춤 큐레이션 결과")
                
                if st.session_state.filter_reasons:
                    with st.expander("🛡️ 적용된 안전 및 제형 필터 세부 내역 확인"):
                        for r in st.session_state.filter_reasons: st.write(f"• {r}")

                st.markdown("### 🥇 고민 영역별 맞춤 영양제 다각화 추천 (1일 비용 & 보관함 연동)")
                
                cols = st.columns(len(st.session_state.recommendations))
                for idx, (g_name, row) in enumerate(st.session_state.recommendations):
                    p_url = get_purchase_url(row['platform'], row['product_name'])
                    img_src = get_product_img(row['img_url'], row['platform'])
                    pid = str(row['product_id'])
                    is_in_cart = pid in st.session_state.cart
                    
                    with cols[idx]:
                        st.markdown(f"""
                        <div class="top-product-card">
                            <div>
                                <img src="{img_src}" class="product-img-box" alt="제품 이미지"/>
                                <span class="badge-goal">🎯 고민: {g_name}</span>
                                <span class="badge-platform">{row['platform'].upper()}</span>
                                <span class="badge-price">💰 1일 약 {int(row['daily_cost']):,}원</span>
                                <h4 style="margin-top:0.5rem; color:#0e462d; font-size:1.05rem; min-height: 2.6rem;">{row['product_name']}</h4>
                                <p style="margin-bottom:0.2rem; color:#444; font-size:0.9rem;"><b>브랜드:</b> {row['brand']}</p>
                                <p style="margin-bottom:0.2rem; color:#1b7a4e; font-size:1.15rem;"><b>가격:</b> {int(row['price']):,}원</p>
                                <p style="margin-bottom:0.4rem; color:#333; font-size:0.85rem;"><b>⭐ 평점:</b> {row['rating']}점 (리뷰 {int(row['review_count']):,}개)</p>
                                <hr style="margin:0.5rem 0; border-color:#e1e9e5;"/>
                                <p style="font-size:0.85rem; color:#333;"><b>🧪 주요 원료:</b><br/>{row['matched_ingredient']}</p>
                            </div>
                            <div>
                                <a href="{p_url}" target="_blank" class="buy-btn">🛒 {row['platform'].upper()}에서 구매하기</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if is_in_cart:
                            if st.button("❌ 보관함에서 삭제", key=f"del_rec_{pid}_{idx}_v9"):
                                remove_from_cart(pid)
                                st.rerun()
                        else:
                            if st.button("➕ 내 보관함에 담기", key=f"add_rec_{pid}_{idx}_v9", type="primary"):
                                add_to_cart(row)
                                st.rerun()

    # ==========================================
    # [탭 2] 카테고리별 인기 영양제
    # ==========================================
    with tab2:
        st.subheader("🏷️ 카테고리별 인기 영양제 & 원클릭 퀵 알약 칩")
        st.caption("원하는 퀵 칩 태그를 클릭하여 원료별 인기 랭킹을 즉시 조회하세요.")
        
        st.markdown("##### 💡 퀵 알약 칩 태그 선택 (Quick Pill Chips)")
        pill_cols = st.columns(7)
        quick_chips = [
            ("⚡ #피로회복", "비타민 B군·비오틴(에너지·활력)"),
            ("🦴 #관절보호", "콘드로이친(관절 건강)"),
            ("👁️ #눈건강", "루테인·지아잔틴(눈 건강)"),
            ("🧬 #장건강", "프로바이오틱스(유산균/장 건강)"),
            ("🫀 #혈관케어", "rTG 오메가-3(혈관·혈행)"),
            ("😴 #수면개선", "L-테아닌(수면·스트레스)"),
            ("🔥 #다이어트", "가르시니아·카테킨(체지방 감소)")
        ]
        
        selected_cat_pill = None
        for i, (chip_label, target_cat) in enumerate(quick_chips):
            with pill_cols[i]:
                if st.button(chip_label, key=f"chip_btn_{i}_v9", use_container_width=True):
                    selected_cat_pill = target_cat

        available_categories = [
            "전체 카테고리 보기", "콘드로이친(관절 건강)", "MSM·글루코사민(관절/연골)",
            "L-테아닌(수면·스트레스)", "바나바잎 추출물(혈당 케어)", "프로바이오틱스(유산균/장 건강)",
            "rTG 오메가-3(혈관·혈행)", "밀크씨슬(실리마린/간 건강)", "루테인·지아잔틴(눈 건강)",
            "비타민 C(항산화·면역)", "비타민 D(뼈 건강·면역)", "비타민 B군·비오틴(에너지·활력)",
            "마그네슘(신경·근육)", "칼슘(뼈·치아)", "아연(면역 기능)", "콜라겐(피부 탄력)",
            "코엔자임Q10(항산화·혈압)", "프로폴리스(항균·면역)", "L-아르기닌(혈류·활력)",
            "쏘팔메토(전립선 건강)", "이소플라본(여성 건강)", "엽산·철분(혈액 생성·임산부)",
            "가르시니아·카테킨(체지방 감소)", "홍삼·인삼(면역·피로 개선)"
        ]
        
        default_idx = 0
        if selected_cat_pill and selected_cat_pill in available_categories:
            default_idx = available_categories.index(selected_cat_pill)
            
        selected_cat = st.selectbox("🎯 상세 영양 성분 카테고리를 선택하세요", available_categories, index=default_idx, key="cat_select_v9")
        
        df_cat = df.copy() if selected_cat == "전체 카테고리 보기" else df[df['matched_ingredient'] == selected_cat]
        df_cat_top10 = df_cat.sort_values(by='popularity_score', ascending=False).head(10)
        
        if df_cat_top10.empty:
            st.info("해당 카테고리에 속한 데이터가 없습니다.")
        else:
            c1, c2 = st.columns([1.2, 1])
            with c1:
                fig = px.bar(
                    df_cat_top10.sort_values(by='popularity_score', ascending=True),
                    x='popularity_score', y='product_name', orientation='h',
                    title=f"🏆 {selected_cat} 인기 스코어 TOP 10",
                    labels={'popularity_score': '인기 점수 (리뷰수 × 평점)', 'product_name': '상품명'},
                    color='popularity_score', color_continuous_scale='Greens'
                )
                fig.update_layout(height=480, showlegend=False, margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Pretendard, sans-serif"))
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("##### 📄 TOP 10 상세 리스트 (1일 비용 포함)")
                renamed_df = df_cat_top10[['brand', 'product_name', 'price', 'daily_cost', 'rating', 'review_count', 'platform']].copy().reset_index(drop=True)
                renamed_df.columns = ['브랜드', '상품명', '가격(원)', '1일 비용(원)', '평점', '리뷰 수', '플랫폼']
                st.dataframe(renamed_df.style.format({'가격(원)': '{:,.0f}', '1일 비용(원)': '{:,.0f}', '평점': '{:.1f}', '리뷰 수': '{:,.0f}'}), use_container_width=True, height=430)

    # ==========================================
    # [탭 3] 연령대별 인기 영양제
    # ==========================================
    with tab3:
        st.subheader("🎂 연령대별 인기 영양제")
        selected_age = st.radio("조회할 연령대를 선택하세요", ["20대", "30대", "40대", "50대", "60대 이상"], horizontal=True, key="age_v9")
        age_weights = {
            "20대": ["비타민 B군·비오틴(에너지·활력)", "프로바이오틱스(유산균/장 건강)"],
            "30대": ["비타민 B군·비오틴(에너지·활력)", "rTG 오메가-3(혈관·혈행)", "마그네슘(신경·근육)"],
            "40대": ["rTG 오메가-3(혈관·혈행)", "밀크씨슬(실리마린/간 건강)", "루테인·지아잔틴(눈 건강)"],
            "50대": ["rTG 오메가-3(혈관·혈행)", "코엔자임Q10(항산화·혈압)", "콘드로이친(관절 건강)"],
            "60대 이상": ["콘드로이친(관절 건강)", "MSM·글루코사민(관절/연골)", "칼슘(뼈·치아)"]
        }
        target_ing_list = age_weights.get(selected_age, [])
        df_age = df.copy()
        df_age['age_score'] = df_age.apply(lambda r: r['popularity_score'] * (2.5 if r['matched_ingredient'] in target_ing_list else 1.0), axis=1)
        df_age_top10 = df_age.sort_values(by='age_score', ascending=False).head(10)
        
        st.dataframe(df_age_top10[['brand', 'product_name', 'matched_ingredient', 'price', 'daily_cost', 'platform']].reset_index(drop=True), use_container_width=True)

    # ==========================================
    # [탭 4] 내 영양제 보관함 분석 (원클릭 바로 구매 링크 100% 연동)
    # ==========================================
    with tab4:
        st.subheader("🛒 내 영양제 보관함 & 성분 중복 과다 섭취 분석")
        cart_count = len(st.session_state.cart)
        if cart_count == 0:
            st.info("💡 아직 보관함에 담긴 영양제가 없습니다. AI 진단 추천 카드나 검색 탭에서 '➕ 내 보관함에 담기'를 클릭해 보세요!")
        else:
            cart_rows = list(st.session_state.cart.values())
            cart_df = pd.DataFrame(cart_rows)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("📦 총 보관 상품 수", f"{cart_count}개")
            with c2: st.metric("💰 총 판매 금액", f"{int(cart_df['price'].sum()):,}원")
            with c3: st.metric("🗓️ 1일 총 합산 복용 비용", f"약 {int(cart_df['daily_cost'].sum()):,}원")
            
            st.divider()
            st.markdown("#### 🚨 영양 성분 중복 및 과다 섭취 위험 진단")
            ing_counts = cart_df['matched_ingredient'].value_counts()
            duplicated_ings = ing_counts[ing_counts > 1]
            if not duplicated_ings.empty:
                for ing_name, cnt in duplicated_ings.items():
                    if ing_name != "미분류 일반식품군":
                        st.error(f"⚠️ **{ing_name}** 성분이 {cnt}개 영양제에 동시 중복 섭취될 위험이 있습니다. 1일 권장량을 초과하지 않도록 조절해 주세요.")
            else:
                st.success("✅ 담으신 상품들 간의 성분 중복 및 과다 섭취 위험 요소가 없습니다.")

            st.divider()
            st.markdown("#### 📋 보관된 영양제 목록 관리 & 원클릭 구매 연동")
            for _, r in cart_df.iterrows():
                pid = str(r['product_id'])
                img_src = get_product_img(r.get('img_url', ''), r.get('platform', ''))
                p_url = get_purchase_url(r.get('platform', ''), r.get('product_name', ''))
                plat_name = str(r.get('platform', 'SHOP')).upper()
                
                cc1, cc2, cc3 = st.columns([1, 4, 1.4])
                with cc1:
                    st.image(img_src, width=85)
                with cc2:
                    st.markdown(f"**{r['product_name']}** | <span style='color:#0369a1; font-weight:700;'>{r['brand']}</span>", unsafe_allow_html=True)
                    st.caption(f"가격: {int(r['price']):,}원 (1일 약 {int(r['daily_cost']):,}원) | 주요 성분: {r['matched_ingredient']} | 판매처: {plat_name}")
                with cc3:
                    # 🌟 보관함 원클릭 구매하기 링크 버튼 추가!
                    st.markdown(f"""
                    <a href="{p_url}" target="_blank" class="cart-buy-btn">🛒 {plat_name} 구매</a>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    
                    if st.button("❌ 삭제", key=f"cart_page_del_{pid}_v9", use_container_width=True):
                        remove_from_cart(pid)
                        st.rerun()

    # ==========================================
    # [탭 5] 영양제 시너지 & 복용 타임 가이드
    # ==========================================
    with tab5:
        st.subheader("💊 영양제 복용 시너지 조합 및 섭취 골든타임 가이드")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### 🟢 최고 시너지 찰떡 궁합 BEST 4")
            st.markdown("""
            <div class="custom-card" style="border-left: 5px solid #16a34a;">
                <h5 style="color:#16a34a; margin-bottom:0.3rem;">1. 오메가3 + 비타민 E / 루테인</h5>
                <p style="font-size:0.95rem; color:#374151;">지용성 영양제인 루테인은 오메가3의 불포화지방산과 함께 섭취 시 체내 흡수율이 대폭 증가하며, 비타민E는 오메가3의 산화를 막아줍니다.</p>
            </div>
            <div class="custom-card" style="border-left: 5px solid #16a34a;">
                <h5 style="color:#16a34a; margin-bottom:0.3rem;">2. 칼슘 + 비타민 D + 마그네슘 (칼마디)</h5>
                <p style="font-size:0.95rem; color:#374151;">비타민D가 장에서 칼슘의 흡수를 돕고, 마그네슘은 흡수된 칼슘이 뼈로 잘 이동하도록 촉진하는 대표 상호보완 조합입니다.</p>
            </div>
            """, unsafe_allow_html=True)
        with g2:
            st.markdown("#### 🔴 동시 복용 금기 / 주의 섭취 조합")
            st.markdown("""
            <div class="custom-card" style="border-left: 5px solid #dc2626;">
                <h5 style="color:#dc2626; margin-bottom:0.3rem;">1. 칼슘 vs 철분</h5>
                <p style="font-size:0.95rem; color:#374151;">두 성분은 체내 이동 통로(흡수 수용체)를 공유하므로 동시 복용 시 서로의 흡수를 섭취 방해합니다. (최소 2시간 차이 권장)</p>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # [탭 6] 영양제 검색 & 스펙 비교
    # ==========================================
    with tab6:
        st.subheader("🔍 전체 28,239개 영양제 다중 키워드 검색 & 1:1 스펙 비교")
        st.caption("공백 단위 멀티 키워드 검색 지원 (예: '종근당 비타민', '고려은단 C', '오쏘몰 7일분')")
        
        search_query = st.text_input("🔎 검색어 입력 (띄어쓰기로 여러 단어 검색 가능)", value="종근당 비타민", key="sq_v9")
        
        if search_query.strip():
            tokens = search_query.strip().split()
            def match_all_tokens(row):
                full_text = f"{row['product_name']} {row['brand']} {row['matched_ingredient']} {row['functionality_raw']}".lower()
                return all(tok.lower() in full_text for tok in tokens)

            mask = df.apply(match_all_tokens, axis=1)
            search_df = df[mask].sort_values(by='popularity_score', ascending=False)
            
            st.markdown(f"📊 **'{search_query}'** 검색 결과: 총 **{len(search_df):,}**건 검색되었습니다.")
            
            if not search_df.empty:
                st.dataframe(
                    search_df[['platform', 'brand', 'product_name', 'price', 'daily_cost', 'rating', 'review_count', 'matched_ingredient', 'form_type']].reset_index(drop=True),
                    use_container_width=True,
                    height=320
                )
                
                # ⚖️ 영양제 3개 선택 1:1 스펙 & 실물 이미지 비교 영역
                st.divider()
                st.markdown("#### ⚖️ 검색 결과 중 최대 3개 제품 1:1 스펙 & 실물 이미지 비교")
                product_options = search_df['product_name'].unique()[:40]
                selected_products = st.multiselect("비교할 제품을 선택하세요 (최대 3개)", product_options, max_selections=3, key="comp_select_v9")
                
                if selected_products:
                    comp_df = search_df[search_df['product_name'].isin(selected_products)].drop_duplicates(subset=['product_name'])
                    comp_cols = st.columns(len(comp_df))
                    
                    for idx, (_, row) in enumerate(comp_df.iterrows()):
                        p_url = get_purchase_url(row['platform'], row['product_name'])
                        img_src = get_product_img(row['img_url'], row['platform'])
                        pid = str(row['product_id'])
                        is_in_cart = pid in st.session_state.cart
                        
                        with comp_cols[idx]:
                            st.markdown(f"""
                            <div class="custom-card" style="text-align:center;">
                                <img src="{img_src}" class="product-img-box" style="height:160px;" alt="제품 이미지"/>
                                <h5 style="margin-top:0.5rem; min-height: 2.4rem; color:#0e462d;">{row['product_name']}</h5>
                                <p style="margin-bottom:0.3rem; font-size:0.9rem; color:#444;"><b>브랜드:</b> {row['brand']} | <b>출처:</b> {row['platform'].upper()}</p>
                                <p style="margin-bottom:0.3rem; color:#1b7a4e; font-size:1.15rem;"><b>가격:</b> {int(row['price']):,}원</p>
                                <p style="margin-bottom:0.3rem; color:#6b21a8; font-size:0.95rem;"><b>💰 1일 섭취비용:</b> 약 {int(row['daily_cost']):,}원/일</p>
                                <p style="margin-bottom:0.3rem; color:#333;"><b>평점:</b> ⭐ {row['rating']}점 (리뷰 {int(row['review_count']):,}개)</p>
                                <p style="margin-bottom:0.3rem; color:#333;"><b>주요 성분:</b> {row['matched_ingredient']}</p>
                                <p style="margin-bottom:0.5rem; color:#333;"><b>제형:</b> {row['form_type']}</p>
                                <a href="{p_url}" target="_blank" class="buy-btn">🛒 {row['platform'].upper()}에서 구매하기</a>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if is_in_cart:
                                if st.button("❌ 보관함에서 삭제", key=f"del_comp_{pid}_{idx}_v9"):
                                    remove_from_cart(pid)
                                    st.rerun()
                            else:
                                if st.button("➕ 내 보관함에 담기", key=f"add_comp_{pid}_{idx}_v9", type="primary"):
                                    add_to_cart(row)
                                    st.rerun()


if __name__ == "__main__":
    main()
