"""
식품안전나라 API, 공공데이터포털 API, DUR 오프라인 덤프 데이터를 수집하고
이커머스 통합 데이터(ec_standardized_total.csv)와 연계하여
상품 이미지 URL(img_url)을 포함한 최종 가교 데이터(ec_mapped_with_api.csv)를 생성하는 파이썬 스크립트입니다.
"""

import os
import sys
import zipfile
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# stdout 한글 출력을 위한 인코딩 설정
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 1. 환경 설정 및 API 키 정의
# ==========================================
FOOD_SAFETY_KEY = "4cca164bc44a494c8e1"
DATA_GO_KEY_1 = "8dc1af0881032d3987fecff814f3b1c94a48cc92969cf7451d2332edd92fab68"
DATA_GO_KEY_2 = "89fccf295e6928bf7077c370409d7f95f5cc99c8a5aa1f1674b9364bbdc58ae3"

DATA_DIR = os.path.join("project2", "data")
EXTRACT_DIR = os.path.join(DATA_DIR, "extracted_dump")
os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================
# 2. 대용량 오프라인 덤프(ZIP) 자동 해제 및 로드
# ==========================================
def process_zip_dump(zip_name="dur_item_dump.zip"):
    zip_path = os.path.join(DATA_DIR, zip_name)
    if not os.path.exists(zip_path):
        alt_zip_path = os.path.join(DATA_DIR, zip_name + ".zip")
        if os.path.exists(alt_zip_path):
            zip_path = alt_zip_path
        else:
            print(f"⚠️ [오프라인 데이터] {zip_path} 파일이 없습니다. 스킵합니다.")
            return pd.DataFrame()
        
    print(f"📦 [오프라인 데이터] {os.path.basename(zip_path)} 압축 해제 및 파싱 시작...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)
        
    for root, dirs, files in os.walk(EXTRACT_DIR):
        for file in files:
            if file.endswith('.csv'):
                csv_file_path = os.path.join(root, file)
                try:
                    df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
                except Exception:
                    df = pd.read_csv(csv_file_path, encoding='cp949')
                print(f"✅ [DUR/덤프] {file} 로드 완료 ({len(df)}건)")
                return df
    return pd.DataFrame()

# ==========================================
# 3. 식품안전나라 API 3종 비동기 수집기
# ==========================================
def fetch_food_safety(service_id, start=1, end=500):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_SAFETY_KEY}/{service_id}/json/{start}/{end}"
    for attempt in range(2):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            res_data = res.json()
            if service_id in res_data and 'row' in res_data[service_id]:
                rows = res_data[service_id]['row']
                return service_id, pd.DataFrame(rows)
        except Exception:
            pass
    return service_id, pd.DataFrame()

# ==========================================
# 4. 공공데이터포털 API 3종 수집기
# ==========================================
def fetch_data_go(url, key, service_name, num_rows=100):
    params = {'serviceKey': key, 'pageNo': '1', 'numOfRows': str(num_rows), 'type': 'json'}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get('body', {}).get('items', [])
        print(f"✅ [공공데이터포털] {service_name} 수집 완료 ({len(items)}건)")
        return service_name, pd.DataFrame(items)
    except Exception as e:
        print(f"❌ [공공데이터포털] {service_name} 호출 실패: {e}")
    return service_name, pd.DataFrame()

