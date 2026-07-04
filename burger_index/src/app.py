"""
이 스크립트는 대한민국 버거 브랜드 분포 및 버거지수 데이터를 탐색하고 시각화하는
Streamlit 다중 페이지 대시보드 웹 애플리케이션입니다.

- 페이지 1: 기본 EDA (Plotly 기반 차트 및 데이터 테이블)
- 페이지 2: 위치 기준 버거지수 산점도 지도 (Folium CircleMarker 및 주요 도시 텍스트 상시 표시)
- 페이지 3: 행정구역별 버거지수 단계구분도 (Folium Choropleth 및 GeoJSON 기반 호버 툴팁 연동)
- 페이지 4: 전국 시군구 카토그램 시각화 (행정구역 격자 맵 기반 버거지수 2D 시각화)

- 작성일: 2026-07-04
"""

import os
import requests
import numpy as np
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm

# Matplotlib 한글 깨짐 방지: 맑은 고딕 절대 경로 강제 등록
font_path = "C:/Windows/Fonts/malgun.ttf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
else:
    # 예외 처리: 시스템 한글 고딕 폰트 검색
    h_fonts = [f.name for f in fm.fontManager.ttflist if 'Gothic' in f.name or 'Malgun' in f.name]
    if h_fonts:
        plt.rcParams['font.family'] = h_fonts[0]
        plt.rcParams['axes.unicode_minus'] = False


