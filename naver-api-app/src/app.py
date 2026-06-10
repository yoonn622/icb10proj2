"""
네이버 오픈API 연동 데이터를 시각화하고 심층 통계 분석을 제공하는 Streamlit 대시보드 애플리케이션입니다.

주요 기능:
- 네이버 API 인증 키(Client ID, Client Secret) 입력 및 관리
- 통합 검색어 트렌드(DataLab) 조회 및 분석
- 네이버 쇼핑 검색 기반 가격 분포, 쇼핑몰, 카테고리/제조사 점유율 분석
- 상품군 타입(productType)을 활용한 다차원 쇼핑 트렌드 분석
- 블로그, 카페글, 뉴스 검색 결과 수집 및 시간적 발행 추이 분석
- 비정형 텍스트(제목 및 요약문) 대상 TF-IDF 기반 상위 30개 키워드 분석
- 플로틀리(Plotly)를 통한 인터랙티브 시각화 차트 제공

작성자: Antigravity AI
생성일: 2026-06-08
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from dotenv import load_dotenv

# .env 파일 로드 (src 디렉토리 기준 상위 폴더인 naver-api-app 아래의 .env 파일 로드)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

# ==============================================================================
# 1. 페이지 설정 및 초기화
# ==============================================================================
st.set_page_config(
    page_title="네이버 API 데이터 수집 및 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태에 .env 파일의 API 키 설정 적용 (매 렌더링마다 .env 최신값을 반영)
st.session_state["client_id"] = os.getenv("NAVER_CLIENT_ID", "")
st.session_state["client_secret"] = os.getenv("NAVER_CLIENT_SECRET", "")

# 한국어 형태소 분석기 대안: 단순 단어 추출용 정규식 토크나이저
def simple_tokenizer(text):
    # 한글, 영문, 숫자 단어만 추출 (2글자 이상)
    words = re.findall(r'[가-힣a-zA-Z0-9]{2,}', text)
    return words

# ==============================================================================
# 2. 네이버 API 호출 함수 (st.cache_data 적용)
# ==============================================================================
@st.cache_data(show_spinner=False)
def fetch_datalab_trend(client_id, client_secret, keywords_list, start_date, end_date):
    """
    네이버 데이터랩 통합 검색어 트렌드 API 호출
    """
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": client_id.strip(),
        "X-Naver-Client-Secret": client_secret.strip(),
        "Content-Type": "application/json"
    }
    
    # keywordGroups 구성 (최대 5개)
    keyword_groups = []
    for kw in keywords_list[:5]:
        keyword_groups.append({
            "groupName": kw,
            "keywords": [kw]
        })
        
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "date",
        "keywordGroups": keyword_groups
    }
    
    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            # 데이터 프레임 변환
            results = res_json.get("results", [])
            df_list = []
            for group in results:
                title = group.get("title")
                data_points = group.get("data", [])
                for dp in data_points:
                    df_list.append({
                        "period": pd.to_datetime(dp.get("period")),
                        "ratio": dp.get("ratio"),
                        "keyword": title
                    })
            if df_list:
                return pd.DataFrame(df_list)
            else:
                raise Exception("결과 데이터가 비어 있습니다.")
        else:
            raise Exception(f"오류 발생 (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        # 캐싱을 차단하기 위해 예외를 상위로 다시 던짐
        raise e

@st.cache_data(show_spinner=False)
def fetch_search_data(client_id, client_secret, api_type, query, display=100):
    """
    블로그, 카페글, 뉴스, 쇼핑 검색 API 호출 (단일 키워드 기준)
    """
    endpoint_map = {
        "blog": "blog.json",
        "news": "news.json",
        "cafearticle": "cafearticle.json",
        "shop": "shop.json"
    }
    
    if api_type not in endpoint_map:
        return pd.DataFrame(), "잘못된 API 타입입니다."
        
    url = f"https://openapi.naver.com/v1/search/{endpoint_map[api_type]}"
    headers = {
        "X-Naver-Client-Id": client_id.strip(),
        "X-Naver-Client-Secret": client_secret.strip()
    }
    params = {
        "query": query,
        "display": display,
        "start": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json().get("items", [])
            if items:
                df = pd.DataFrame(items)
                df["search_keyword"] = query
                return df
            else:
                return pd.DataFrame()  # 검색 결과 없음
        else:
            raise Exception(f"오류 발생 (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        raise e

# 쇼핑인사이트에 사용되는 네이버 쇼핑 분야별 카테고리 ID (cid) 매핑 정보
SHOPPING_CATEGORIES = {
    "패션의류": "50000000",
    "패션잡화": "50000001",
    "화장품/미용": "50000002",
    "디지털/가전": "50000003",
    "가구/인테리어": "50000004",
    "출산/육아": "50000005",
    "식품": "50000006",
    "스포츠/레저": "50000007",
    "생활/건강": "50000008",
    "여가/생활편의": "50000009",
    "면세점": "50000010",
    "도서": "50005542"
}

@st.cache_data(show_spinner=False)
def fetch_shopping_insight_trend(client_id, client_secret, categories_list, start_date, end_date):
    """
    네이버 데이터랩 쇼핑인사이트 분야별 트렌드 API 호출
    """
    url = "https://openapi.naver.com/v1/datalab/shopping/categories"
    headers = {
        "X-Naver-Client-Id": client_id.strip(),
        "X-Naver-Client-Secret": client_secret.strip(),
        "Content-Type": "application/json"
    }
    
    category_param = []
    for cat in categories_list[:5]:
        category_param.append({
            "name": cat["name"],
            "param": [cat["cid"]]
        })
        
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "date",
        "category": category_param
    }
    
    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            results = res_json.get("results", [])
            df_list = []
            for group in results:
                title = group.get("title")
                data_points = group.get("data", [])
                for dp in data_points:
                    df_list.append({
                        "period": pd.to_datetime(dp.get("period")),
                        "ratio": dp.get("ratio"),
                        "category_name": title
                    })
            if df_list:
                return pd.DataFrame(df_list)
            else:
                raise Exception("결과 데이터가 비어 있습니다.")
        else:
            raise Exception(f"오류 발생 (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        raise e

def get_merged_search_data(client_id, client_secret, api_type, keywords_list, display=100):
    """
    여러 키워드에 대해 검색 데이터를 수집하고 하나로 병합
    """
    all_dfs = []
    error_msgs = []
    
    for kw in keywords_list:
        try:
            df = fetch_search_data(client_id, client_secret, api_type, kw, display)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            error_msgs.append(f"[{kw}] {str(e)}")
            
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True), error_msgs
    return pd.DataFrame(), error_msgs

# ==============================================================================
# 3. 통계 계산 유틸리티 함수
# ==============================================================================
def calculate_advanced_stats(df, value_col):
    """
    수치형 데이터에 대해 상세 통계 정보를 계산하여 반환
    """
    stats = {}
    if df.empty or value_col not in df.columns:
        return stats
        
    series = pd.to_numeric(df[value_col], errors='coerce').dropna()
    if series.empty:
        return stats
        
    stats["평균 (Mean)"] = series.mean()
    stats["중앙값 (Median)"] = series.median()
    stats["최빈값 (Mode)"] = series.mode().iloc[0] if not series.mode().empty else np.nan
    stats["최소값 (Min)"] = series.min()
    stats["최대값 (Max)"] = series.max()
    stats["표준편차 (Std Dev)"] = series.std()
    stats["왜도 (Skewness)"] = series.skew()
    stats["첨도 (Kurtosis)"] = series.kurt()
    
    # 변동 계수 (Coefficient of Variation)
    mean_val = series.mean()
    stats["변동 계수 (CV)"] = (series.std() / mean_val) if mean_val != 0 else np.nan
    
    # IQR 및 이상치 경계 계산
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    stats["Q1 (25%)"] = q1
    stats["Q3 (75%)"] = q3
    stats["IQR"] = iqr
    stats["이상치 하한선"] = q1 - 1.5 * iqr
    stats["이상치 상한선"] = q3 + 1.5 * iqr
    
    # 이상치 개수
    outliers = series[(series < (q1 - 1.5 * iqr)) | (series > (q3 + 1.5 * iqr))]
    stats["이상치 개수"] = len(outliers)
    
    return stats

# ==============================================================================
# 4. TF-IDF 키워드 분석 함수
# ==============================================================================
def analyze_tfidf_keywords(df, text_cols):
    """
    비정형 텍스트 데이터를 받아 TF-IDF 키워드 분석 후 상위 30개 추출
    """
    if df.empty:
        return pd.DataFrame()
        
    # 텍스트 병합 및 정제
    combined_texts = []
    for _, row in df.iterrows():
        row_text = " ".join([str(row[col]) for col in text_cols if col in df.columns])
        # HTML 태그 제거 및 텍스트 클렌징
        clean_text = re.sub(r'<[^>]*>', ' ', row_text)
        clean_text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', clean_text)
        combined_texts.append(clean_text)
        
    # 데이터가 없거나 텍스트가 모두 공백인 경우 처리
    if not combined_texts or all(len(t.strip()) == 0 for t in combined_texts):
        return pd.DataFrame()
        
    try:
        # TF-IDF 분석 수행 (단순 단어 토크나이저 활용)
        vectorizer = TfidfVectorizer(tokenizer=simple_tokenizer, max_features=100, stop_words=['의', '를', '을', '은', '는', '이', '가', '에', '와', '과', '으로', '로', '하고', '해서'])
        tfidf_matrix = vectorizer.fit_transform(combined_texts)
        
        # 키워드별 평균 TF-IDF 점수 계산
        feature_names = vectorizer.get_feature_names_out()
        mean_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
        
        tfidf_df = pd.DataFrame({
            "키워드": feature_names,
            "TF-IDF 점수": mean_tfidf
        }).sort_values(by="TF-IDF 점수", ascending=False).head(30).reset_index(drop=True)
        
        return tfidf_df
    except Exception:
        # 단어가 충분하지 않는 등의 문제 발생 시 예외 처리
        return pd.DataFrame()

# ==============================================================================
# 5. 사이드바 구성 (설정 및 필터)
# ==============================================================================
with st.sidebar:
    st.title("⚙️ 설정 및 입력")
    
    # 5.1 API Key 설정 정보 표시
    st.subheader("🔑 네이버 API 키 설정")
    if st.session_state["client_id"] and st.session_state["client_secret"]:
        st.success("✅ .env 파일로부터 API 키가 로드되었습니다.")
    else:
        st.error("❌ .env 파일에 API 키가 설정되지 않았습니다.")
        
    st.markdown("---")
    
    # 5.2 공통 검색 필터 설정
    st.subheader("🔍 분석 조건 설정")
    keywords_raw = st.text_input(
        "검색 키워드 (쉼표 ',' 구분)", 
        value="삼성전자, 애플, 엔비디아",
        help="여러 키워드를 비교하려면 쉼표로 구분하여 입력하세요."
    )
    # 키워드 정제
    keywords_list = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    
    # 기간 설정 (최대 1년 범위 권장)
    today = datetime.now().date()
    start_date = st.date_input("시작일", value=today - timedelta(days=90), max_value=today)
    end_date = st.date_input("종료일", value=today, max_value=today)
    
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
        
    st.markdown("---")
    
    # 5.3 페이지 메뉴 구성
    page = st.selectbox(
        "🖥️ 분석 페이지 선택",
        options=[
            "💡 개요 (Overview)",
            "📈 검색어 트렌드 (DataLab)",
            "🛍️ 쇼핑 검색 분석",
            "📊 쇼핑 트렌드 분석",
            "✍️ 블로그 검색 분석",
            "☕ 카페글 검색 분석",
            "📰 뉴스 검색 분석"
        ]
    )

# ==============================================================================
# 6. API Key 검증 경고창
# ==============================================================================
api_keys_ready = bool(st.session_state["client_id"]) and bool(st.session_state["client_secret"])

if not api_keys_ready:
    st.warning("⚠️ 왼쪽 사이드바에서 네이버 API Client ID와 Client Secret을 먼저 입력해 주세요.")
    # API 키가 없으면 개요 페이지로 고정시킴
    page = "💡 개요 (Overview)"

# ==============================================================================
# 7. 페이지별 화면 렌더링
# ==============================================================================

# ------------------------------------------------------------------------------
# 7.1 개요 (Overview) 페이지
# ------------------------------------------------------------------------------
if page == "💡 개요 (Overview)":
    st.title("📊 네이버 API 데이터 수집 및 분석 대시보드")
    st.markdown("""
    네이버 개발자 오픈 API를 활용하여 트렌드 정보와 검색 결과 데이터를 실시간으로 수집하고 통계 분석을 제공하는 대시보드입니다.
    왼쪽 메뉴에서 키워드와 기간을 설정하고 원하는 분석 보고서를 확인해 보세요.
    """)
    
    st.info("💡 **이용 가이드**: 본 애플리케이션은 네이버 비로그인 방식 API를 호출합니다. 사전에 [네이버 개발자 센터](https://developers.naver.com/)에 애플리케이션을 등록하시어 API 키를 발급받으셔야 정상 작동합니다.")
    
    # API 연결 상태 테스트 섹션
    st.subheader("🔗 API 연결 테스트")
    if api_keys_ready:
        if st.button("연결 테스트 시작"):
            with st.spinner("네이버 API와 통신을 확인하는 중..."):
                # 블로그 검색 API로 단순 호출 시도
                try:
                    df = fetch_search_data(
                        st.session_state["client_id"], 
                        st.session_state["client_secret"], 
                        "blog", 
                        "네이버", 
                        display=1
                    )
                    st.success("✅ 네이버 API 인증 및 연결 상태가 정상입니다!")
                except Exception as e:
                    st.error(f"❌ 연결 실패: {str(e)}")
    else:
        st.write("사이드바에 API Key를 입력하면 연결 상태를 검증할 수 있는 테스트 버튼이 활성화됩니다.")

    st.markdown("---")
    st.subheader("📂 수집 대상 문서 및 지원 한도")
    st.markdown("""
    - **검색어 트렌드**: 통합 검색어 트렌드 API (`/v1/datalab/search`, 일 한도 1,000회)
    - **쇼핑 검색**: 쇼핑 검색 API (`/v1/search/shop.json`, 일 한도 25,000회)
    - **블로그 검색**: 블로그 검색 API (`/v1/search/blog.json`, 일 한도 25,000회)
    - **카페글 검색**: 카페글 검색 API (`/v1/search/cafearticle.json`, 일 한도 25,000회)
    - **뉴스 검색**: 뉴스 검색 API (`/v1/search/news.json`, 일 한도 25,000회)
    """)

# ------------------------------------------------------------------------------
# 7.2 검색어 트렌드 (DataLab) 페이지
# ------------------------------------------------------------------------------
elif page == "📈 검색어 트렌드 (DataLab)":
    st.title("📈 네이버 통합 검색어 트렌드 분석")
    st.markdown("네이버 데이터랩 API를 사용하여 입력한 키워드들의 일간 검색 트렌드 추이를 시각화하고 통계적으로 분석합니다.")
    
    if not keywords_list:
        st.warning("분석할 검색 키워드를 입력해 주세요.")
    else:
        df_trend = pd.DataFrame()
        err = None
        with st.spinner("데이터랩 트렌드 데이터를 수집하는 중..."):
            try:
                df_trend = fetch_datalab_trend(
                    st.session_state["client_id"],
                    st.session_state["client_secret"],
                    keywords_list,
                    start_date,
                    end_date
                )
            except Exception as e:
                err = str(e)
            
        if err:
            st.error(err)
        elif df_trend.empty:
            st.info("해당 조건으로 조회된 트렌드 데이터가 없습니다.")
        else:
            # 1) 시각화 - 시계열 검색량 트렌드 라인 차트
            fig = px.line(
                df_trend, 
                x="period", 
                y="ratio", 
                color="keyword",
                title="일자별 상대 검색 비율 추이 (최고점=100)",
                labels={"period": "날짜", "ratio": "검색량 비율 (%)", "keyword": "키워드"}
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
            # 2) 키워드별 상세 통계 분석 및 테이블
            st.markdown("### 📊 키워드별 검색 트렌드 상세 통계 검증")
            
            for kw in df_trend["keyword"].unique():
                kw_df = df_trend[df_trend["keyword"] == kw]
                stats = calculate_advanced_stats(kw_df, "ratio")
                
                if stats:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.subheader(f"🔍 {kw} 통계 지표")
                        stats_df = pd.DataFrame(list(stats.items()), columns=["지표명", "값"])
                        st.dataframe(stats_df.style.format({"값": "{:,.2f}"}), use_container_width=True)
                    with col2:
                        st.subheader(f"📈 {kw} 데이터 분포 및 아웃라이어")
                        fig_box = px.box(
                            kw_df, 
                            y="ratio", 
                            points="all", 
                            title=f"[{kw}] 검색 비율 분포 박스 플롯",
                            labels={"ratio": "검색량 비율 (%)"}
                        )
                        st.plotly_chart(fig_box, use_container_width=True)
                        
                        # 왜도 및 첨도 해석
                        skew = stats.get("왜도 (Skewness)", 0)
                        kurt = stats.get("첨도 (Kurtosis)", 0)
                        interpretation = ""
                        if skew > 1:
                            interpretation += "데이터의 꼬리가 오른쪽으로 긴 형태(검색량이 간헐적으로 급증하는 트렌드)입니다. "
                        elif skew < -1:
                            interpretation += "데이터의 꼬리가 왼쪽으로 긴 형태(대체로 높은 수준을 유지하다가 가끔 하락하는 패턴)입니다. "
                        else:
                            interpretation += "비교적 고른 정규 분포와 유사한 분포를 보입니다. "
                            
                        if kurt > 3:
                            interpretation += "뾰족한 정점을 가지며 극단적인 폭발적 관심(트렌드 급상승 이벤트 등)이 자주 목격되는 집중형 추세입니다."
                        else:
                            interpretation += "완만하고 변동 폭이 부드러운 완만한 추세입니다."
                        
                        st.caption(f"📝 **통계적 해석**: {interpretation}")
                    st.markdown("---")

# ------------------------------------------------------------------------------
# 7.3 쇼핑 검색 분석 페이지
# ------------------------------------------------------------------------------
elif page == "🛍️ 쇼핑 검색 분석":
    st.title("🛍️ 쇼핑 상품 검색 결과 분석")
    st.markdown("네이버 쇼핑 API를 통해 키워드별 인기 상품을 수집하고 가격 분포 및 쇼핑몰별 비중을 분석합니다.")
    
    if not keywords_list:
        st.warning("분석할 검색 키워드를 입력해 주세요.")
    else:
        with st.spinner("쇼핑 데이터를 수집하는 중..."):
            df_shop, errors = get_merged_search_data(
                st.session_state["client_id"],
                st.session_state["client_secret"],
                "shop",
                keywords_list,
                display=100
            )
            
        if errors:
            for err in errors:
                st.error(err)
                
        if df_shop.empty:
            st.info("수집된 쇼핑 데이터가 없습니다.")
        else:
            # 수치 데이터 정제
            df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors='coerce').fillna(0)
            
            # 1) 전체 현황 KPI
            st.markdown("### 🔑 전체 쇼핑 데이터 개요")
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            with kpi_col1:
                st.metric("수집된 총 상품 개수", f"{len(df_shop)} 개")
            with kpi_col2:
                avg_price = df_shop[df_shop["lprice"] > 0]["lprice"].mean()
                st.metric("수집 상품 평균 가격", f"{avg_price:,.0f} 원")
            with kpi_col3:
                top_mall = df_shop["mallName"].mode().iloc[0] if not df_shop["mallName"].empty else "N/A"
                st.metric("가장 많이 등록된 쇼핑몰", top_mall)
                
            st.markdown("---")
            
            # 2) 가격 분포 분석 (Box Plot & Histogram)
            st.markdown("### 💰 상품 최저가(`lprice`) 분포 통계 분석")
            
            fig_hist = px.histogram(
                df_shop[df_shop["lprice"] > 0],
                x="lprice",
                color="search_keyword",
                marginal="box",
                barmode="overlay",
                title="상품 가격 분포 히스토그램 & 박스 플롯",
                labels={"lprice": "최저 가격 (원)", "search_keyword": "검색어"}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 3) 키워드별 상세 통계량 분석
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 키워드별 상세 가격 통계 지표")
                shop_stats_list = []
                for kw in df_shop["search_keyword"].unique():
                    kw_df = df_shop[(df_shop["search_keyword"] == kw) & (df_shop["lprice"] > 0)]
                    stats = calculate_advanced_stats(kw_df, "lprice")
                    if stats:
                        stats["키워드"] = kw
                        shop_stats_list.append(stats)
                if shop_stats_list:
                    df_shop_stats = pd.DataFrame(shop_stats_list).set_index("키워드").T
                    st.dataframe(df_shop_stats.style.format("{:,.1f}"), use_container_width=True)
            
            with col2:
                st.markdown("#### 쇼핑몰 점유율 분석")
                mall_counts = df_shop["mallName"].value_counts().head(10).reset_index()
                fig_mall = px.pie(
                    mall_counts,
                    values="count",
                    names="mallName",
                    title="상위 10개 판매 쇼핑몰 점유율"
                )
                st.plotly_chart(fig_mall, use_container_width=True)

            # 4) 브랜드 및 제조사 파레토 분석 (80/20)
            st.markdown("---")
            st.markdown("### 🏷️ 제조사(Maker) 및 카테고리 집중도 분석 (Pareto Analysis)")
            
            col_brand, col_cat = st.columns(2)
            with col_brand:
                # 제조사 빈도
                maker_df = df_shop[df_shop["maker"].str.strip() != ""]["maker"].value_counts().reset_index()
                if not maker_df.empty:
                    maker_df["누적비율"] = maker_df["count"].cumsum() / maker_df["count"].sum() * 100
                    fig_maker = px.bar(
                        maker_df.head(15),
                        x="maker",
                        y="count",
                        title="상위 15개 인기 제조사 분포",
                        labels={"maker": "제조사", "count": "등록 상품 수"}
                    )
                    st.plotly_chart(fig_maker, use_container_width=True)
                    
                    # 80/20 분석 해석
                    p80_makers = maker_df[maker_df["누적비율"] <= 85]["maker"].tolist()
                    st.caption(f"📝 **제조사 파레토 분석**: 상위 제조사들이 전체 상품 공급의 대부분을 차지합니다. 주요 영향력을 발휘하는 브랜드: {', '.join(p80_makers[:5])} 등")
                else:
                    st.info("제조사 정보가 누락되어 분석을 생략합니다.")
                    
            with col_cat:
                # 카테고리 분포
                cat_df = df_shop[df_shop["category1"].str.strip() != ""]["category1"].value_counts().reset_index()
                if not cat_df.empty:
                    fig_cat = px.pie(
                        cat_df,
                        values="count",
                        names="category1",
                        title="대분류(Category 1) 기준 상품 점유율"
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)
                else:
                    st.info("카테고리 정보가 없어 분석을 생략합니다.")

# ------------------------------------------------------------------------------
# 7.4 쇼핑 트렌드 분석 페이지
# ------------------------------------------------------------------------------
elif page == "📊 쇼핑 트렌드 분석":
    st.title("📊 네이버 쇼핑 트렌드 다차원 분석")
    
    # 탭 구성: 1. 카테고리 클릭 트렌드 (쇼핑인사이트), 2. 상품군 유형 및 가격 분석
    tab_insight, tab_type = st.tabs(["🛍️ 카테고리 클릭 트렌드 (쇼핑인사이트)", "📦 상품군 유형 및 가격 분석"])
    
    with tab_insight:
        st.subheader("🛍️ 네이버 쇼핑 카테고리별 클릭 추이 분석")
        st.markdown("네이버 데이터랩 쇼핑인사이트 API를 통해 주요 쇼핑 분야별 상대적 클릭 관심도 추이를 시각화합니다.")
        
        # 멀티 셀렉트로 카테고리 선택 받기 (최대 5개까지 API 지원)
        default_cats = ["패션의류", "패션잡화", "디지털/가전"]
        selected_cats = st.multiselect(
            "조회할 쇼핑 카테고리 (최대 5개 선택)",
            options=list(SHOPPING_CATEGORIES.keys()),
            default=default_cats,
            help="네이버 데이터랩 API 스펙상 한 번에 최대 5개 분야까지 분석 가능합니다."
        )
        
        if not selected_cats:
            st.warning("분석할 쇼핑 카테고리를 하나 이상 선택해 주세요.")
        else:
            # 카테고리 리스트 가공
            cats_list_to_fetch = [{"name": name, "cid": SHOPPING_CATEGORIES[name]} for name in selected_cats[:5]]
            
            with st.spinner("쇼핑인사이트 데이터를 수집하는 중..."):
                try:
                    df_insight = fetch_shopping_insight_trend(
                        st.session_state["client_id"],
                        st.session_state["client_secret"],
                        cats_list_to_fetch,
                        start_date,
                        end_date
                    )
                    
                    # 1) 시각화 - 시계열 클릭 트렌드 라인 차트
                    fig_insight = px.line(
                        df_insight, 
                        x="period", 
                        y="ratio", 
                        color="category_name",
                        title="분류 분야별 상대적 클릭 관심도 추이 (최고점=100)",
                        labels={"period": "날짜", "ratio": "클릭 비율 (%)", "category_name": "카테고리"}
                    )
                    fig_insight.update_layout(hovermode="x unified")
                    st.plotly_chart(fig_insight, use_container_width=True)
                    
                    # 2) 카테고리별 통계 검증 분석
                    st.markdown("#### 📊 카테고리별 세부 관심도 통계 지표")
                    insight_stats_list = []
                    for cat_name in df_insight["category_name"].unique():
                        cat_df = df_insight[df_insight["category_name"] == cat_name]
                        stats = calculate_advanced_stats(cat_df, "ratio")
                        if stats:
                            stats["카테고리"] = cat_name
                            insight_stats_list.append(stats)
                    if insight_stats_list:
                        df_insight_stats = pd.DataFrame(insight_stats_list).set_index("카테고리").T
                        st.dataframe(df_insight_stats.style.format("{:,.2f}"), use_container_width=True)
                        
                except Exception as e:
                    st.error(f"쇼핑인사이트 API 호출 실패: {str(e)}")
                    
    with tab_type:
        st.subheader("📦 수집된 쇼핑 상품군 유형 및 가격 분석")
        st.markdown("수집된 상품들의 타입(`productType`) 코드 정보와 가격 정보를 매핑하여 구조적인 특징을 분석합니다.")
        
        if not keywords_list:
            st.warning("분석할 검색 키워드를 입력해 주세요.")
        else:
            with st.spinner("쇼핑 상품 데이터를 분석하는 중..."):
                df_shop_trend, errors = get_merged_search_data(
                    st.session_state["client_id"],
                    st.session_state["client_secret"],
                    "shop",
                    keywords_list,
                    display=100
                )
                
            if errors:
                for err in errors:
                    st.error(err)
                    
            if df_shop_trend.empty:
                st.info("수집된 쇼핑 데이터가 없습니다.")
            else:
                # lprice 타입 정제
                df_shop_trend["lprice"] = pd.to_numeric(df_shop_trend["lprice"], errors='coerce').fillna(0)
                # productType 타입 정제
                df_shop_trend["productType"] = pd.to_numeric(df_shop_trend["productType"], errors='coerce').fillna(2)
                
                # 상품군 매핑 정의 (가이드 문서 기준)
                type_mapping = {
                    1: "일반 - 가격비교 매칭",
                    2: "일반 - 가격비교 비매칭",
                    3: "일반 - 가격비교 매칭 일반",
                    4: "중고 - 가격비교 매칭",
                    5: "중고 - 가격비교 비매칭",
                    6: "중고 - 가격비교 매칭 일반",
                    7: "단종 - 가격비교 매칭",
                    8: "단종 - 가격비교 비매칭",
                    9: "단종 - 가격비교 매칭 일반",
                    10: "판매예정 - 가격비교 매칭",
                    11: "판매예정 - 가격비교 비매칭",
                    12: "판매예정 - 가격비교 매칭 일반"
                }
                
                df_shop_trend["상품유형"] = df_shop_trend["productType"].map(type_mapping).fillna("기타/비매칭")
                
                # 상품 대분류군 묶기
                def get_group(ptype):
                    if ptype in [1, 2, 3]: return "일반상품"
                    elif ptype in [4, 5, 6]: return "중고상품"
                    elif ptype in [7, 8, 9]: return "단종상품"
                    elif ptype in [10, 11, 12]: return "판매예정상품"
                    return "기타"
                df_shop_trend["상품대그룹"] = df_shop_trend["productType"].apply(get_group)
                
                # 가격비교 여부 묶기
                def get_comparison(ptype):
                    if ptype in [1, 4, 7, 10]: return "가격비교 상품"
                    elif ptype in [2, 5, 8, 11]: return "가격비교 비매칭"
                    return "가격비교 매칭일반"
                df_shop_trend["가격비교여부"] = df_shop_trend["productType"].apply(get_comparison)
                
                # 1) 상품군 분포 분석 시각화
                col1, col2 = st.columns(2)
                with col1:
                    group_counts = df_shop_trend["상품대그룹"].value_counts().reset_index()
                    fig_group = px.pie(
                        group_counts,
                        values="count",
                        names="상품대그룹",
                        title="상품 대그룹 분류 비율 (일반 vs 중고 vs 단종 등)"
                    )
                    st.plotly_chart(fig_group, use_container_width=True)
                with col2:
                    comp_counts = df_shop_trend["가격비교여부"].value_counts().reset_index()
                    fig_comp = px.pie(
                        comp_counts,
                        values="count",
                        names="가격비교여부",
                        title="가격비교 서비스 연동 상태 비율"
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
                    
                # 2) 상품유형별 가격 트렌드 비교 (Box Plot)
                st.markdown("---")
                st.markdown("### 💸 상품유형별 가격 트렌드 분석")
                
                fig_trend_box = px.box(
                    df_shop_trend[df_shop_trend["lprice"] > 0],
                    x="상품유형",
                    y="lprice",
                    color="search_keyword",
                    title="상세 상품유형별 가격 분포 박스 플롯",
                    labels={"lprice": "가격 (원)", "상품유형": "상품 상세 유형"}
                )
                st.plotly_chart(fig_trend_box, use_container_width=True)
                
                # 유형별 데이터 표 요약
                st.markdown("#### 상품 유형별 통계 요약표")
                summary_tbl = df_shop_trend[df_shop_trend["lprice"] > 0].groupby(["search_keyword", "상품유형"])["lprice"].agg(
                    ["count", "mean", "median", "std", "min", "max"]
                ).rename(columns={
                    "count": "상품수", "mean": "평균가", "median": "중앙가", "std": "표준편차", "min": "최저가", "max": "최고가"
                }).reset_index()
                st.dataframe(summary_tbl.style.format({
                    "평균가": "{:,.0f}", "중앙가": "{:,.0f}", "표준편차": "{:,.0f}", "최저가": "{:,.0f}", "최고가": "{:,.0f}"
                }), use_container_width=True)

# ------------------------------------------------------------------------------
# 7.5 블로그 검색 분석 페이지
# ------------------------------------------------------------------------------
elif page == "✍️ 블로그 검색 분석":
    st.title("✍️ 블로그 검색 결과 트렌드 및 텍스트 분석")
    st.markdown("네이버 블로그 검색 API를 활용하여 검색 키워드별 포스트 트렌드와 본문 텍스트의 TF-IDF 주요 키워드를 정밀 분석합니다.")
    
    if not keywords_list:
        st.warning("분석할 검색 키워드를 입력해 주세요.")
    else:
        with st.spinner("블로그 포스트를 수집하는 중..."):
            df_blog, errors = get_merged_search_data(
                st.session_state["client_id"],
                st.session_state["client_secret"],
                "blog",
                keywords_list,
                display=100
            )
            
        if errors:
            for err in errors:
                st.error(err)
                
        if df_blog.empty:
            st.info("수집된 블로그 데이터가 없습니다.")
        else:
            # 날짜 파싱
            df_blog["postdate_parsed"] = pd.to_datetime(df_blog["postdate"], format="%Y%m%d", errors="coerce")
            
            # 1) 포스팅 시간적 트렌드 시각화
            st.markdown("### 📅 블로그 포스트 작성일 기준 시계열 트렌드")
            if not df_blog["postdate_parsed"].dropna().empty:
                df_time = df_blog.groupby(["postdate_parsed", "search_keyword"]).size().reset_index(name="count")
                fig_time = px.line(
                    df_time,
                    x="postdate_parsed",
                    y="count",
                    color="search_keyword",
                    title="일별 블로그 포스팅 발행 빈도 트렌드",
                    labels={"postdate_parsed": "발행일", "count": "발행 포스트 수", "search_keyword": "키워드"}
                )
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("포스팅 작성일 정보를 읽을 수 없습니다.")
                
            # 2) 텍스트 TF-IDF 키워드 빈도 분석 (스킬 요구사항 반영)
            st.markdown("---")
            st.markdown("### 🔠 블로그 본문 및 제목 TF-IDF 키워드 분석 (상위 30개)")
            
            with st.spinner("TF-IDF 연산 중..."):
                # 제목과 description을 합쳐서 분석
                tfidf_df = analyze_tfidf_keywords(df_blog, ["title", "description"])
                
            if tfidf_df.empty:
                st.info("텍스트 정보가 부족하여 TF-IDF 분석을 진행할 수 없습니다.")
            else:
                col_chart, col_tbl = st.columns([2, 1])
                with col_chart:
                    fig_tfidf = px.bar(
                        tfidf_df.head(15),
                        x="TF-IDF 점수",
                        y="키워드",
                        orientation="h",
                        title="가장 중요도가 높은 본문 핵심 키워드 Top 15 (TF-IDF)",
                        color="TF-IDF 점수"
                    )
                    fig_tfidf.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_tfidf, use_container_width=True)
                with col_tbl:
                    st.markdown("#### 핵심 키워드 Top 30")
                    st.dataframe(tfidf_df, use_container_width=True)
                    
            # 3) 유명 블로거 점유율 분석
            st.markdown("---")
            st.markdown("### 👑 상위 블로거 점유율")
            blogger_counts = df_blog["bloggername"].value_counts().head(10).reset_index()
            fig_blogger = px.bar(
                blogger_counts,
                x="count",
                y="bloggername",
                orientation="h",
                title="가장 활동이 활발한 블로거 Top 10",
                labels={"count": "수집 포스트 수", "bloggername": "블로거 이름"}
            )
            fig_blogger.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_blogger, use_container_width=True)

# ------------------------------------------------------------------------------
# 7.6 카페글 검색 분석 페이지
# ------------------------------------------------------------------------------
elif page == "☕ 카페글 검색 분석":
    st.title("☕ 카페글 검색 결과 트렌드 및 채널 분석")
    st.markdown("네이버 카페글 검색 API를 활용하여 검색 키워드별 카페 채널 점유율과 게시글 내용의 TF-IDF 주요 키워드를 정밀 분석합니다.")
    
    if not keywords_list:
        st.warning("분석할 검색 키워드를 입력해 주세요.")
    else:
        with st.spinner("카페글을 수집하는 중..."):
            df_cafe, errors = get_merged_search_data(
                st.session_state["client_id"],
                st.session_state["client_secret"],
                "cafearticle",
                keywords_list,
                display=100
            )
            
        if errors:
            for err in errors:
                st.error(err)
                
        if df_cafe.empty:
            st.info("수집된 카페글 데이터가 없습니다.")
        else:
            # 1) 카페 채널별 점유율 분석 (Pie Chart)
            st.markdown("### 🏛️ 활성화 카페 채널 점유율 분석")
            col_pie, col_tbl = st.columns([3, 2])
            with col_pie:
                cafe_counts = df_cafe["cafename"].value_counts().head(15).reset_index()
                fig_cafe = px.pie(
                    cafe_counts,
                    values="count",
                    names="cafename",
                    title="상위 15개 인기 네이버 카페 점유율"
                )
                st.plotly_chart(fig_cafe, use_container_width=True)
            with col_tbl:
                st.markdown("#### 상위 20개 인기 카페 리스트")
                cafe_all_counts = df_cafe["cafename"].value_counts().head(20).reset_index()
                st.dataframe(cafe_all_counts, use_container_width=True)
                
            # 2) 텍스트 TF-IDF 키워드 빈도 분석
            st.markdown("---")
            st.markdown("### 🔠 카페글 본문 및 제목 TF-IDF 키워드 분석 (상위 30개)")
            
            with st.spinner("TF-IDF 연산 중..."):
                tfidf_df_cafe = analyze_tfidf_keywords(df_cafe, ["title", "description"])
                
            if tfidf_df_cafe.empty:
                st.info("텍스트 정보가 부족하여 TF-IDF 분석을 진행할 수 없습니다.")
            else:
                col_chart, col_tbl = st.columns([2, 1])
                with col_chart:
                    fig_tfidf_cafe = px.bar(
                        tfidf_df_cafe.head(15),
                        x="TF-IDF 점수",
                        y="키워드",
                        orientation="h",
                        title="카페글 핵심 키워드 Top 15 (TF-IDF)",
                        color="TF-IDF 점수"
                    )
                    fig_tfidf_cafe.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_tfidf_cafe, use_container_width=True)
                with col_tbl:
                    st.markdown("#### 핵심 키워드 Top 30")
                    st.dataframe(tfidf_df_cafe, use_container_width=True)

# ------------------------------------------------------------------------------
# 7.7 뉴스 검색 분석 페이지
# ------------------------------------------------------------------------------
elif page == "📰 뉴스 검색 분석":
    st.title("📰 뉴스 검색 결과 및 언론사 분석")
    st.markdown("네이버 뉴스 검색 API를 활용하여 검색 키워드별 언론사 보도 점유율과 기사 텍스트의 TF-IDF 주요 키워드를 정밀 분석합니다.")
    
    if not keywords_list:
        st.warning("분석할 검색 키워드를 입력해 주세요.")
    else:
        with st.spinner("뉴스 기사를 수집하는 중..."):
            df_news, errors = get_merged_search_data(
                st.session_state["client_id"],
                st.session_state["client_secret"],
                "news",
                keywords_list,
                display=100
            )
            
        if errors:
            for err in errors:
                st.error(err)
                
        if df_news.empty:
            st.info("수집된 뉴스 데이터가 없습니다.")
        else:
            # pubDate 파싱 (예: "Mon, 26 Sep 2016 07:50:00 +0900")
            df_news["pubDate_parsed"] = pd.to_datetime(df_news["pubDate"], errors="coerce")
            
            # 1) 뉴스 보도 시계열 트렌드 시각화
            st.markdown("### 📅 뉴스 보도 시간적 트렌드")
            if not df_news["pubDate_parsed"].dropna().empty:
                df_time_news = df_news.groupby([df_news["pubDate_parsed"].dt.date, "search_keyword"]).size().reset_index(name="count")
                fig_time_news = px.line(
                    df_time_news,
                    x="pubDate_parsed",
                    y="count",
                    color="search_keyword",
                    title="일별 뉴스 기사 보도 빈도 트렌드",
                    labels={"pubDate_parsed": "보도일", "count": "기사 수", "search_keyword": "키워드"}
                )
                st.plotly_chart(fig_time_news, use_container_width=True)
            else:
                st.info("보도시간 정보를 파싱할 수 없습니다.")
                
            # 2) 텍스트 TF-IDF 키워드 빈도 분석
            st.markdown("---")
            st.markdown("### 🔠 뉴스 기사 본문 및 제목 TF-IDF 키워드 분석 (상위 30개)")
            
            with st.spinner("TF-IDF 연산 중..."):
                tfidf_df_news = analyze_tfidf_keywords(df_news, ["title", "description"])
                
            if tfidf_df_news.empty:
                st.info("텍스트 정보가 부족하여 TF-IDF 분석을 진행할 수 없습니다.")
            else:
                col_chart, col_tbl = st.columns([2, 1])
                with col_chart:
                    fig_tfidf_news = px.bar(
                        tfidf_df_news.head(15),
                        x="TF-IDF 점수",
                        y="키워드",
                        orientation="h",
                        title="뉴스 기사 핵심 키워드 Top 15 (TF-IDF)",
                        color="TF-IDF 점수"
                    )
                    fig_tfidf_news.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_tfidf_news, use_container_width=True)
                with col_tbl:
                    st.markdown("#### 핵심 키워드 Top 30")
                    st.dataframe(tfidf_df_news, use_container_width=True)
                    
            # 3) 언론사 점유율 분석
            st.markdown("---")
            st.markdown("### 📢 주요 언론사별 보도 점유율")
            
            # 네이버 뉴스는 link와 originallink가 있음. 도메인 기반 언론사 추출
            def extract_domain(url):
                if not url: return "기타"
                match = re.search(r'https?://([^/]+)', url)
                if match:
                    domain = match.group(1)
                    return domain.replace("www.", "")
                return "기타"
            
            df_news["언론사도메인"] = df_news["originallink"].apply(extract_domain)
            media_counts = df_news["언론사도메인"].value_counts().head(15).reset_index()
            
            col_media_chart, col_media_tbl = st.columns([3, 2])
            with col_media_chart:
                fig_media = px.pie(
                    media_counts,
                    values="count",
                    names="언론사도메인",
                    title="상위 15개 언론사(도메인 기준) 보도 점유율"
                )
                st.plotly_chart(fig_media, use_container_width=True)
            with col_media_tbl:
                st.markdown("#### 보도 언론사 순위")
                st.dataframe(df_news["언론사도메인"].value_counts().head(20).reset_index(), use_container_width=True)