# ==========================================
# 5. 25종+ 최신 인기 건기식 세분화 카테고리 매핑 룰
# ==========================================
INGREDIENT_RULES = [
    (['콘드로이친', '소연골', '상어연골'], '콘드로이친(관절 건강)', '관절 및 연골 건강과 연골 마모 방지에 도움'),
    (['msm', '엠에스엠', '글루코사민', '관절보궁'], 'MSM·글루코사민(관절/연골)', '관절의 유유성 및 연골 조직 형성 지원'),
    (['테아닌', 'l-테아닌', '타트체리', '수면'], 'L-테아닌(수면·스트레스)', '스트레스로 인한 긴장 완화 및 수면 질 개선'),
    (['바나바', '코로솔산'], '바나바잎 추출물(혈당 케어)', '식후 혈당 상승 억제에 도움을 줄 수 있음'),
    (['프로바이오틱스', '유산균', '락토핏', '비피더스', '생유산균'], '프로바이오틱스(유산균/장 건강)', '장 내 유익균 증식 및 유해균 억제, 배변활동 원활'),
    (['오메가3', '오메가-3', '오메가 3', 'epa', 'dha', 'rtg'], 'rTG 오메가-3(혈관·혈행)', '혈중 중성지질 개선 및 혈행 개선, 건조한 눈 개선'),
    (['밀크씨슬', '밀크시슬', '실리마린'], '밀크씨슬(실리마린/간 건강)', '간 세포 보호 및 피로 물질 대사 간 건강에 도움'),
    (['루테인', '지아잔틴', '아스타잔틴', '아이케어'], '루테인·지아잔틴(눈 건강)', '황반 색소 밀도 유지 및 피로한 눈 건강에 도움'),
    (['비타민c', '비타민 c', '아스코르브산'], '비타민 C(항산화·면역)', '유해산소로부터 세포 보호, 항산화 및 결합조직 형성'),
    (['비타민d', '비타민 d', '비타민d3'], '비타민 D(뼈 건강·면역)', '뼈의 형성 및 유지, 골다공증 위험 감소, 면역 관리'),
    (['비타민b', '비타민 b', '비오틴', '나이아신', '티아민', '리보플라빈'], '비타민 B군·비오틴(에너지·활력)', '체내 수용성 에너지 대사 및 수면/피로 회복 지원'),
    (['마그네슘', 'magnesium'], '마그네슘(신경·근육)', '에너지 이용 및 신경과 근육 기능 유지'),
    (['칼슘', 'calcium'], '칼슘(뼈·치아)', '뼈와 치아 형성, 신경 전달 및 정상적 혈액응고'),
    (['아연', 'zinc'], '아연(면역 기능)', '정상적인 면역 기능 및 정상적인 세포분열에 필요'),
    (['콜라겐', '피쉬콜라겐', '저분자콜라겐'], '콜라겐(피부 탄력)', '피부 수분 유지 및 보습, 피부 건강 관리에 도움'),
    (['코엔자임', '코큐텐', 'coq10'], '코엔자임Q10(항산화·혈압)', '항산화 작용 및 높은 혈압 감소에 도움'),
    (['프로폴리스', 'propolis'], '프로폴리스(항균·면역)', '구강 내 항균 작용 및 항산화 관리'),
    (['아르기닌', 'l-아르기닌', '알기닌'], 'L-아르기닌(혈류·활력)', '신체 활력 증진 및 혈류 흐름 개선 지원'),
    (['쏘팔메토', '사발팜'], '쏘팔메토(전립선 건강)', '남성 전립선 건강 유지에 도움'),
    (['이소플라본', '대두이소플라본'], '이소플라본(여성 건강)', '갱년기 여성 건강 유지에 도움'),
    (['엽산', '철분', '철분제'], '엽산·철분(혈액 생성·임산부)', '세포와 혈액생성에 필요, 태아 신경관의 정상 발달'),
    (['락토페린'], '락토페린(체지방·면역)', '체지방 감소 및 면역력 강화에 도움'),
    (['홍삼', '인삼', '진세노사이드'], '홍삼·인삼(면역·피로 개선)', '면역력 증진, 피로 개선, 혈소판 응집억제를 통한 혈액흐름에 도움'),
    (['가르시니아', '카테킨', '시네프린'], '가르시니아·카테킨(체지방 감소)', '탄수화물이 지방으로 합성되는 것을 억제하여 체지방 감소'),
    (['크릴오일', '크릴'], '크릴오일(혈행 개선)', '인지질 함유로 인체 흡수율이 높은 오메가3 공급'),
]