# 0. Streamlit 기본 환경 설정 및 스타일 커스터마이징 (프리미엄 다크 무드 적용)
st.set_page_config(
    page_title="대한민국 버거지수 대시보드",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세련된 CSS 스타일 주입
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
    }
    div[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    div[data-testid="stMetricValue"] {
        color: #f59e0b;
        font-size: 2rem;
        font-weight: 700;
    }
    .css-1dp5440 {
        font-family: 'Pretendard', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# 1. 데이터 로드 및 전처리 함수 캐싱
@st.cache_data
def load_data():
    crosstab_path = 'burger_index/data/city_brand_crosstab.csv'
    burger_path = 'burger_index/data/burger.csv'
    
    if not os.path.exists(crosstab_path) or not os.path.exists(burger_path):
        return None, None
        
    df = pd.read_csv(crosstab_path, encoding='utf-8-sig')
    burger_df = pd.read_csv(burger_path, encoding='utf-8')
    
    # 컬럼명 리네임 일치화
    df = df.rename(columns={'위도': '위도_중앙값', '경도': '경도_중앙값'})
    
    # 2. burger.csv로부터 시도시군구명별 시군구코드(5자리) 추출 및 매핑
    burger_df['정제_시도명'] = burger_df['정제_시도명'].fillna('')
    burger_df['정제_시군구명'] = burger_df['정제_시군구명'].fillna('')
    burger_df['시도시군구명'] = (burger_df['정제_시도명'] + ' ' + burger_df['정제_시군구명']).str.strip()
    
    # 시도시군구명과 시군구코드 매핑 딕셔너리 구성
    code_map = burger_df.groupby('시도시군구명')['시군구코드'].first().astype(str).to_dict()
    
    # 교차표 데이터프레임에 시군구코드 열 매핑 추가
    df['시군구코드'] = df['시도시군구명'].map(code_map)
    
    # 시도명 파생변수 생성
    df['시도명'] = df['시도시군구명'].apply(lambda x: x.split()[0] if isinstance(x, str) else '')
    
    # 각 시도별 버거지수가 가장 높은 1위 대표 지역 마킹 (텍스트 겹침 방지 라벨용)
    plot_df = df[df['시도시군구명'] != '합계'].dropna(subset=['버거지수', '위도_중앙값', '경도_중앙값']).copy()
    major_indices = plot_df.groupby('시도명')['버거지수'].idxmax()
    df['주요도시_여부'] = False
    df.loc[major_indices, '주요도시_여부'] = True
    
    return df, burger_df

@st.cache_data
def load_geojson():
    # KOSTAT 2013 대한민국 시군구 행정구역 GeoJSON 다운로드
    url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"GeoJSON 데이터를 다운로드하는 중 오류가 발생했습니다: {e}")
    return None

# 데이터 로드 실행
df, burger_df = load_data()
geojson_data = load_geojson()

@st.cache_data
def load_cartogram_data(crosstab_df):
    local_path = 'burger_index/data/data_draw_korea.csv'
    url = "https://raw.githubusercontent.com/ynicekyhh/analysis_chickenfranchise/master/__test__/data_draw_korea.csv"
    
    if not os.path.exists(local_path):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                os.makedirs('burger_index/data', exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(r.content)
            else:
                st.error("카토그램 격자 데이터를 다운로드하지 못했습니다.")
                return None
        except Exception as e:
            st.error(f"카토그램 격자 데이터 다운로드 오류: {e}")
            return None
            
    draw_df = pd.read_csv(local_path, index_col=0, encoding='utf-8')
    
    # 조인 집계 처리
    c_df = crosstab_df[crosstab_df['시도시군구명'] != '합계'].copy()
    
    def split_city(name):
        if not isinstance(name, str):
            return "", "", ""
        parts = name.split()
        sido = parts[0]
        sigungu = parts[1] if len(parts) > 1 else ""
        detail = parts[2] if len(parts) > 2 else ""
        return sido, sigungu, detail
        
    c_df['sido'], c_df['sigungu'], c_df['detail'] = zip(*c_df['시도시군구명'].apply(split_city))
    
    stats_list = []
    for idx, row in draw_df.iterrows():
        draw_sido = row['광역시도']
        draw_guyu = row['행정구역']
        
        # 광역시도 매칭 (앞 2글자)
        sido_prefix = draw_sido[:2]
        matched_sido = c_df[c_df['sido'].str.startswith(sido_prefix)]
        
        # 행정구역 매칭
        matched = matched_sido[matched_sido['sigungu'] == draw_guyu]
        
        # 구 단위 데이터가 crosstab에 분리된 행정시 통합 집계
        if len(matched) == 0:
            matched = matched_sido[matched_sido['sigungu'].str.startswith(draw_guyu) | matched_sido['sigungu'].str.contains(draw_guyu)]
            
        if len(matched) == 0:
            if draw_sido.startswith('세종') or draw_guyu == '세종시':
                matched = matched_sido[matched_sido['sido'].str.startswith('세종')]
                
        if len(matched) > 0:
            lotteria = matched['롯데리아'].sum()
            mcdonald = matched['맥도날드'].sum()
            burgerking = matched['버거킹'].sum()
            kfc = matched['KFC'].sum()
            total = matched['합계'].sum()
            
            if lotteria > 0:
                burger_idx = (burgerking + mcdonald + kfc) / lotteria
            else:
                burger_idx = np.nan
        else:
            lotteria = 0
            mcdonald = 0
            burgerking = 0
            kfc = 0
            total = 0
            burger_idx = np.nan
            
        stats_list.append({
            'shortName': row['shortName'],
            'x': int(row['x']),
            'y': int(row['y']),
            '롯데리아': int(lotteria),
            '맥도날드': int(mcdonald),
            '버거킹': int(burgerking),
            'KFC': int(kfc),
            '합계': int(total),
            '버거지수': burger_idx
        })
        
    return pd.DataFrame(stats_list)

carto_df = load_cartogram_data(df)

if df is None:
    st.error("데이터 파일을 불러오지 못했습니다. 경로를 확인해 주세요.")
    st.stop()

# 2. 사이드바 메뉴 구성
st.sidebar.title("🍔 버거지수 대시보드")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "메뉴 선택",
    ["1) 기본 EDA", "2) 위치 기준 산점도 지도", "3) 행정구역별 단계구분도", "4) 전국 시군구 카토그램"]
)


# 전국 합계 행 및 일반 시군구 행 분리
national_summary = df[df['시도시군구명'] == '합계'].iloc[0]
city_df = df[df['시도시군구명'] != '합계'].copy()
# 결측치 없는 시각화용 데이터프레임
plot_df = city_df.dropna(subset=['버거지수', '위도_중앙값', '경도_중앙값']).copy()

# ==========================================
# PAGE 1: 기본 EDA
# ==========================================
if page == "1) 기본 EDA":
    st.header("📊 전국 버거 매장 현황 및 EDA")
    st.markdown("전국 4대 버거 브랜드(롯데리아, 맥도날드, 버거킹, KFC)의 매장수 통계와 버거지수 분포를 탐색합니다.")
    
    # 핵심 지표 카드 영역
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="🍔 전국 평균 버거지수", value=f"{national_summary['버거지수']:.4f}")
    with col2:
        st.metric(label="🔴 롯데리아 매장 수", value=f"{int(national_summary['롯데리아']):,}개")
    with col3:
        st.metric(label="🟡 맥도날드 매장 수", value=f"{int(national_summary['맥도날드']):,}개")
    with col4:
        st.metric(label="🟤 버거킹 매장 수", value=f"{int(national_summary['버거킹']):,}개")
    with col5:
        st.metric(label="🔴 KFC 매장 수", value=f"{int(national_summary['KFC']):,}개")

    st.markdown("---")
    
    # 2열 시각화 레이아웃
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🍕 4대 버거 브랜드 전국 점유율")
        brand_data = pd.DataFrame({
            '브랜드': ['롯데리아', '맥도날드', '버거킹', 'KFC'],
            '매장수': [national_summary['롯데리아'], national_summary['맥도날드'], national_summary['버거킹'], national_summary['KFC']]
        })
        fig_pie = px.pie(
            brand_data, 
            values='매장수', 
            names='브랜드', 
            color='브랜드',
            color_discrete_map={
                '롯데리아': '#e74c3c',
                '맥도날드': '#f1c40f',
                '버거킹': '#e67e22',
                'KFC': '#c0392b'
            },
            hole=0.4
        )
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#f3f4f6')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with chart_col2:
        st.subheader("📈 시도별 평균 버거지수 순위")
        # 시도별 평균 버거지수 계산 (결측치 제외)
        sido_index = plot_df.groupby('시도명')['버거지수'].mean().reset_index()
        sido_index = sido_index.sort_values(by='버거지수', ascending=False)
        
        fig_bar = px.bar(
            sido_index,
            x='시도명',
            y='버거지수',
            color='버거지수',
            color_continuous_scale='YlOrRd',
            labels={'버거지수': '평균 버거지수'}
        )
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#f3f4f6')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    
    # 버거지수 분포 히스토그램 및 데이터 브라우저
    dist_col, table_col = st.columns([1, 1.2])
    
    with dist_col:
        st.subheader("📊 전국 시군구별 버거지수 분포")
        fig_hist = px.histogram(
            plot_df,
            x='버거지수',
            nbins=30,
            color_discrete_sequence=['#fd8d3c'],
            labels={'count': '시군구 수'}
        )
        fig_hist.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font_color='#f3f4f6',
            xaxis_title="버거지수",
            yaxis_title="시군구 수"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with table_col:
        st.subheader("🔍 지역별 버거 데이터 테이블 검색기")
        search_query = st.text_input("도시명으로 검색 (예: 강릉, 분당, 강남)", "")
        
        display_df = city_df[['시도시군구명', 'KFC', '롯데리아', '맥도날드', '버거킹', '합계', '버거지수']].copy()
        
        if search_query:
            display_df = display_df[display_df['시도시군구명'].str.contains(search_query, na=False)]
            
        st.dataframe(
            display_df.sort_values(by='버거지수', ascending=False).style.format({'버거지수': '{:.4f}'}),
            use_container_width=True,
            height=300
        )

