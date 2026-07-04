"""
이 스크립트는 city_brand_crosstab.csv 데이터를 기반으로 한국 지도상에 버거지수 분포를 시각화한
인터랙티브 웹 대시보드(HTML)를 생성합니다.

- 입력 파일: burger_index/data/city_brand_crosstab.csv
- 출력 파일: burger_index/report/dashboard.html
- 작성일: 2026-07-04
"""

import os
import json
import requests
import pandas as pd
import numpy as np

def generate_dashboard():
    csv_path = 'burger_index/data/city_brand_crosstab.csv'
    burger_csv = 'burger_index/data/burger.csv'
    output_dir = 'burger_index/report'
    output_html = os.path.join(output_dir, 'dashboard.html')

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} 파일이 존재하지 않습니다.")
        return

    # 데이터 로드
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 컬럼 정제 및 결측치 제거
    df = df.rename(columns={'위도': '위도_중앙값', '경도': '경도_중앙값'})
    plot_df = df.dropna(subset=['위도_중앙값', '경도_중앙값', '버거지수'])
    plot_df = plot_df[plot_df['시도시군구명'] != '합계'].copy()

    # 각 시도(서울, 경기 등)별 버거지수가 가장 높은 1위 대표 지역 추출 (텍스트 겹침 방지용)
    plot_df['시도명'] = plot_df['시도시군구명'].apply(lambda x: x.split()[0])
    major_indices = plot_df.groupby('시도명')['버거지수'].idxmax()
    plot_df['주요도시_여부'] = False
    plot_df.loc[major_indices, '주요도시_여부'] = True

    # burger.csv를 이용하여 시도시군구명별 시군구코드(5자리) 추출 및 매핑
    code_map = {}
    if os.path.exists(burger_csv):
        burger_df = pd.read_csv(burger_csv, encoding='utf-8')
        burger_df['정제_시도명'] = burger_df['정제_시도명'].fillna('')
        burger_df['정제_시군구명'] = burger_df['정제_시군구명'].fillna('')
        burger_df['시도시군구명'] = (burger_df['정제_시도명'] + ' ' + burger_df['정제_시군구명']).str.strip()
        code_map = burger_df.groupby('시도시군구명')['시군구코드'].first().astype(str).to_dict()
    
    plot_df['시군구코드'] = plot_df['시도시군구명'].map(code_map).fillna('')

    # GeoJSON 데이터 다운로드 및 캐싱
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_municipalities_geo.json"
    geojson_dir = 'burger_index/data'
    geojson_path = os.path.join(geojson_dir, 'skorea_municipalities_geo.json')
    geojson_data = None

    if os.path.exists(geojson_path):
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            print("로컬 GeoJSON 캐시 파일을 성공적으로 불러왔습니다.")
        except Exception as e:
            print(f"로컬 GeoJSON 캐시 로드 중 오류 발생: {e}")

    if geojson_data is None:
        print("GeoJSON 데이터를 원격 저장소에서 다운로드합니다...")
        try:
            response = requests.get(geojson_url, timeout=15)
            if response.status_code == 200:
                geojson_data = response.json()
                os.makedirs(geojson_dir, exist_ok=True)
                with open(geojson_path, 'w', encoding='utf-8') as f:
                    json.dump(geojson_data, f, ensure_ascii=False)
                print("GeoJSON 데이터 다운로드 및 캐싱 성공.")
            else:
                print(f"GeoJSON 다운로드 실패 (상태코드: {response.status_code})")
        except Exception as e:
            print(f"GeoJSON 다운로드 중 오류 발생: {e}")

    geojson_json = json.dumps(geojson_data, ensure_ascii=False) if geojson_data else "null"

    # HTML에 삽입할 JSON 데이터 포맷 변환
    records = []
    for _, row in plot_df.iterrows():
        records.append({
            'city': row['시도시군구명'],
            'code': str(row['시군구코드']),
            'kfc': int(row['KFC']),
            'lotteria': int(row['롯데리아']),
            'mcdonald': int(row['맥도날드']),
            'burgerking': int(row['버거킹']),
            'total': int(row['합계']),
            'index': float(row['버거지수']),
            'lat': float(row['위도_중앙값']),
            'lng': float(row['경도_중앙값']),
            'is_major': bool(row['주요도시_여부'])
        })

    json_data = json.dumps(records, ensure_ascii=False)

    # 전국 요약 통계 계산
    national_kfc = int(df.loc[df['시도시군구명'] == '합계', 'KFC'].values[0])
    national_lotteria = int(df.loc[df['시도시군구명'] == '합계', '롯데리아'].values[0])
    national_mcdonald = int(df.loc[df['시도시군구명'] == '합계', '맥도날드'].values[0])
    national_burgerking = int(df.loc[df['시도시군구명'] == '합계', '버거킹'].values[0])
    national_total = int(df.loc[df['시도시군구명'] == '합계', '합계'].values[0])
    national_index = float(df.loc[df['시도시군구명'] == '합계', '버거지수'].values[0])

    # 버거지수 기준 Top 10 시군구 정렬
    top_10 = plot_df.sort_values(by='버거지수', ascending=False).head(10)
    top_10_records = []
    for idx, row in top_10.iterrows():
        top_10_records.append({
            'city': row['시도시군구명'],
            'index': float(row['버거지수']),
            'total': int(row['합계'])
        })
    top_10_json = json.dumps(top_10_records, ensure_ascii=False)

    # 시도별 평균 버거지수 계산 (차트 시각화용)
    sido_avg = plot_df.groupby('시도명')['버거지수'].mean().reset_index()
    sido_avg = sido_avg.sort_values(by='버거지수', ascending=False)
    sido_avg_records = []
    for idx, row in sido_avg.iterrows():
        sido_avg_records.append({
            'sido': row['시도명'],
            'index': float(row['버거지수'])
        })
    sido_avg_json = json.dumps(sido_avg_records, ensure_ascii=False)

    # 브랜드 및 버거지수 시도시군구별 기술통계 계산 (평균, 중앙값, 표준편차, 최소, 최대, 왜도, 첨도)
    stats_cols = [
        ('롯데리아', '롯데리아'),
        ('맥도날드', '맥도날드'),
        ('버거킹', '버거킹'),
        ('KFC', 'KFC'),
        ('버거지수', '버거지수')
    ]
    stats_records = []
    for col_key, label in stats_cols:
        series = plot_df[col_key]
        stats_records.append({
            'brand': label,
            'mean': float(series.mean()),
            'median': float(series.median()),
            'std': float(series.std()),
            'min': float(series.min()),
            'max': float(series.max()),
            'skew': float(series.skew()),
            'kurt': float(series.kurt())
        })
    stats_json = json.dumps(stats_records, ensure_ascii=False)


    # HTML 템플릿 코드 작성
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>대한민국 버거지수 대시보드</title>
    <!-- Tailwind CSS (프리미엄 UI/스타일용) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Leaflet CSS & JS (지도용) -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <!-- Chart.js (인터랙티브 통계 그래프용) -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Google Fonts (Pretendard 스타일 폰트) -->
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    
    <style>
        body {{
            font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
            background-color: #0b0f19;
            color: #f3f4f6;
        }}
        /* 스크롤바 커스텀 */
        ::-webkit-scrollbar {{
            width: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: #0f172a;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #334155;
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #475569;
        }}
        /* Leaflet 라벨 스타일 */
        .leaflet-tooltip-own {{
            background: rgba(15, 23, 42, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
            font-weight: 500 !important;
            font-size: 11px !important;
            border-radius: 6px !important;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3) !important;
            padding: 6px 10px !important;
        }}
        .leaflet-tooltip-left:before, .leaflet-tooltip-right:before {{
            border: none !important;
        }}
        /* 팝업 스타일링 */
        .leaflet-popup-content-wrapper {{
            background: #1e293b !important;
            color: #f3f4f6 !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.5) !important;
            padding: 4px !important;
        }}
        .leaflet-popup-content {{
            margin: 8px 12px !important;
        }}
        .leaflet-popup-tip {{
            background: #1e293b !important;
        }}
        
        /* 커스텀 범례(Legend) 스타일 */
        .map-legend {{
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 10px;
            color: #f3f4f6;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3);
            backdrop-filter: blur(8px);
        }}
        .legend-gradient {{
            background: linear-gradient(to right, #fed976, #fd8d3c, #f03b20, #bd0026);
            height: 12px;
            border-radius: 4px;
        }}
    </style>
</head>
<body class="h-screen w-screen flex overflow-hidden">

    <!-- 좌측 사이드바 (메뉴 및 옵션) -->
    <aside class="w-64 bg-[#111827] border-r border-gray-800 flex flex-col shrink-0 z-20">
        
        <!-- 대시보드 로고 및 타이틀 -->
        <div class="p-6 border-b border-gray-800 flex flex-col gap-1 shrink-0">
            <h2 class="text-md font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 flex items-center gap-2">
                🍔 버거지수 대시보드
            </h2>
            <span class="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Burger Index App v2.0</span>
        </div>
        
        <!-- 내비게이션 메뉴 목록 -->
        <nav class="flex-1 p-4 flex flex-col gap-6 overflow-y-auto">
            
            <!-- 대시보드 메인 -->
            <div>
                <span class="text-[10px] text-gray-500 uppercase tracking-wider font-bold block mb-2 px-2">대시보드 메인</span>
                <div class="flex flex-col gap-1">
                    <button onclick="switchTab('home')" id="btn-tab-home" class="sidebar-tab-btn w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-300 hover:bg-gray-800/60 hover:text-white transition bg-gray-800 text-white">
                        <span>🏠</span> 홈 (소개 및 종합)
                    </button>
                </div>
            </div>
            
            <!-- 세부 분석 메뉴 -->
            <div>
                <span class="text-[10px] text-gray-500 uppercase tracking-wider font-bold block mb-2 px-2">세부 분석 메뉴</span>
                <div class="flex flex-col gap-1">
                    <button onclick="switchTab('eda')" id="btn-tab-eda" class="sidebar-tab-btn w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-300 hover:bg-gray-800/60 hover:text-white transition">
                        <span>📊</span> 1) 기본 EDA
                    </button>
                    <button onclick="switchTab('scatter')" id="btn-tab-scatter" class="sidebar-tab-btn w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-300 hover:bg-gray-800/60 hover:text-white transition">
                        <span>📍</span> 2) 버거지수 지도 시각화
                    </button>
                    <button onclick="switchTab('choropleth')" id="btn-tab-choropleth" class="sidebar-tab-btn w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-300 hover:bg-gray-800/60 hover:text-white transition">
                        <span>🗺️</span> 3) 행정구역별 시각화
                    </button>
                </div>
            </div>

            <!-- 분할선 및 필터 옵션 영역 (3번 탭 활성화 시에만 렌더링되게 구성) -->
            <div id="filter-panel" class="hidden border-t border-gray-800 pt-4 mt-2">
                <span class="text-[10px] text-gray-500 uppercase tracking-wider font-bold block mb-3 px-2 flex items-center gap-1.5">
                    <span>⚙️</span> 단계구분도 필터 옵션
                </span>
                
                <!-- 결측치 처리 방식 -->
                <div class="px-2 flex flex-col gap-1.5">
                    <label class="text-[11px] text-gray-400 flex items-center justify-between">
                        <span>버거지수 결측치(NaN) 처리 방식</span>
                        <span class="cursor-help text-gray-500 hover:text-gray-300" title="롯데리아 매장이 없거나(NaN) 브랜드 교차 데이터가 존재하지 않는 행정구역의 색상 채우기 처리 방식입니다.">❔</span>
                    </label>
                    <select id="nan-mode-select" onchange="updateChoroplethNaNMode()" class="w-full bg-[#1e293b] border border-gray-800 rounded-lg px-2.5 py-2 text-xs text-gray-200 focus:outline-none focus:border-blue-500 transition">
                        <option value="original" selected>원형(결측치로 유지 - 회색 표시)</option>
                        <option value="zero">0으로 대체 (롯데리아만 존재)</option>
                        <option value="mean">전국 평균값으로 대체</option>
                    </select>
                </div>
            </div>

        </nav>
        
        <!-- 하단 전국 요약 평균 뱃지 -->
        <div class="p-4 border-t border-gray-800 text-center shrink-0">
            <span class="inline-block bg-blue-500/10 text-blue-400 text-[10px] px-2.5 py-1 rounded-full border border-blue-500/20 font-semibold uppercase tracking-wider">
                전국 평균 버거지수: {national_index:.4f}
            </span>
        </div>
    </aside>

    <!-- 우측 메인 콘텐츠 프레임 -->
    <main class="flex-1 h-full flex flex-col overflow-hidden relative">
        
        <!-- ========================================== -->
        <!-- TAB 1: 홈 (소개 및 종합) -->
        <!-- ========================================== -->
        <div id="tab-home" class="flex-1 overflow-y-auto p-8 flex flex-col gap-6">
            
            <div class="border-b border-gray-800 pb-4">
                <h1 class="text-2xl font-bold text-gray-100">대한민국 버거지수(Burger Index) 홈</h1>
                <p class="text-xs text-gray-400 mt-1">전국 소상공인 상권 데이터를 기초로 정제한 대안 도시 생활지표 요약</p>
            </div>

            <!-- 상단 소개 및 메트릭스 -->
            <div class="grid grid-cols-5 gap-4">
                <div class="bg-[#1e293b] border border-gray-800 p-4.5 rounded-xl flex flex-col gap-1">
                    <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🍔 전국 평균 버거지수</span>
                    <span class="text-2xl font-extrabold text-amber-500">{national_index:.4f}</span>
                </div>
                <div class="bg-[#1e293b] border border-gray-800 p-4.5 rounded-xl flex flex-col gap-1">
                    <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🔴 롯데리아 매장 수</span>
                    <span class="text-2xl font-extrabold text-red-500">{national_lotteria:,}개</span>
                </div>
                <div class="bg-[#1e293b] border border-gray-800 p-4.5 rounded-xl flex flex-col gap-1">
                    <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🟡 맥도날드 매장 수</span>
                    <span class="text-2xl font-extrabold text-yellow-400">{national_mcdonald:,}개</span>
                </div>
                <div class="bg-[#1e293b] border border-gray-800 p-4.5 rounded-xl flex flex-col gap-1">
                    <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🟤 버거킹 매장 수</span>
                    <span class="text-2xl font-extrabold text-orange-400">{national_burgerking:,}개</span>
                </div>
                <div class="bg-[#1e293b] border border-gray-800 p-4.5 rounded-xl flex flex-col gap-1">
                    <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🔴 KFC 매장 수</span>
                    <span class="text-2xl font-extrabold text-red-600">{national_kfc:,}개</span>
                </div>
            </div>

            <!-- 하단 2열 대시보드 리포트 -->
            <div class="grid grid-cols-3 gap-6 items-start">
                
                <!-- 소개 카드 -->
                <div class="bg-[#1e293b] border border-gray-800 rounded-xl p-5 col-span-2 flex flex-col gap-3">
                    <h3 class="text-sm font-bold text-gray-200 border-b border-gray-800 pb-2 flex items-center gap-1.5">
                        <span>💡</span> 버거지수(Burger Index)란?
                    </h3>
                    <p class="text-xs text-gray-400 leading-relaxed">
                        버거지수(Burger Index)는 한국 도시 인프라 및 주민 생활 수준을 대변하는 대안 지수입니다. 
                        국내 버거 브랜드 중 자본 집약적이고 상권 분석에 철저한 프리미엄/외산 브랜드인 <strong>버거킹, 맥도날드, KFC의 매장 수 합산</strong>을 전국 구석구석까지 고르게 침투해 있는 토종 브랜드인 <strong>롯데리아 매장 수로 나누어</strong> 산출합니다.
                    </p>
                    <p class="text-xs text-gray-400 leading-relaxed">
                        이 지수가 높을수록(즉, 롯데리아 대비 외산/프리미엄 3대 버거 브랜드의 비율이 높을수록) 
                        도시 인프라가 풍부하고 소비 수준이 높은 매력적인 도시 지역으로 평가받는 이른바 <strong>'생활 편의 인프라 지수'</strong>로 널리 통용되고 있습니다.
                    </p>
                    <div class="bg-gray-900/60 p-3 rounded-lg border border-gray-800/80 mt-1 flex flex-col gap-1.5 text-xs">
                        <span class="font-bold text-gray-300">📊 버거지수 공식</span>
                        <code class="text-blue-400 font-mono font-bold">(버거킹 매장 수 + 맥도날드 매장 수 + KFC 매장 수) ÷ 롯데리아 매장 수</code>
                    </div>
                </div>

                <!-- 도넛 점유율 차트 -->
                <div class="bg-[#1e293b] border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
                    <h3 class="text-sm font-bold text-gray-200 border-b border-gray-800 pb-2">🍕 4대 버거 브랜드 전국 점유율</h3>
                    <div class="relative h-44 w-full flex items-center justify-center">
                        <canvas id="brandShareChartHome"></canvas>
                    </div>
                    <div class="text-center text-[10px] text-gray-500 font-medium">총 {national_total:,}개 매장 (롯데리아 과반 근접)</div>
                </div>

            </div>

        </div>

        <!-- ========================================== -->
        <!-- TAB 2: 기본 EDA (시도평균 & 데이터 테이블) -->
        <!-- ========================================== -->
        <div id="tab-eda" class="flex-1 overflow-y-auto p-8 flex flex-col gap-8 hidden">
            
            <div class="border-b border-gray-800 pb-4">
                <h1 class="text-2xl font-bold text-gray-100 flex items-center gap-2">
                    📊 4대 버거 브랜드 기본 EDA 및 통계 분석
                </h1>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">
                    전국 시도시군구별 버거 매장 수 데이터를 요약 및 기술 통계 관점에서 보여줍니다. 대표값의 왜곡 방지를 위해 대표값(평균/중앙값), 이상치, <strong>비대칭도(왜도/첨도)</strong>를 점검합니다.
                </p>
            </div>

            <!-- 전국 현황 요약 메트릭 카드 5종 -->
            <div class="grid grid-cols-5 gap-6 bg-[#111827]/40 p-6 rounded-xl border border-gray-800/80 shrink-0">
                <div class="flex flex-col gap-1">
                    <span class="text-xs font-semibold text-gray-400">총 브랜드 매장 수</span>
                    <span class="text-3xl font-extrabold text-white">{national_total:,}개</span>
                </div>
                <div class="flex flex-col gap-1">
                    <span class="text-xs font-semibold text-gray-400">롯데리아 매장 수</span>
                    <span class="text-3xl font-extrabold text-red-500">{national_lotteria:,}개</span>
                </div>
                <div class="flex flex-col gap-1">
                    <span class="text-xs font-semibold text-gray-400">맥도날드 매장 수</span>
                    <span class="text-3xl font-extrabold text-yellow-400">{national_mcdonald:,}개</span>
                </div>
                <div class="flex flex-col gap-1">
                    <span class="text-xs font-semibold text-gray-400">버거킹 매장 수</span>
                    <span class="text-3xl font-extrabold text-orange-400">{national_burgerking:,}개</span>
                </div>
                <div class="flex flex-col gap-1">
                    <span class="text-xs font-semibold text-gray-400">KFC 매장 수</span>
                    <span class="text-3xl font-extrabold text-red-600">{national_kfc:,}개</span>
                </div>
            </div>

            <!-- 기술통계 테이블 섹션 -->
            <div class="bg-[#1e293b] border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
                <h3 class="text-sm font-bold text-gray-200 flex items-center gap-2">
                    <span>📈</span> 시도시군구별 브랜드 매장 분포 기술통계
                </h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs border-collapse">
                        <thead>
                            <tr class="bg-gray-900/80 text-gray-400 font-bold border-b border-gray-800">
                                <th class="p-3">브랜드</th>
                                <th class="p-3 text-center">평균(Mean)</th>
                                <th class="p-3 text-center">중앙값(Median)</th>
                                <th class="p-3 text-center">표준편차(SD)</th>
                                <th class="p-3 text-center">최소값(Min)</th>
                                <th class="p-3 text-center">최대값(Max)</th>
                                <th class="p-3 text-center">왜도(Skewness)</th>
                                <th class="p-3 text-center">첨도(Kurtosis)</th>
                            </tr>
                        </thead>
                        <tbody id="stats-table-body">
                            <!-- JS로 동적 렌더링 -->
                        </tbody>
                    </table>
                </div>
                <div class="text-[11px] text-gray-400 leading-relaxed mt-2 flex items-start gap-1.5 bg-gray-900/40 p-3 rounded-lg border border-gray-800/60">
                    <span>💡</span>
                    <p>
                        <strong>분포 비대칭성 가이드:</strong> 왜도(Skewness)가 클수록 특정 대도시 지역에 매장이 고도로 편중되어 있음을 나타냅니다. 특히 맥도날드, 버거킹, KFC는 매우 큰 왜도를 보이며 대도시 집중화 현상이 뚜렷합니다.
                    </p>
                </div>
            </div>

            <!-- 차트 2열 -->
            <div class="grid grid-cols-2 gap-6">
                <!-- 시도별 평균 버거지수 -->
                <div class="bg-[#1e293b] border border-gray-800 rounded-xl p-5">
                    <h3 class="text-sm font-bold text-gray-200 mb-3 uppercase tracking-wider">📈 시도별 평균 버거지수 순위</h3>
                    <div class="relative h-[250px] w-full">
                        <canvas id="sidoAvgChartEda"></canvas>
                    </div>
                </div>
                <!-- 분포 히스토그램 -->
                <div class="bg-[#1e293b] border border-gray-800 rounded-xl p-5">
                    <h3 class="text-sm font-bold text-gray-200 mb-3 uppercase tracking-wider">📊 전국 시군구별 버거지수 분포</h3>
                    <div class="relative h-[250px] w-full">
                        <canvas id="burgerIndexDistChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- 데이터 테이블 검색기 -->
            <div class="bg-[#1e293b] border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
                <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                    <h3 class="text-sm font-bold text-gray-200 flex items-center gap-1.5">
                        <span>🔍</span> 지역별 버거 데이터 테이블 검색기
                    </h3>
                    <div class="w-72">
                        <input type="text" id="table-search-input" onkeyup="filterDataTable()" placeholder="도시명으로 검색 (예: 강릉, 분당, 강남)" class="w-full bg-[#0b0f19] border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-blue-500 transition" />
                    </div>
                </div>
                
                <!-- 테이블 영역 -->
                <div class="overflow-x-auto max-h-[350px] overflow-y-auto">
                    <table class="w-full text-left text-xs border-collapse">
                        <thead>
                            <tr class="bg-gray-900/80 text-gray-400 font-bold sticky top-0 border-b border-gray-800">
                                <th class="p-3">시도시군구명</th>
                                <th class="p-3 text-center">롯데리아</th>
                                <th class="p-3 text-center">맥도날드</th>
                                <th class="p-3 text-center">버거킹</th>
                                <th class="p-3 text-center">KFC</th>
                                <th class="p-3 text-center">총 매장수</th>
                                <th class="p-3 text-right">버거지수</th>
                            </tr>
                        </thead>
                        <tbody id="data-table-body">
                            <!-- JS로 동적 렌더링 -->
                        </tbody>
                    </table>
                </div>
            </div>

        </div>


        <!-- ========================================== -->
        <!-- TAB 3: 버거지수 지도 시각화 (산점도 및 Top 10) -->
        <!-- ========================================== -->
        <div id="tab-scatter" class="flex-1 flex overflow-hidden hidden">
            
            <!-- 좌측 순위 패널 (산점도 지도용) -->
            <section class="w-80 bg-[#0f172a] border-r border-gray-800 p-5 flex flex-col gap-4 overflow-y-auto shrink-0 z-10">
                <div class="border-b border-gray-800 pb-2">
                    <h3 class="text-sm font-bold text-gray-200">🏆 버거지수 Top 10 지역</h3>
                    <p class="text-[10px] text-gray-500 mt-0.5">버거지수가 가장 높은 최상위 시군구 10곳</p>
                </div>
                <div class="flex-1 overflow-y-auto pr-1 flex flex-col gap-1.5" id="top10-container-scatter">
                    <!-- JS로 렌더링 -->
                </div>
            </section>
            
            <!-- 우측 지도 -->
            <section class="flex-1 h-full relative" id="scatter-map-container">
                <div id="scatter-map" class="w-full h-full"></div>
            </section>

        </div>

        <!-- ========================================== -->
        <!-- TAB 4: 행정구역별 시각화 (Choropleth Map) -->
        <!-- ========================================== -->
        <div id="tab-choropleth" class="flex-1 flex flex-col overflow-hidden hidden">
            <!-- 지도 영역 -->
            <section class="flex-1 h-full relative" id="choropleth-map-container">
                <div id="choropleth-map" class="w-full h-full"></div>
                
                <!-- 상단 플로팅 정보 타이틀 (캡처 이미지 재현) -->
                <div class="absolute top-6 left-6 z-[1000] bg-white/95 text-slate-800 px-5 py-4 rounded-xl border border-slate-200 shadow-xl max-w-lg backdrop-blur-md">
                    <h2 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                        🗺️ 3) Folium 행정구역별 버거지수 시각화 (Choropleth)
                    </h2>
                    <p class="text-xs text-slate-500 mt-1 leading-relaxed border-t border-slate-100 pt-1.5">
                        시군구 경계 데이터를 활용하여 해당 지역의 버거지수를 단계적 색상으로 표시합니다. 결측치는 사이드바 필터 옵션에 따라 유연하게 렌더링됩니다.
                    </p>
                </div>

                <!-- 범례 (우측 상단 캡처 스타일 재현) -->
                <div class="absolute top-6 right-6 z-[1000] map-legend w-64 flex flex-col gap-2">
                    <div class="flex justify-between text-[10px] font-bold text-gray-400">
                        <span>0.0</span>
                        <span>0.6</span>
                        <span>1.1</span>
                        <span>1.7</span>
                        <span>2.2</span>
                        <span>2.8</span>
                        <span>3.3+</span>
                    </div>
                    <div class="legend-gradient"></div>
                    <span class="text-[10px] text-gray-400 font-semibold text-center block">시군구별 버거지수</span>
                </div>
            </section>
        </div>

    </main>

    <script>
        // 파이썬 주입 데이터
        const burgerData = {json_data};
        const top10Data = {top_10_json};
        const sidoAvgData = {sido_avg_json};
        const geojsonData = {geojson_json};
        const statsData = {stats_json};

        // 데이터 매핑용 객체 생성 (시군구코드 -> 버거 데이터)
        const burgerMap = {{}};
        burgerData.forEach(item => {{
            burgerMap[item.code] = item;
        }});


        // GeoJSON 피처에 버거지수 매핑
        if (geojsonData) {{
            geojsonData.features.forEach(feature => {{
                const code = feature.properties.code;
                const data = burgerMap[code];
                feature.properties.burger_index = data ? data.index : null;
                feature.properties.data = data || null;
            }});
        }}

        // -------------------------------------------------------------
        // [지트 초기화] - 맵 객체 2종 생성 (산점도용 다크맵, 단계구분도용 라이트맵)
        // -------------------------------------------------------------
        
        // 1. 산점도 지도 (Scatter Map) - 다크 테마
        const scatterMap = L.map('scatter-map', {{
            center: [36.2, 127.8],
            zoom: 7.3,
            zoomControl: false
        }});
        
        L.control.zoom({{ position: 'topright' }}).addTo(scatterMap);
        
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(scatterMap);

        // 2. 단계구분도 지도 (Choropleth Map) - 라이트(Positron) 테마
        const choroplethMap = L.map('choropleth-map', {{
            center: [36.2, 127.8],
            zoom: 7.3,
            zoomControl: false
        }});
        
        L.control.zoom({{ position: 'topright' }}).addTo(choroplethMap);
        
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(choroplethMap);

        // -------------------------------------------------------------
        // [컬러 및 라디우스 매핑 함수]
        // -------------------------------------------------------------
        function getColor(val) {{
            if (val === null || isNaN(val)) return '#9ca3af'; // 기본 회색 (결측치)
            return val >= 1.5 ? '#bd0026' :
                   val >= 1.0 ? '#f03b20' :
                   val >= 0.5 ? '#fd8d3c' :
                                '#fed976';
        }}

        function getRadius(val) {{
            if (val === null || isNaN(val)) return 4;
            return Math.min(5 + (val * 6), 25);
        }}

        // -------------------------------------------------------------
        // [1. 산점도 마커 렌더링]
        // -------------------------------------------------------------
        burgerData.forEach(item => {{
            const marker = L.circleMarker([item.lat, item.lng], {{
                radius: getRadius(item.index),
                fillColor: getColor(item.index),
                color: '#ffffff',
                weight: 0.8,
                opacity: 0.8,
                fillOpacity: 0.7
            }});

            const popupContent = `
                <div class="p-1">
                    <h4 class="text-sm font-bold border-b border-gray-700 pb-1.5 text-white mb-2">${{item.city}}</h4>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-gray-300">
                        <div>버거지수: <span class="font-bold text-amber-400">${{item.index !== null ? item.index.toFixed(4) : 'NaN'}}</span></div>
                        <div>총 매장수: <span class="font-bold text-white">${{item.total}}개</span></div>
                        <div class="col-span-2 border-t border-gray-700/50 my-0.5"></div>
                        <div>롯데리아: ${{item.lotteria}}개</div>
                        <div>맥도날드: ${{item.mcdonald}}개</div>
                        <div>버거킹: ${{item.burgerking}}개</div>
                        <div>KFC: ${{item.kfc}}개</div>
                    </div>
                </div>
            `;
            marker.bindPopup(popupContent);

            marker.bindTooltip(`${{item.city}} (버거지수: ${{item.index !== null ? item.index.toFixed(2) : 'NaN'}})`, {{
                direction: 'top',
                opacity: 0.9
            }});

            // 주요 도시 라벨
            if (item.is_major && item.index !== null) {{
                const labelTooltip = L.tooltip({{
                    permanent: true,
                    direction: 'right',
                    className: 'leaflet-tooltip-own',
                    offset: [getRadius(item.index) + 2, 0]
                }})
                .setLatLng([item.lat, item.lng])
                .setContent(`${{item.city.split(' ').slice(-1)[0]}} (${{item.index.toFixed(2)}})`);
                
                labelTooltip.addTo(scatterMap);
            }}

            marker.addTo(scatterMap);
        }});

        // -------------------------------------------------------------
        // [2. Choropleth 단계구분도 렌더링]
        // -------------------------------------------------------------
        let geojsonLayer = null;

        function renderChoropleth(nanMode = 'original') {{
            if (geojsonLayer) {{
                choroplethMap.removeLayer(geojsonLayer);
            }}

            if (!geojsonData) return;

            // 데이터 갱신
            geojsonData.features.forEach(feature => {{
                const code = feature.properties.code;
                const data = burgerMap[code];
                if (data) {{
                    feature.properties.burger_index = data.index;
                }} else {{
                    if (nanMode === 'original') feature.properties.burger_index = null;
                    else if (nanMode === 'zero') feature.properties.burger_index = 0.0;
                    else if (nanMode === 'mean') feature.properties.burger_index = 1.0565; // 전국평균
                }}
            }});

            geojsonLayer = L.geoJson(geojsonData, {{
                style: function(feature) {{
                    const val = feature.properties.burger_index;
                    let fillCol = getColor(val);
                    if (val === null || isNaN(val)) {{
                        fillCol = '#e2e8f0'; // 오리지널 결측은 연한 회색 (라이트맵 테마에 맞춤)
                    }}
                    return {{
                        fillColor: fillCol,
                        weight: 1.2,
                        opacity: 0.7,
                        color: '#64748b',
                        dashArray: '2',
                        fillOpacity: 0.75
                    }};
                }},
                onEachFeature: function(feature, layer) {{
                    layer.on({{
                        mouseover: function(e) {{
                            const lyr = e.target;
                            lyr.setStyle({{
                                weight: 2.5,
                                color: '#0f172a',
                                dashArray: '',
                                fillOpacity: 0.9
                            }});
                            lyr.bringToFront();
                            
                            const data = feature.properties.data;
                            const idxVal = feature.properties.burger_index;
                            const displayIdx = idxVal !== null ? idxVal.toFixed(3) : 'NaN';
                            
                            let tooltipHtml = '';
                            if (data) {{
                                tooltipHtml = `
                                    <div class="p-1 text-slate-100">
                                        <div class="font-bold border-b border-gray-700 pb-1 mb-1.5">📍 시군구명: ${{data.city}}</div>
                                        <div class="flex flex-col gap-0.5">
                                            <div>📊 버거지수: <span class="font-bold text-amber-400">${{displayIdx}}</span></div>
                                            <div>📦 매장총합: <span class="font-bold">${{data.total}}개</span></div>
                                            <div class="text-[10px] text-gray-400">🍔 브랜드수: 롯데리아 ${{data.lotteria}} | 버거킹 ${{data.burgerking}} | 맥도날드 ${{data.mcdonald}} | KFC ${{data.kfc}}</div>
                                        </div>
                                    </div>
                                `;
                            }} else {{
                                tooltipHtml = `
                                    <div class="p-1 text-slate-100">
                                        <div class="font-bold border-b border-gray-700 pb-1 mb-1">📍 시군구명: ${{feature.properties.name}}</div>
                                        <div class="text-gray-400">📊 버거지수: ${{displayIdx}} (매장 정보 없음)</div>
                                    </div>
                                `;
                            }}
                            
                            lyr.bindTooltip(tooltipHtml, {{ sticky: true, className: 'leaflet-tooltip-own' }}).openTooltip();
                        }},
                        mouseout: function(e) {{
                            geojsonLayer.resetStyle(e.target);
                        }},
                        click: function(e) {{
                            const data = feature.properties.data;
                            if (data) {{
                                const popupContent = `
                                    <div class="p-1">
                                        <h4 class="text-sm font-bold border-b border-gray-700 pb-1.5 text-white mb-2">${{data.city}}</h4>
                                        <div class="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-gray-300">
                                            <div>버거지수: <span class="font-bold text-amber-400">${{data.index.toFixed(4)}}</span></div>
                                            <div>총 매장수: <span class="font-bold text-white">${{data.total}}개</span></div>
                                            <div class="col-span-2 border-t border-gray-700/50 my-0.5"></div>
                                            <div>롯데리아: ${{data.lotteria}}개</div>
                                            <div>맥도날드: ${{data.mcdonald}}개</div>
                                            <div>버거킹: ${{data.burgerking}}개</div>
                                            <div>KFC: ${{data.kfc}}개</div>
                                        </div>
                                    </div>
                                `;
                                L.popup().setLatLng(e.latlng).setContent(popupContent).openOn(choroplethMap);
                            }}
                        }}
                    }});
                }}
            }});
            geojsonLayer.addTo(choroplethMap);
        }}

        // 최초 렌더링
        renderChoropleth('original');

        // NaN 모드 변경 리스너
        function updateChoroplethNaNMode() {{
            const mode = document.getElementById('nan-mode-select').value;
            renderChoropleth(mode);
        }}

        // -------------------------------------------------------------
        // [탭 전환 제어 로직]
        // -------------------------------------------------------------
        let activeTab = 'home';
        function switchTab(tabId) {{
            if (activeTab === tabId) return;

            // 모든 탭 숨김
            document.getElementById('tab-home').classList.add('hidden');
            document.getElementById('tab-eda').classList.add('hidden');
            document.getElementById('tab-scatter').classList.add('hidden');
            document.getElementById('tab-choropleth').classList.add('hidden');

            // 대상 탭 표시
            document.getElementById('tab-' + tabId).classList.remove('hidden');

            // 사이드바 버튼 상태 변경
            const buttons = document.querySelectorAll('.sidebar-tab-btn');
            buttons.forEach(btn => {{
                btn.classList.remove('bg-gray-800', 'text-white');
                btn.classList.add('text-gray-300');
            }});
            document.getElementById('btn-tab-' + tabId).classList.add('bg-gray-800', 'text-white');
            document.getElementById('btn-tab-' + tabId).classList.remove('text-gray-300');

            // 필터 옵션 영역 가시성 제어 (Choropleth에서만 활성화)
            const filterPanel = document.getElementById('filter-panel');
            if (tabId === 'choropleth') {{
                filterPanel.classList.remove('hidden');
            }} else {{
                filterPanel.classList.add('hidden');
            }}

            // 지도 크기 재조정 (지도가 찌그러져 렌더링되는 것 방지)
            if (tabId === 'scatter') {{
                setTimeout(() => {{
                    scatterMap.invalidateSize();
                }}, 50);
            }}
            if (tabId === 'choropleth') {{
                setTimeout(() => {{
                    choroplethMap.invalidateSize();
                }}, 50);
            }}

            activeTab = tabId;
        }}

        // -------------------------------------------------------------
        // [3. Top 10 순위 렌더링 & 지도 이동 연동]
        // -------------------------------------------------------------
        const top10ContainerScatter = document.getElementById('top10-container-scatter');
        top10Data.forEach((item, index) => {{
            const div = document.createElement('div');
            div.className = "flex items-center justify-between bg-[#1e293b]/50 p-2.5 rounded-lg border border-gray-800/80 hover:bg-[#1e293b] transition duration-150 cursor-pointer";
            
            let badgeClass = "bg-gray-700 text-gray-300";
            if (index === 0) badgeClass = "bg-amber-500 text-slate-900 font-bold";
            else if (index === 1) badgeClass = "bg-slate-300 text-slate-900 font-bold";
            else if (index === 2) badgeClass = "bg-amber-700 text-white font-bold";

            div.innerHTML = `
                <div class="flex items-center gap-2.5">
                    <span class="w-5 h-5 flex items-center justify-center text-xs rounded-full ${{badgeClass}}">${{index + 1}}</span>
                    <span class="text-xs font-medium text-gray-200">${{item.city}}</span>
                </div>
                <div class="text-right">
                    <span class="text-xs font-bold text-amber-400">${{item.index.toFixed(4)}}</span>
                </div>
            `;
            
            div.onclick = () => {{
                const target = burgerData.find(b => b.city === item.city);
                if (target) {{
                    scatterMap.setView([target.lat, target.lng], 10);
                    // 산점도 마커 팝업 트리거
                    scatterMap.eachLayer(layer => {{
                        if (layer instanceof L.CircleMarker && layer.getLatLng().lat === target.lat && layer.getLatLng().lng === target.lng) {{
                            layer.openPopup();
                        }}
                    }});
                }}
            }};
            top10ContainerScatter.appendChild(div);
        }});

        // -------------------------------------------------------------
        // [기술통계 테이블 렌더링]
        // -------------------------------------------------------------
        const statsTableBody = document.getElementById('stats-table-body');
        function renderStatsTable() {{
            statsTableBody.innerHTML = '';
            statsData.forEach((item, index) => {{
                const tr = document.createElement('tr');
                tr.className = "border-b border-gray-800 hover:bg-gray-800/30 transition text-gray-300";
                
                const isBurgerIndex = item.brand === '버거지수';
                const meanVal = item.mean.toFixed(2);
                const medianVal = isBurgerIndex ? item.median.toFixed(2) : Math.round(item.median).toString();
                const stdVal = item.std.toFixed(2);
                const minVal = isBurgerIndex ? item.min.toFixed(2) : Math.round(item.min).toString();
                const maxVal = isBurgerIndex ? item.max.toFixed(2) : Math.round(item.max).toString();
                const skewVal = item.skew.toFixed(2);
                const kurtVal = item.kurt.toFixed(2);
                
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-gray-200">
                        <span class="text-gray-500 mr-2">${{index}}</span>${{item.brand}}
                    </td>
                    <td class="p-3 text-center">${{meanVal}}</td>
                    <td class="p-3 text-center">${{medianVal}}</td>
                    <td class="p-3 text-center">${{stdVal}}</td>
                    <td class="p-3 text-center">${{minVal}}</td>
                    <td class="p-3 text-center">${{maxVal}}</td>
                    <td class="p-3 text-center font-semibold text-amber-400">${{skewVal}}</td>
                    <td class="p-3 text-center">${{kurtVal}}</td>
                `;
                statsTableBody.appendChild(tr);
            }});
        }}
        renderStatsTable();

        // -------------------------------------------------------------
        // [4. 기본 EDA 테이블 렌더링 및 실시간 검색]
        // -------------------------------------------------------------
        const tableBody = document.getElementById('data-table-body');
        
        function renderDataTable(dataList) {{
            tableBody.innerHTML = '';
            dataList.forEach(item => {{
                const tr = document.createElement('tr');
                tr.className = "border-b border-gray-800 hover:bg-gray-800/30 transition text-gray-300";
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-gray-200">${{item.city}}</td>
                    <td class="p-3 text-center">${{item.lotteria}}</td>
                    <td class="p-3 text-center">${{item.mcdonald}}</td>
                    <td class="p-3 text-center">${{item.burgerking}}</td>
                    <td class="p-3 text-center">${{item.kfc}}</td>
                    <td class="p-3 text-center font-bold text-white">${{item.total}}</td>
                    <td class="p-3 text-right font-bold text-amber-400">${{item.index.toFixed(4)}}</td>
                `;
                tableBody.appendChild(tr);
            }});
        }}

        // 초기 정렬 상태로 렌더링
        const sortedBurgerData = [...burgerData].sort((a, b) => b.index - a.index);
        renderDataTable(sortedBurgerData);

        // 검색 필터 함수
        function filterDataTable() {{
            const query = document.getElementById('table-search-input').value.toLowerCase().trim();
            const filtered = sortedBurgerData.filter(item => item.city.toLowerCase().includes(query));
            renderDataTable(filtered);
        }}

        // -------------------------------------------------------------
        // [5. Chart.js 차트 초기화]
        // -------------------------------------------------------------
        
        // (1) 홈화면 브랜드 비율 도넛 차트
        const brandShareCtxHome = document.getElementById('brandShareChartHome').getContext('2d');
        new Chart(brandShareCtxHome, {{
            type: 'doughnut',
            data: {{
                labels: ['롯데리아', '맥도날드', '버거킹', 'KFC'],
                datasets: [{{
                    data: [{national_lotteria}, {national_mcdonald}, {national_burgerking}, {national_kfc}],
                    backgroundColor: ['#ef4444', '#facc15', '#f97316', '#dc2626'],
                    borderWidth: 0,
                    hoverOffset: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            color: '#94a3b8',
                            font: {{ size: 10 }}
                        }}
                    }}
                }},
                cutout: '65%'
            }}
        }});

        // (2) EDA 화면 시도별 평균 버거지수 가로 바 차트
        const sidoAvgCtxEda = document.getElementById('sidoAvgChartEda').getContext('2d');
        const sidoLabels = sidoAvgData.map(item => item.sido);
        const sidoValues = sidoAvgData.map(item => item.index);
        
        new Chart(sidoAvgCtxEda, {{
            type: 'bar',
            data: {{
                labels: sidoLabels,
                datasets: [{{
                    label: '평균 버거지수',
                    data: sidoValues,
                    backgroundColor: sidoValues.map(val => {{
                        if (val >= 1.5) return 'rgba(189, 0, 38, 0.85)';
                        if (val >= 1.0) return 'rgba(240, 59, 32, 0.8)';
                        if (val >= 0.5) return 'rgba(253, 141, 60, 0.8)';
                        return 'rgba(254, 217, 118, 0.8)';
                    }}),
                    borderRadius: 4
                }}]
            }},
            options: {{
                indexAxis: 'y', // 가로 막대
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: '#1e293b' }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 9 }} }}
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#f3f4f6', font: {{ size: 10, weight: 'bold' }} }}
                    }}
                }}
            }}
        }});

        // (3) EDA 화면 전국 시군구별 버거지수 분포 히스토그램
        // 버거지수 분포를 0.5 간격으로 구간화(binning)하여 계산
        const distBins = {{ '0.0-0.5': 0, '0.5-1.0': 0, '1.0-1.5': 0, '1.5-2.0': 0, '2.0-2.5': 0, '2.5-3.0': 0, '3.0+': 0 }};
        burgerData.forEach(item => {{
            const val = item.index;
            if (val < 0.5) distBins['0.0-0.5']++;
            else if (val < 1.0) distBins['0.5-1.0']++;
            else if (val < 1.5) distBins['1.0-1.5']++;
            else if (val < 2.0) distBins['1.5-2.0']++;
            else if (val < 2.5) distBins['2.0-2.5']++;
            else if (val < 3.0) distBins['2.5-3.0']++;
            else distBins['3.0+']++;
        }});

        const distCtx = document.getElementById('burgerIndexDistChart').getContext('2d');
        new Chart(distCtx, {{
            type: 'bar',
            data: {{
                labels: Object.keys(distBins),
                datasets: [{{
                    label: '시군구 수 (개)',
                    data: Object.values(distBins),
                    backgroundColor: '#3b82f6',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}
                    }},
                    y: {{
                        grid: {{ color: '#1e293b' }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 9 }} }}
                    }}
                }}
            }}
        }});

    </script>
</body>
</html>
"""

    # HTML 파일 쓰기
    os.makedirs(output_dir, exist_ok=True)
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"대시보드 HTML 파일이 성공적으로 작성되었습니다: {output_html}")

if __name__ == '__main__':
    generate_dashboard()