def map_ingredient_and_function(product_name, df_i0040):
    p_name_lower = product_name.lower()
    for keywords, ing_label, fn_desc in INGREDIENT_RULES:
        if any(kw in p_name_lower for kw in keywords):
            return ing_label, fn_desc
            
    if not df_i0040.empty:
        for _, api_row in df_i0040.iterrows():
            ing_name = str(api_row.get('PRDUCT_NM', ''))
            if ing_name and len(ing_name) > 1 and ing_name.lower() in p_name_lower:
                return ing_name, api_row.get('FNCLTY_CN', '식약처 인증 기능성 원료')
                
    return "미분류 일반식품군", "일반 영양 공급"

# ==========================================
# 6. 메인 데이터 파이프라인
# ==========================================
def main():
    print("🚀 [Step 3 이미지 URL 포함 매핑] 파이프라인 가동\n")
    
    ec_path = os.path.join(DATA_DIR, "ec_standardized_total.csv")
    if not os.path.exists(ec_path):
        print(f"❌ 기준 데이터가 없습니다. {ec_path}를 먼저 생성해주세요.")
        return
    df_ec = pd.read_csv(ec_path)

    api_results = {}
    services_food_safety = ["I-0050", "I0760", "I-0040"]
    data_go_targets = [
        ("https://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsItemInq03", DATA_GO_KEY_1, "건기식제품정보"),
        ("https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02", DATA_GO_KEY_1, "식품영양성분DB"),
        ("https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList", DATA_GO_KEY_2, "의약품개요_e약은요")
    ]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for s_id in services_food_safety:
            futures.append(executor.submit(fetch_food_safety, s_id))
        for url, key, name in data_go_targets:
            futures.append(executor.submit(fetch_data_go, url, key, name))
            
        for future in as_completed(futures):
            name, df = future.result()
            if not df.empty:
                api_results[name] = df

    df_dur = process_zip_dump("dur_item_dump.zip")
    if not df_dur.empty:
        api_results["DUR품목정보"] = df_dur

    df_i0040 = api_results.get("I-0040", pd.DataFrame())
    
    mapped_list = []
    for _, ec_row in df_ec.iterrows():
        p_name = str(ec_row.get('product_name', ''))
        matched_ingredient, functionality = map_ingredient_and_function(p_name, df_i0040)
        
        hard_filter_trigger = "None"
        p_name_lower = p_name.lower()
        
        if "비타민 a" in p_name_lower or "레티놀" in p_name_lower or "비타민a" in p_name_lower:
            hard_filter_trigger = "PREGNANCY_HAZARD"
        elif any(k in p_name_lower for k in ["갑각류", "키토산", "게", "새우"]):
            hard_filter_trigger = "ALLERGY_CRUSTACEAN"
        elif any(k in p_name_lower for k in ["대두", "콩", "이소플라본"]):
            hard_filter_trigger = "ALLERGY_SOY"
        elif any(k in p_name_lower for k in ["우유", "유청", "유청단백질", "whey"]):
            hard_filter_trigger = "ALLERGY_MILK"
            
        mapped_list.append({
            'platform': ec_row.get('platform', 'unknown'),
            'product_id': ec_row.get('product_id', ''),
            'brand': ec_row.get('brand', 'Unknown'),
            'product_name': p_name,
            'price': ec_row.get('price', 0),
            'rating': ec_row.get('rating', 0),
            'review_count': ec_row.get('review_count', 0),
            'matched_ingredient': matched_ingredient,
            'functionality_raw': functionality,
            'hard_filter_trigger': hard_filter_trigger,
            'img_url': ec_row.get('img_url', '')
        })
        
    df_final_bridge = pd.DataFrame(mapped_list)
    output_path = os.path.join(DATA_DIR, "ec_mapped_with_api.csv")
    df_final_bridge.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n🎯 [이미지 URL 포함 완료] ec_mapped_with_api.csv 저장 완료 ({len(df_final_bridge)}건)")
    print(f"이미지 URL 보유 수량: {df_final_bridge['img_url'].notna().sum()}건")

if __name__ == "__main__":
    main()