# ==========================================
# PAGE 2: 위치 기준 산점도 지도
# ==========================================
elif page == "2) 위치 기준 산점도 지도":
    st.header("📍 위경도 좌표 기준 버거지수 위치 산점도")
    st.markdown("대한민국 지도 위에 버거지수 규모를 원형 마커로 시각화합니다. 크기가 크고 붉을수록 버거지수가 높은 지역입니다.")

    # 1. 지도 생성
    m = folium.Map(location=[36.2, 127.8], zoom_start=7, tiles="Cartodb Positron")

    # 버거지수별 마커 색상 정의
    def get_color(val):
        if pd.isna(val):
            return '#9ca3af'
        return '#bd0026' if val >= 1.5 else \
               '#f03b20' if val >= 1.0 else \
               '#fd8d3c' if val >= 0.5 else \
               '#fed976'

    # 2. 데이터 마커 추가
    for _, row in plot_df.iterrows():
        val = row['버거지수']
        radius = min(4 + (val * 6), 24)
        color = get_color(val)
        
        # 상세 매장현황 팝업 구성
        popup_html = f"""
        <div style="font-family: 'Malgun Gothic', sans-serif; font-size: 12px; width: 180px;">
            <b style="font-size: 14px; color: #1e293b;">{row['시도시군구명']}</b><hr style="margin: 5px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td><b>버거지수:</b></td><td style="color:#e67e22; font-weight:bold; text-align:right;">{val:.4f}</td></tr>
                <tr><td><b>총 매장수:</b></td><td style="text-align:right;">{int(row['합계'])}개</td></tr>
                <tr><td colspan="2"><hr style="margin: 3px 0; border: 0.5px solid #eee;"></td></tr>
                <tr><td>롯데리아:</td><td style="text-align:right;">{int(row['롯데리아'])}개</td></tr>
                <tr><td>맥도날드:</td><td style="text-align:right;">{int(row['맥도날드'])}개</td></tr>
                <tr><td>버거킹:</td><td style="text-align:right;">{int(row['버거킹'])}개</td></tr>
                <tr><td>KFC:</td><td style="text-align:right;">{int(row['KFC'])}개</td></tr>
            </table>
        </div>
        """
        
        # CircleMarker 드로잉
        folium.CircleMarker(
            location=[row['위도_중앙값'], row['경도_중앙값']],
            radius=radius,
            fill=True,
            fill_color=color,
            color='#ffffff',
            weight=0.5,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{row['시도시군구명']} (버거지수: {val:.2f})"
        ).add_to(m)

        # 3. 요구사항 1: 텍스트 겹침을 방지하기 위해 시도별 1위 '주요 도시' 이름표 상시 표시
        if row['주요도시_여부']:
            # L.divIcon 스타일을 적용한 상시 마커 배치
            clean_name = row['시도시군구명'].split()[-1]  # '강릉시', '분당구' 등만 추출해 깔끔하게 표기
            icon_html = f"""
            <div style="
                font-family: 'Malgun Gothic', sans-serif;
                font-size: 9px;
                font-weight: bold;
                color: #ffffff;
                background-color: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 2px 4px;
                white-space: nowrap;
                box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
                display: inline-block;
            ">
                {clean_name} ({val:.2f})
            </div>
            """
            folium.Marker(
                location=[row['위도_중앙값'], row['경도_중앙값']],
                icon=folium.DivIcon(
                    icon_anchor=(-10, 5),  # 마커 오른쪽 살짝 옆으로 라벨 이동
                    html=icon_html
                )
            ).add_to(m)

    # 4. 지도 출력
    st_folium(m, width=1100, height=650, returned_objects=[])

# ==========================================
# PAGE 3: 행정구역별 단계구분도
# ==========================================
elif page == "3) 행정구역별 단계구분도":
    st.header("🗺️ 행정구역별 버거지수 단계구분도 (Choropleth Map)")
    st.markdown("대한민국 통계청 시군구 행정경계(GeoJSON) 데이터와 연동하여, 행정구역 경계선별 버거지수를 단계별 색상으로 분석합니다.")

    if geojson_data is None:
        st.error("행정구역 GeoJSON 데이터를 로드할 수 없습니다. 인터넷 연결 및 소스를 확인해 주세요.")
    else:
        # GeoJSON 데이터 전처리 (시군구 코드 기준으로 버거지수 및 전체 지역명을 Feature Properties에 직접 주입)
        idx_dict = plot_df.set_index('시군구코드')['버거지수'].to_dict()
        name_dict = plot_df.set_index('시군구코드')['시도시군구명'].to_dict()
        
        for feature in geojson_data['features']:
            code = feature['properties']['code']
            feature['properties']['burger_index'] = idx_dict.get(code, np.nan)
            feature['properties']['full_name'] = name_dict.get(code, feature['properties']['name'])

        # 1. 지도 초기화
        m = folium.Map(location=[36.2, 127.8], zoom_start=7, tiles="Cartodb Positron")

        # 2. Choropleth 레이어 얹기
        choropleth = folium.Choropleth(
            geo_data=geojson_data,
            data=plot_df,
            columns=['시군구코드', '버거지수'],
            key_on='feature.properties.code',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name='버거지수',
            highlight=True
        ).add_to(m)

        # 3. 호버(Hover) 시 세련된 툴팁 렌더링을 위해 투명한 GeoJson 레이어 오버레이 배치
        folium.GeoJson(
            geojson_data,
            style_function=lambda x: {
                'fillColor': '#ffffff',
                'color': '#000000',
                'fillOpacity': 0.0,  # 완전히 투명하게 설정하여 색상은 Choropleth를 보여줌
                'weight': 0.1
            },
            highlight_function=lambda x: {
                'fillColor': '#ffffff',
                'color': '#2c3e50',
                'fillOpacity': 0.1,
                'weight': 1.5
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['full_name', 'burger_index'],
                aliases=['행정구역:', '버거지수:'],
                localize=True,
                sticky=True,
                labels=True,
                style="""
                    background-color: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    color: #f3f4f6;
                    font-family: 'Malgun Gothic', sans-serif;
                    font-size: 12px;
                    padding: 8px;
                """
            )
        ).add_to(m)

        # 4. 지도 출력
        st_folium(m, width=1100, height=650, returned_objects=[])

# ==========================================
# PAGE 4: 전국 시군구 카토그램
# ==========================================
elif page == "4) 전국 시군구 카토그램":
    st.header("🗺️ 전국 시군구 단위 버거지수 카토그램 (Cartogram)")
    st.markdown("각 시군구를 동일한 크기의 정방형 격자로 정렬하여, 지리적 면적의 왜곡 없이 전국 버거지수 분포를 균등한 스케일로 시각화합니다.")

    # 1. Matplotlib를 이용한 카토그램 그리기
    @st.cache_resource
    def generate_cartogram_plot(_data):
        # 다크 테마에 맞는 피규어 생성
        fig, ax = plt.subplots(figsize=(8, 12), facecolor='#0b0f19')
        ax.set_facecolor('#0b0f19')
        
        xmax = _data['x'].max() + 1
        ymax = _data['y'].max() + 1
        
        # 캡처와 가장 매칭도가 높은 'Blues' 컬러맵 사용
        cmap = plt.cm.Blues
        
        # 1) 각 격자 셀 그리기
        for _, row in _data.iterrows():
            x, y = int(row['x']), int(row['y'])
            val = row['버거지수']
            name = row['shortName']
            
            # 결측치(NaN) 처리
            if pd.isna(val):
                color = '#334155'  # 결측치는 세련된 어두운 회색
                text_color = '#94a3b8'
                display_val = "NaN"
            else:
                # 0.0 ~ 3.0 스케일로 노멀라이즈
                norm_val = min(max(val / 3.0, 0.0), 1.0)
                color = mcolors.to_hex(cmap(norm_val * 0.85 + 0.15)) # 색 대비 확보
                text_color = '#ffffff' if norm_val > 0.45 else '#0f172a'
                display_val = f"{val:.2f}"
                
            # 격자 사각형 그리기
            rect = plt.Rectangle(
                (x - 0.5, y - 0.5), 1.0, 1.0,
                facecolor=color, edgecolor='#1e293b', linewidth=0.8
            )
            ax.add_patch(rect)
            
            # 텍스트 라벨 추가
            # 줄바꿈 정제
            if '(' in name:
                clean_name = name.replace('(', '\n(')
            elif len(name) > 3:
                clean_name = name[:2] + '\n' + name[2:]
            else:
                clean_name = name
                
            # 지역명
            ax.text(
                x, y - 0.08, clean_name,
                ha='center', va='center', fontsize=7.5,
                color=text_color, fontweight='bold'
            )
            # 버거지수
            ax.text(
                x, y + 0.28, display_val,
                ha='center', va='center', fontsize=6.2,
                color=text_color, alpha=0.9
            )
            
        # 2) 주요 광역 권역 경계선 그리기 (굵은 실선)
        BORDER_LINES = [
            # 서울
            [(4.5, 4.5), (6.5, 4.5), (6.5, 6.5), (4.5, 6.5), (4.5, 4.5)],
            # 인천
            [(1.5, 3.5), (1.5, 5.5), (2.5, 5.5), (2.5, 6.5), (0.5, 6.5), (0.5, 7.5), (1.5, 7.5), (1.5, 6.5)],
            # 광주
            [(2.5, 18.5), (2.5, 21.5), (3.5, 21.5), (3.5, 18.5), (2.5, 18.5)],
            # 대구
            [(8.5, 13.5), (8.5, 16.5), (10.5, 16.5), (10.5, 13.5), (8.5, 13.5)],
            # 부산/울산
            [(9.5, 17.5), (9.5, 20.5), (11.5, 20.5), (11.5, 17.5), (9.5, 17.5)]
        ]
        
        for line in BORDER_LINES:
            xs, ys = zip(*line)
            ax.plot(xs, ys, color='#1e293b', linewidth=2.5)
            
        ax.set_xlim(-0.6, xmax - 0.4)
        ax.set_ylim(-0.6, ymax - 0.4)
        ax.invert_yaxis()  # y=0이 맨 위가 되도록 축 반전
        ax.axis('off')
        
        # 3) 범례(Colorbar) 바배치
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0.0, vmax=3.0))
        sm._A = []
        cb = fig.colorbar(sm, ax=ax, shrink=0.45, aspect=15, pad=0.03, orientation='vertical')
        cb.ax.yaxis.set_tick_params(color='#f3f4f6')
        cb.ax.tick_params(labelsize=8, labelcolor='#f3f4f6')
        cb.set_label('버거지수', color='#f3f4f6', fontsize=9, fontweight='bold', labelpad=8)
        cb.outline.set_visible(False)
        
        return fig

    # 차트 출력
    fig = generate_cartogram_plot(carto_df)
    st.pyplot(fig)

    st.markdown("---")
    
    # 카토그램 통합 시군구 데이터 테이블
    st.subheader("🔍 카토그램 격자 원천 데이터 브라우저")
    search_q = st.text_input("지역명으로 검색 (예: 수원, 고양, 강릉)", "")
    
    display_carto = carto_df.copy()
    if search_q:
        display_carto = display_carto[display_carto['shortName'].str.contains(search_q, na=False)]
        
    st.dataframe(
        display_carto.sort_values(by='버거지수', ascending=False).style.format({'버거지수': '{:.4f}'}),
        use_container_width=True,
        height=300
    )

