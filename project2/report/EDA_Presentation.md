---
marp: true
theme: default
size: 16:9
paginate: true
style: |
  @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
  @font-face {
    font-family: 'GmarketSansBold';
    src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_one@1.0/GmarketSansBold.woff') format('woff');
    font-weight: normal;
    font-style: normal;
  }
  section {
    background-color: #F4F1EC;
    color: #3D3530;
    font-family: 'Nanum Gothic', 'NanumGothic', sans-serif;
    padding: 35px 45px;
    box-sizing: border-box;
  }
  h1 {
    font-family: 'GmarketSansBold', sans-serif;
    color: #3D3530;
    font-size: 1.7rem;
    margin: 0 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 2px solid #8A7A6A;
  }
  h2 {
    font-family: 'GmarketSansBold', sans-serif;
    color: #8A7A6A;
    font-size: 1.15rem;
    margin: 0 0 6px 0;
  }
  p, li {
    font-family: 'Nanum Gothic', sans-serif;
    font-size: 0.8rem;
    line-height: 1.4;
    color: #3D3530;
  }
  ul {
    margin: 3px 0 6px 0;
    padding-left: 18px;
  }
  li {
    margin-bottom: 3px;
  }
  .accent {
    color: #3D3530;
    font-weight: bold;
  }
  code {
    background-color: #E6DFD5 !important;
    color: #1A1A1A !important;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    padding: 2px 5px !important;
    border-radius: 3px;
    font-size: 0.82rem !important;
    border: 1px solid #C8BFAF;
  }
  .footer-note {
    position: absolute;
    bottom: 20px;
    left: 45px;
    right: 75px;
    font-size: 0.68rem;
    color: #8A7A6A;
    border-top: 1px solid #D9CFC4;
    padding-top: 4px;
    display: flex;
    justify-content: space-between;
  }
  .slide-container {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
    gap: 25px;
    margin-top: 6px;
  }
  .text-content {
    width: 48%;
  }
  .visual-content {
    width: 49%;
    text-align: center;
  }
  .visual-content img {
    max-width: 100% !important;
    max-height: 380px !important;
    object-fit: contain;
    border-radius: 6px;
    box-shadow: 0 4px 8px rgba(61, 53, 48, 0.12);
    border: 1px solid #D9CFC4;
    display: block;
    margin: 0 auto;
  }
  /* 병렬 이미지 가로 배치 및 세로 줄바꿈 방지 스타일 */
  .image-row {
    display: flex !important;
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
    width: 100% !important;
    gap: 8px !important;
    margin-bottom: 5px !important;
  }
  .image-row img {
    width: 49% !important;
    height: auto !important;
    max-height: 165px !important;
    display: inline-block !important;
    object-fit: contain !important;
  }
  .info-box {
    background-color: #EAE5DC;
    border-left: 4px solid #8A7A6A;
    padding: 6px 10px;
    margin-top: 5px;
    border-radius: 0 4px 4px 0;
    width: 100%;
    box-sizing: border-box;
  }
  .info-box p {
    margin: 0;
    font-size: 0.78rem;
    color: #3D3530;
    line-height: 1.35;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    font-size: 0.85rem; /* 가시성 향상을 위해 폰트 확대 */
  }
  th, td {
    padding: 5px 8px; /* 패딩 확장 */
    border: 1.5px solid #8A7A6A; /* 테두리 명확화 */
    text-align: center;
    color: #3D3530;
  }
  th {
    background-color: #EAE5DC;
    font-weight: bold;
  }
  td {
    background-color: #FAF9F6;
  }
---

# 💊 NutriFit 추천 알고리즘 및 트렌드 대시보드 구축을 위한 초정밀 EDA

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

## 이커머스 건기식 통합 데이터 분석 기반 추천 룰(Rule) 설계
- **발표자**: NutriFit 데이터 사이언티스트 & 헬스케어 비즈니스 분석 전문가
- **분석 대상**: 아이허브, 올리브영, 쿠팡 이커머스 통합 원천 데이터 (28,239개 상품)
- **핵심 과제**: 문진 변수와 이커머스 핵심 데이터(제형, 평점, 리뷰, 건강고민) 간의 정밀 매칭 알고리즘 설계

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
여러분 안녕하십니까. 오늘 발표를 맡은 데이터 사이언티스트이자 헬스케어 비즈니스 분석 전문가입니다. 
우리는 맞춤형 웰니스 케어 서비스인 '뉴트리핏(NutriFit)'의 추천 알고리즘 고도화와 시장 분석을 위한 트렌드 대시보드 구축이라는 중요한 비즈니스 마일스톤을 눈앞에 두고 있습니다. 
이번 탐색적 데이터 분석(EDA)은 단순한 기초 통계량 출력을 넘어서, 유저들의 실제 문진 변수인 선호 제형, 알약 삼킴에 대한 불편감, 휴대성 선호도, 그리고 8대 주요 건강 고민을 수집된 28,239건의 방대한 이커머스 실데이터와 어떻게 정교하게 연결하고, 서비스의 실질적인 추천 룰로 정의할 수 있을 것인가에 초점을 맞추었습니다. 
이커머스 채널인 올리브영, 쿠팡, 아이허브에서 추출한 로우 데이터를 정제하고 9대 표준 제형으로 변환하는 과정부터, 텍스트 마이닝 기법과 감성 점수 산출을 통해 발견한 비즈니스 기회와 데이터의 실질적 한계점까지 차례대로 말씀드리겠습니다. 
본 분석 결과는 향후 대시보드의 백엔드 엔진과 실시간 추천 알고리즘의 초기 가중치 테이블 설계에 즉각 반영될 것입니다. 그럼 지금부터 상세 리포트 발표를 시작하겠습니다.
-->

---

# 📋 목차 (Table of Contents)

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

## 4대 핵심 분석 영역 및 대시보드 연계 설계안
1. **데이터 검사 및 프로파일링**: 데이터 누락 및 기초 기술통계량 심층 분석
2. **제형(Form) 9대 분류 표준화 및 텍스트 마이닝**: 정밀 룰 기반 제형 분류 및 Unknown 분석
3. **복용 편의성 & 휴대성 감성 분석**: 감성 텍스트 패턴 추출 및 만족도 검증
4. **8대 건강 고민 카테고리 매핑**: 성분 기반 라벨링 및 고민별 인기 제형 TOP 3
5. **가성비 포지셔닝 및 가설 검증**: 대체 제형 지불 용의(WTP) 분석 및 최종 알고리즘 설계안

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
이번 장에서는 전체 발표의 나침반이 될 목차에 대해 간략히 설명해 드리겠습니다. 
오늘 세션은 총 다섯 개의 대주제로 구성되어 있습니다. 
첫째, 데이터의 무결성을 점검하기 위해 28,239행의 전체 데이터 셋에 존재하는 중복치와 결측 상태를 점검하고, 수치형 변수와 범주형 변수의 통계적 왜도에 대한 Senior 분석가로서의 해석을 제시합니다. 
둘째, 상품명과 설명글을 기반으로 제형을 정제, 캡슐, 구미/젤리 등 9대 표준 제형으로 표준화하는 룰베이스 분류기를 코딩하고, 미분류 키워드에 대해 TF-IDF 텍스트 마이닝을 수행하여 신규 트렌드 제형 후보를 발굴합니다. 
셋째, 복용 편의성과 휴대성에 대한 정성적 감성 텍스트 패턴을 찾아 스코어를 매기고, 평점 및 리뷰 반응과의 관계를 확인하여 이커머스 채널 데이터의 한계점과 대안을 제시합니다. 
넷째, 유저들이 문진 시 선택하는 8대 건강 고민을 핵심 성분 사전에 따라 라벨링하여 시장 크기와 인기 제형 순위를 규명합니다. 
다섯째, 최종적으로 '2030 세대는 편의성과 맛을 위해 고가임에도 더 비용을 지불하는가'에 대한 가격-리뷰 가성비 맵을 그리고, 추천 알고리즘의 실질적 백엔드 반영 로직 설계도를 제공하겠습니다. 각 장에서 유기적으로 연결되는 비즈니스 임팩트를 주목해 주시기 바랍니다.
-->

---

# 🔍 1. 데이터 검사 및 기초 프로파일링

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>데이터 결측 상태 파악 및 데이터 클렌징 처리</h2>
    <ul>
      <li><span class="accent">전체 데이터 볼륨</span>: 28,239행, 8대 주요 칼럼 구성</li>
      <li><span class="accent">결측 변수 현황</span>: 상세설명(<code>description</code>)이 1,140건 누락으로 비중 최대, 평점/리뷰도 308건 누락 확인</li>
      <li><span class="accent">중복 데이터</span>: 완전 중복 588건 포착 ➡️ 분석 신뢰성을 위해 완전 정제 제거</li>
      <li><span class="accent">결측 처리</span>: 문자열은 빈 값(<code>''</code>)으로 대체, 가격/평점/리뷰는 <code>0</code>으로 일괄 전처리 완료</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[원천 칼럼 프로파일]</b><br>
      - platform (채널)<br>
      - product_id (코드)<br>
      - brand (브랜드)<br>
      - product_name (상품명)<br>
      - price (가격)<br>
      - rating (평점)<br>
      - review_count (리뷰수)<br>
      - description (설명글)</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
분석의 가장 첫 단추인 데이터 검사 및 기초 프로파일링 단계입니다. 
우리가 수집한 원천 이커머스 데이터는 총 28,239행에 8개의 주요 피처 컬럼으로 이루어져 있습니다. 
결측 상태를 확인해 본 결과, 상품 고유 코드, 브랜드명, 제품명, 판매 가격은 동일하게 63건의 누락이 있었으며, 평점과 리뷰 수는 308건, 그리고 가장 중요한 비정형 텍스트인 상세설명 컬럼은 1,140건의 결측치가 관찰되었습니다. 
이 텍스트 결측치는 판다스 함수로 문자열 내 특정 감성어나 성분 키워드를 카운팅할 때 에러를 야기할 수 있습니다. 
따라서 본격적인 자연어 처리 이전에 결측 클렌징을 완수했습니다. 
또한 데이터 중복 행이 588건 발견되었습니다. 이는 크롤링 수집 과정에서 다중 스크랩되었거나 프로모션용 번들 제품들이 단순 반복 등록된 경우로, 추천 룰 왜곡을 방지하기 위해 분석 정제 프로세스에서 이를 명확히 보정하고 가공을 시작하였습니다.
-->

---

# 📊 2. 수치형 변수 기술통계 심층 분석

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>가격(Price)과 평점(Rating)의 통계적 분포 특징</h2>
    <ul>
      <li><span class="accent">평균 가격</span>: 36,254원 (중위수 28,810원, 표준편차 28,488원)</li>
      <li>최댓값은 784,000원에 달해 오른쪽 꼬리가 긴 <span class="accent">극단적 우편향(Right-skewed, 왜도 4.10)</span> 분포 형성</li>
      <li><span class="accent">평균 평점</span>: 4.57점 (중위수 4.7점, 75% 분위수 4.8점)</li>
      <li>대부분의 제품 평점이 4.5점 이상에 몰려있는 <span class="accent">강한 좌편향(Left-skewed, 왜도 -5.20)</span> 분포로 상향 평준화 현상 뚜렷</li>
      <li>단순 평점 순 정렬 배제하고, 리뷰 볼륨을 가중 연산한 랭킹 설계 제안</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[수치형 요약 통계량]</b><br>
      - 가격 평균: 36,254원<br>
      - 가격 중위수: 28,810원<br>
      - 평점 평균: 4.57점<br>
      - 평점 중위수: 4.70점<br>
      - 리뷰수 평균: 2,266건<br>
      - 리뷰수 중위수: 234건</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
이번 장에서는 데이터 셋에 내재된 세 가지 핵심 수치형 피처인 가격, 평점, 리뷰 수 중 우선 가격과 평점의 통계적 거동에 대해 파악해 보겠습니다. 
첫째, 건강기능식품의 평균 가격은 약 36,000원 대입니다. 하지만 중위값은 28,000원대이며, 표준편차가 28,000원에 육박하는 수준으로 값의 변동폭이 극도로 큽니다. 
우량 제품들이 대개 2~4만 원대에 고르게 퍼져 있지만, 최댓값은 무려 78만 원을 넘어가며 왜도가 4.10인 전형적인 우편향 분포를 띱니다. 
이는 대시보드나 필터에서 획일적인 평균 가격선을 쓸 경우 왜곡이 생기므로 예산대에 맞춰 대중 보급형, 합리적 스탠다드, 프리미엄의 세 영역으로 쪼개는 룰이 적절함을 말해줍니다. 
둘째, 평점의 거동은 더욱 특이합니다. 평균 평점은 무려 4.57점으로 중위값인 4.7점과 75% 분위수인 4.8점과 매우 가까워, 대부분의 상품 평점이 5점 만점에 4.7점 내외로 초집중되는 좌편향 왜도(-5.20)가 나타납니다. 
이 상향 평준화 현상은 단순한 '평점 평균값'만으로 추천 순위를 결정할 경우 차별성이 떨어진다는 치명적인 문제를 야기하므로 가중 랭킹을 설계해야 합니다.
-->

---

# 📈 3. 리뷰 수(Review Count) 변수 심층 분석

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>롱테일(Long-tail) 분포와 파레토 법칙의 통계적 입증</h2>
    <ul>
      <li><span class="accent">평균 리뷰 수</span>: 2,266건, 반면 <span class="accent">중위값</span>은 단 234건</li>
      <li>최댓값은 무려 486,127건으로 평균과 극단적인 격차 발생</li>
      <li>왜도가 <span class="accent">19.24</span>에 달해 우측 꼬리가 매우 길고 얇은 전형적인 롱테일 구조</li>
      <li>상위 10% 미만의 인기 스테디셀러 제품(예: 나우푸드 단일 성분 직구 품목)이 시장 내 리뷰 총합의 80% 이상을 장악하는 파레토 지배 현상 포착</li>
      <li><span class="accent">비즈니스 시사점</span>: 대시보드 시각화 시 단순 리니어 축 사용을 지양하고, 반드시 <span class="accent">로그 변환(Log Scale, log10)</span>을 적용해 시각적 스펙트럼 확보 필요</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[리뷰 왜도 검증]</b><br>
      - 가격 왜도: 4.10<br>
      - 평점 왜도: -5.20<br>
      - 리뷰 왜도: 19.24 (최고 수준)<br><br>
      * 리뷰 데이터는 스케일 조정(Log Scale) 필수 보정 대상입니다.</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
수치형 피처의 마지막 축인 리뷰 수의 통계적 거동을 함께 보시겠습니다. 
리뷰 수는 해당 제품의 인지도와 누적 판매량을 대변하는 가장 확실한 '시장 반응 척도'입니다. 
통계를 보면 평균은 약 2,200여 건이지만 중위값은 고작 234건에 그칩니다. 
반면 최댓값은 약 48만 6천 건에 달해, 왜도가 19.24라는 가공할 수준의 우편향 롱테일 구조를 보이고 있습니다. 
이는 건기식 이커머스 생태계가 신규 론칭된 수만 개의 후발 주자 제품과 소수의 전통적인 탑 티어 메이저 스테디셀러 제품으로 극명하게 쪼개져 있음을 방증합니다. 
이 14개 휴대성 제품군 안에서도 특히 스틱형 개별 포장으로 설계된 파우더/분말 제형에서 유저 리뷰의 밀도가 가장 높게 관찰되었습니다. 
이 특징은 비즈니스 분석 전문가로서 중요한 테크니컬 가이드를 줍니다. 
첫째, 대시보드 개발 시 축을 그대로 두면 하위 제품들이 0에 가까운 위치에 뭉쳐 차트를 알아볼 수 없으므로 반드시 상용로그 스케일을 매겨 시각화 영역의 가독성을 다듬어야 합니다.
-->

---

# 🏭 4. 범주형 변수 기술통계 심층 분석

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>플랫폼 채널 및 제조사 브랜드의 편중 분석</h2>
    <ul>
      <li><span class="accent">플랫폼(Platform) 분포</span>: 아이허브가 25,171건(89.1%)으로 지배적</li>
      <li>올리브영 2,560건(9.1%), 쿠팡 508건(1.8%) 순으로 구성</li>
      <li>아이허브 단독 채널 의존도가 매우 높아 전체 통계량 산출 시 글로벌 직구 데이터 경향성으로 강하게 쏠리는 현상 발생</li>
      <li><span class="accent">제조 브랜드(Brand) 다각화</span>: 고유 브랜드 1,251개 등록</li>
      <li>나우푸드(NOW Foods)가 1,027건(3.65%)으로 점유율 1위</li>
      <li>스완슨, 뉴트리코스트 등 직구 가성비 거대 제조사들이 공급 주도</li>
      <li><span class="accent">시사점</span>: 플랫폼별 가중치를 표준화하고, 채널 세그먼트 분리 필요</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[탑 3 브랜드 점유]</b><br>
      1. NOW Foods: 1,027개<br>
      2. Swanson: 955개<br>
      3. Nutricost: 889개<br><br>
      * 상위 3대 브랜드가 모두 글로벌 직구형 가성비 단일 성분 제품군입니다.</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
이제 데이터를 구성하는 범주형 칼럼인 플랫폼 채널과 브랜드 제조사에 대한 기술통계를 살펴보겠습니다. 
우선 플랫폼의 경우, 통합 데이터의 무려 89.1%가 글로벌 직구 건기식 쇼핑몰인 아이허브에서 기인합니다. 
올리브영은 9.1%, 쿠팡은 1.8%에 불과합니다. 
이처럼 극단적인 플랫폼 수집량 불균형은 글로벌 플랫폼의 거대한 취급 품목 수(SKU) 차이에서 발생합니다. 
만약 우리가 단순 평균 모델로 추천 알고리즘을 빌드하면, 유저가 국내 배송을 원하든 원치 않든 무조건 직구 브랜드 위주로 도출되는 심각한 '채널 편향'이 발생합니다. 
따라서 추천 알고리즘 가중치 설계 시 플랫폼별 가중 보정치를 부여하거나, 채널 선호를 분리 적용하는 아키텍처가 요구됩니다.
-->

---

# 📊 5. 플랫폼 및 브랜드 데이터의 구조적 특성

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 1: 플랫폼 비중 및 상위 브랜드 분석</h2>
    <ul>
      <li><span class="accent">플랫폼 비중 시각화</span>: 아이허브 채널의 독점적 구성 확인</li>
      <li>국내 건기식 커머스 생태계(올리브영, 쿠팡) 대비 압도적 SKU 수</li>
      <li><span class="accent">상위 브랜드 시각화</span>: 글로벌 가성비 대형사 중심의 시장 다각화</li>
      <li>나우푸드, 스완슨 등 롱테일 곡선의 상단에 위치한 기업 중심 분포</li>
      <li>하위 50% 브랜드들은 단 1~2개의 단독 상품만을 보유하여, 소수의 대기업과 다수의 파편화된 소규모 브랜드가 대치하는 구조</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/01_platform_distribution.png" alt="플랫폼 분포">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 1: 플랫폼별 상품 등록 수 분포</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
이전 장에서 설명해 드린 수치형 및 범주형 변수의 데이터 불균형 문제를 시각화 1의 그래프를 통해 더욱 명확하게 인지하실 수 있습니다. 
우측에 배치된 시각화 1 차트는 플랫폼별 등록 상품 수의 분포를 보여줍니다. 
보시는 바와 같이 아이허브가 압도적으로 높은 막대를 보이고 있으며, 올리브영과 쿠팡은 상대적으로 매우 낮게 형성되어 있습니다. 
이 시각 자료는 우리가 데이터 셋의 채널 믹스를 수행할 때 국내 소비자 맞춤 큐레이션을 위해서는 데이터의 비율 가중치를 평활화하거나 유저 세그먼트별로 분리 가중치를 주어야 한다는 비즈니스 분석 전문가의 권고를 강력하게 지지합니다. 
대시보드 트렌드를 볼 때도 이 브랜드 집중도를 감안해야 올바른 비즈니스 동향 파악이 가능합니다.
-->

---

# 📊 6. 상위 30개 건강기능식품 브랜드 등록 분포

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 2: 메이저 제조사의 공급 강도와 시장 지배력</h2>
    <ul>
      <li><span class="accent">브랜드 집중 현상</span>: 상위 제조사의 독과점적 SKU 공급 확인</li>
      <li>나우푸드, 스완슨 비타민, 뉴트리코스트가 탑 3의 위치 점유</li>
      <li>이 세 대형 제조사는 다품종 소량 생산 및 가성비 중심 직구 전략으로 이커머스 건기식 생태계의 품목 다양성을 견인</li>
      <li><span class="accent">추천 룰 빌드 전략</span>: 안정 지향적 유저(메이저 브랜드 선호)와 틈새 탐험형 유저(신규 브랜드 선호) 세그먼트를 문진을 통해 구별하고 노출 가중치 다변화 적용</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/02_top_30_brands.png" alt="상위 브랜드">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 2: 상위 30개 브랜드 등록 분포</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
우측의 시각화 2 그래프는 상위 30개 브랜드의 등록 분포를 나타내고 있습니다. 
나우푸드, 스완슨, 뉴트리코스트 등 글로벌 건기식의 대표적 가성비 대형사들이 차트 상단을 길게 메우고 있습니다. 
이들 거대 공급 업체는 다양한 단일 영양소 성분의 조합과 대량 생산을 기반으로 이커머스 유통 시장의 다양성을 실질적으로 장악하고 있습니다. 
이처럼 집중된 브랜드 분포 특성은 추천 엔진 설계자에게 매우 가치 있는 정보를 전달합니다. 
유저 중에는 잘 알려진 유명 브랜드의 메이저 제품을 안전하게 섭취하고 싶어 하는 보수적 세그먼트가 있는 반면, 대기업 제조사는 아니더라도 자신의 특정 건강 고민에 최적화된 신흥 브랜드를 탐험하려는 세그먼트가 존재하므로 노출 가중치 다변화 룰이 요구됩니다.
-->

---

# 🛠️ 7. 파트 1: 제형(Form) 9대 분류 표준화

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>비정형 데이터의 구조화 및 '정' 오탐 방지 정규표현식 룰</h2>
    <ul>
      <li><span class="accent">대상 칼럼</span>: 비정형 텍스트인 <code>product_name</code> 및 <code>description</code></li>
      <li><span class="accent">9대 분류 체계</span>: 정제, 캡슐, 구미/젤리, 파우더/분말, 액상/샷, 스틱, 스트립/필름, 패치, 기타(Unknown)</li>
      <li><span class="accent">정제 제형 매칭의 오탐 리스크</span>: '정' 문자 단독 서치 시 '정보', '정밀', '정상', '오늘드림' 등 일반 단어에 무차별 오매칭되는 문제 발생</li>
      <li><span class="accent">정밀 룰 고도화</span>: 정제, 타블렛, tablet 단어 검색과 더불어 정규표현식 <code>\d+\s*정\b|\b정\b</code>(예: 60정, 120정 및 단독 어휘) 매칭을 주입하여 오탐 방어 완료</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[분류 적용 정규표현식]</b><br>
      <code>re.search(r'\d+\s*정\b|\b정\b', text)</code><br><br>
      * 숫자 뒤에 결합한 '정' 수량 단위를 검출하여 복용 형태가 정제인 상품을 오차 없이 추출해냅니다.</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
비정형 텍스트 데이터를 정형화된 추천 피처로 전환하기 위한 제형 9대 분류 표준화 프로세스에 대해 설명하겠습니다. 
우리는 비정형 데이터인 제품명과 상세설명을 분석하여 정제, 캡슐, 구미/젤리, 파우더/분말, 액상/샷, 스틱, 스트립/필름, 패치, 그리고 기타 미분류의 9가지 형태로 구조화하는 분류 알고리즘을 개발했습니다. 
여기서 데이터 사이언스 관점의 정교한 예외 처리가 요구됩니다. 
특히 전통적인 알약 제형인 '정제'를 추출하기 위해 단순히 '정'이라는 한 글자 텍스트 매칭을 시도하면, 올리브영 데이터 등에 빈번히 등장하는 일반 어휘에 포함된 글자까지 모두 정제 제형으로 휩쓸어 분류하는 극심한 오탐이 발생하게 됩니다. 
이를 완벽히 필터링하기 위해 정제, 타블렛, 태블릿 등의 직관적인 어휘 서치와 병행하여, 숫자 뒤에 결합한 수량 단위인 '정'을 추적하는 정규표현식 즉, `\d+\s*정\b` 또는 단어 경계로 구분된 독립된 `\b정\b` 형태만을 인정하는 정밀 매칭 코드를 구현하여 해결했습니다.
-->

---

# 📊 8. 제형별 데이터 분포 및 분류 현황

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>9대 제형의 빈도 분포 통계 및 인사이트</h2>
    <ul>
      <li><span class="accent">캡슐(Capsule)</span>: 12,610개 (44.66%)로 점유율 1위</li>
      <li><span class="accent">정제(Tablet)</span>: 4,639개 (16.43%)로 2위</li>
      <li><span class="accent">파우더/분말(Powder)</span>: 4,111개 (14.56%)로 3위</li>
      <li>전체 건강기능식품의 약 <span class="accent">75.7%</span>가 전통적인 3대 제형(캡슐, 정제, 분말)으로 구성되어 여전히 압도적인 메인스트림 형성</li>
      <li><span class="accent">구미/젤리 및 액상/샷</span>: 각각 1,515개(5.36%), 2,718개(9.63%) 포진</li>
      <li><span class="accent">기타(Unknown)</span>: 2,314개 (8.20%) 존재 ➡️ 텍스트 마이닝을 통한 원인 분석 필요</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[제형별 품목 수 요약]</b><br>
      - 캡슐: 12,610개 (44.7%)<br>
      - 정제: 4,639개 (16.4%)<br>
      - 파우더: 4,111개 (14.6%)<br>
      - 액상/샷: 2,718개 (9.6%)<br>
      - Unknown: 2,314개 (8.2%)<br>
      - 구미/젤리: 1,515개 (5.4%)</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
제형 분류 알고리즘을 전체 데이터 셋에 일괄 적용한 결과와 분포 현황입니다. 
분석 결과, 건기식 시장의 지배적 제형은 단연 캡슐 제형으로 전체의 44.66%에 달하는 12,610개가 존재합니다. 
그 뒤를 이어 알약 형태의 정제가 16.43%, 가루 형태인 파우더/분말이 14.56%로 집계되었습니다. 
이 전통적인 3대 주류 제형의 총합 비중은 무려 75.7%를 넘어섭니다. 
이는 건강기능식품의 핵심 생산 및 보관 안정성을 보장하는 고전적 형태가 여전히 전체 시장 공급의 뼈대를 이루고 있음을 실증합니다. 
반면 복용이 재미있고 맛이 가미되어 선호도가 높은 구미/젤리나 액상 제형은 상대적으로 적은 볼륨을 띱니다. 
또한 아직 룰셋에 매칭되지 않고 '기타(Unknown)' 제형으로 분류된 상품이 약 2,314개로 8.20%를 점유하고 있습니다. 
이 미분류 집단에 숨겨진 텍스트 데이터의 특징을 TF-IDF 기법으로 상세히 파헤쳐 볼 필요가 있습니다.
-->

---

# 📊 9. 플랫폼별 제형 구성 분포 비교

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 3: 이커머스 채널별 제형 소싱 전략 분석</h2>
    <ul>
      <li><span class="accent">아이허브 제형 전략</span>: 캡슐(48.2%) 중심의 정통 의약품형 직구 건기식 위주 구성</li>
      <li><span class="accent">올리브영 제형 전략</span>: 구미/젤리(8.9%), 액상/샷(5.6%) 및 스틱(3.1%) 등 맛과 트렌디한 편의성을 강조한 섭취 형태 대거 소싱</li>
      <li>올리브영의 '기타(Unknown)' 비중이 40.7%로 매우 큼 ➡️ 뷰티/콜라겐 관련 신흥 제형이 대거 쏠려있음을 암시</li>
      <li><span class="accent">쿠팡 제형 전략</span>: 정제(35.8%) 및 기타(51.2%) 위주 포진</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/03_platform_form_crosstab.png" alt="플랫폼별 제형 분포">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 3: 플랫폼별 제형 분포 백분율 비교</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
우측의 시각화 3 stacked bar 차트는 각 이커머스 플랫폼 채널이 지닌 고유의 제형 소싱 전략과 세일즈 정체성을 시각적으로 웅변해 줍니다. 
아이허브의 경우 캡슐 제형이 거의 절반에 달하는 48.2%를 차지는 반면, 국내 드럭스토어 강자인 올리브영은 구미/젤리가 8.9%, 액상/샷이 5.6%, 스틱이 3.1%로 타 플랫폼 대비 훨씬 높은 다각화 비중을 보입니다. 
올리브영은 젊은 유저층이 일상에서 간편하게 맛을 즐기며 섭취할 수 있는 트렌디한 제형을 주력으로 배치하고 있는 것입니다. 
또한 올리브영에서 40.7%에 달하는 미분류 '기타(Unknown)' 제형의 존재가 눈에 땕니다. 
이는 뷰티 케어와 건기식이 융합된 올리브영 특성상 화장품형 이너뷰티나 신개념 겔, 슬림 라인 등 기존 룰셋에 걸리지 않은 특이 신규 제형들이 시장에 다수 포진해 있음을 의미하므로 큐레이션 알고리즘 설계에 활용해야 합니다.
-->

---

# 📊 10. 미분류(Unknown) 제형의 TF-IDF 마이닝

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 4: 미분류(기타) 제형 내 텍스트 피처 가중치 분석</h2>
    <ul>
      <li><span class="accent">마이닝 목표</span>: '기타(Unknown)' 제형으로 판정된 8.2% 데이터의 원인 규명 및 분류 알고리즘 개선 방향 획득</li>
      <li><span class="accent">핵심 추출 단어</span>: '오늘드림', '세일', '쿠폰' 등 채널별 광고 및 프로모션 노이즈 텍스트 다수 분포 포착</li>
      <li><span class="accent">신규 제형 후보군 검출</span>: <span class="accent">'츄어블'(Chewable), '패킷'(Packet), '스프레이'(Spray)</span> 키워드가 주요 TF-IDF 가중치 상위에 랭크됨</li>
      <li><span class="accent">룰 보완 전략</span>: '츄어블'은 구미/젤리 룰셋에 흡수하고, '패킷'은 스틱/분말 룰셋에, '스프레이'는 액상 룰셋에 추가 반영하여 분류 정밀도 개선</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/04_unknown_keywords_tfidf.png" alt="Unknown TF-IDF">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 4: Unknown 제형 내 TF-IDF 핵심 키워드</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
분석의 정밀도를 극한으로 끌어올리기 위해 진행한 미분류(기타) 데이터 셋 대상의 TF-IDF 텍스트 마이닝 분석 결과입니다. 
우리는 형태소 분석기를 돌리는 대신 scikit-learn의 TF-IDF 벡터라이저를 적용해 단어 가중치를 계산하고 시각화 4 차트로 가시화했습니다. 
분석 결과, 우선 올리브영 등에서 수집된 '오늘드림', '세일', '쿠폰' 같은 마케팅용 단어들이 대량으로 섞여 미분류를 유발했음을 밝혀냈습니다. 
하지만 비즈니스 관점에서 더욱 핵심적인 소득은 '츄어블(Chewable)', '패킷(Packet)', '스프레이(Spray)' 등의 실질적인 신규 제형 관련 명사 키워드들이 상당한 TF-IDF 가중치를 점유한 상태로 상위 20개 내에 고스란히 포진되어 있었다는 점입니다. 
이들을 각각의 제형 룰셋에 보강 통합한다면, 미분류 기타 데이터의 비율을 획기적으로 낮추고 추천 정밀도를 극대화할 수 있을 것입니다.
-->

---

# 🎯 11. 파트 2: 복용 편의성 & 휴대성 감성 분석

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>문진 변수 연계를 위한 감성 키워드 매칭 스코어 설계</h2>
    <ul>
      <li><span class="accent">삼킴 편의성 키워드 사전</span>: `['목넘김', '알약 크기', '작아서', '삼키기', '부담 없는']` ➡️ swallow_score 변수로 누적 카운트 매핑</li>
      <li><span class="accent">휴대 편의성 키워드 사전</span>: `['개별포장', '휴대', '파우치', '외출', '가방', '스틱포']` ➡️ portability_score 변수로 누적 카운트 매핑</li>
      <li><span class="accent">대시보드 알고리즘 연계 목표</span>: 유저 문진 시 "알약을 삼키는 데 큰 부담을 느끼나요?" 혹은 "바쁜 직장 생활로 인해 휴대하기 편한 패키지를 선호하나요?"에 매칭할 최적의 상품 감성 필터 점수 확보</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[감성 스코어 산출식]</b><br>
      Score = Sum of Keyword Counts<br><br>
      - swallow_score >= 1 혹은 portability_score >= 1 인 상품군을 타겟 편의성 소구 제품으로 세그먼트화하여 맞춤 추천 풀에 진입시킵니다.</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
이번 2파트 분석에서는 유저의 문진 변수 중 가장 직접적인 신체적 불편감과 라이프스타일 패턴을 연결해 주기 위한 감성 분석 스코어 설계에 대해 다룹니다. 
우리는 유저가 문진 시 호소하는 두 가지 페인포인트, 즉 '알약을 삼킬 때 목구멍이 좁아 느껴지는 이물감'과 '외출이나 출근 시 간편하게 가방에 넣어 다닐 수 있는 휴대성'을 제품 데이터와 연결해야 합니다. 
이를 위해 상세설명 텍스트 필드를 대상으로 한 감성 사전 키워드 매칭 함수를 빌드했습니다. 
삼킴 편의성 스코어에는 '목넘김', '알약 크기', '삼키기' 등 실제 유저들이 복용 편의를 느낄 때 사용하는 단어들을 사전으로 정의해 빈도를 합산하였고, 휴대 편의성 스코어 역시 '개별포장', '파우치', '외출' 등의 핵심 어휘 빈도를 집계하도록 구성했습니다. 
이 가공 과정을 거쳐 신설된 스코어 변수들은 향후 뉴트리핏 대시보드 및 추천 엔진의 핵심 필터로 작동하게 될 것입니다.
-->

---

# 📊 12. 감성 키워드 분포 현황 및 데이터 수집 한계

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 5 & 6: 감성 어휘의 수집 빈도 분포 및 한계점 진단</h2>
    <ul>
      <li><span class="accent">삼킴 편의성 소구 제품</span>: 통합 DB 내 단 0개 매칭</li>
      <li><span class="accent">휴대 편의성 소구 제품</span>: 통합 DB 내 단 14개 매칭</li>
      <li><span class="accent">텍스트 한계 원인 분석</span>: 현재 수집된 이커머스 <code>description</code> 컬럼이 상품 고유 상세 기술서 전문이 아니라 프로모션용 태그(올리브영)나 수량 메타 데이터(아이허브) 위주로 구성되어 나타나는 정보 누락 한계</li>
      <li><span class="accent">비즈니스 해결안</span>: 1단계 매칭 룰을 적용하되, 향후 <span class="accent">사용자 실제 리뷰 텍스트(Review Text)</span>의 전면적 수집 및 NLP 감성 임베딩 분석 파이프라인의 보완이 추천 엔진의 실질적 고도화에 필수적</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="image-row">
      <img src="../images/05_swallow_score_hist.png" alt="삼킴 스코어 분포">
      <img src="../images/06_portability_score_hist.png" alt="휴대성 스코어 분포">
    </div>
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 5 & 6: 편의성 및 휴대성 스코어 분포</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
좌측과 우측에 나란히 배치된 시각화 5와 시각화 6 차트는 데이터 사이언티스트의 냉철한 시각으로 바라본 데이터 수집 상의 한계점을 극명하게 짚어줍니다. 
감성 사전을 매핑한 결과, 놀랍게도 삼킴 스코어가 1점 이상인 제품은 전체 28,000여 개 중 0개였고, 휴대성 스코어를 획득한 제품 역시 단 14개에 불과했습니다. 
원인을 역추적해 본 결과, 크롤링된 `description` 컬럼이 브랜드사가 올린 상세 안내문 전문이 아니라, 아이허브의 규격 텍스트와 올리브영의 짧은 쿠폰 태그들로 단조롭게 채워져 있기 때문인 것으로 규명되었습니다. 
이 분석 결과는 매우 중요한 비즈니스 전환점을 시사합니다. 
단순한 룰 기반의 상세설명 키워드 매칭만으로는 유저들의 감성적 페인포인트를 맞춤형으로 걸러주기에 현시점의 데이터 피처 정보량이 지나치게 얕습니다. 
따라서 우리는 룰셋의 뼈대는 유지하되, 이 한계를 극복하기 위해 사용자 실제 리뷰 텍스트 데이터 셋을 별도 크롤링하여 그 텍스트에 감성 사전 매핑을 매겨 스코어를 누적하는 후속 파이프라인 보완 작업을 제안합니다.
-->

---

# 📊 13. 휴대성 편의성 소구에 따른 시장 반응 분석

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 7: 휴대 편의성 소구 제품의 리뷰 및 평점 분석</h2>
    <ul>
      <li><span class="accent">평점 추이</span>: 일반 제품 평균 4.57점 대비 휴대 소구 제품군은 평균 4.0점으로 소폭 하락 ➡️ 휴대용 개별 포장 패키징 변경으로 인한 만족도 편차 발생 여부 추가 검증 필요</li>
      <li><span class="accent">리뷰 수 추이</span>: 일반 제품 평균 2,267건 대비 휴대 소구 제품군은 평균 353건의 유의미한 반응 수 획득</li>
      <li><span class="accent">제형별 휴대성 분석</span>: 휴대 소구 제품군 중 특히 파우더/분말(스틱포 패키지 형태) 제형에서 유저 리뷰 반응 포착 ➡️ 휴대 편의성이 구매 요인으로 직결됨을 방증</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/07_portability_comparison.png" alt="휴대성 비교">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 7: 휴대 편의성 소구 여부별 평점/리뷰 비교</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
우측의 시각화 7 그래프는 휴대 편의성 키워드를 소구하고 있는 제품군과 그렇지 않은 일반 제품군 간의 평점 및 리뷰 수 격차를 나타내고 있습니다. 
표본 수가 14개로 극히 적은 통계적 유의성 한계는 존재하지만, 매우 흥미로운 패턴이 발견되었습니다. 
평점의 경우 휴대성 언급 제품군이 4.0점으로 일반 제품의 4.57점 대비 약간 낮게 포지셔닝되어 있습니다. 
이는 가성비 중심의 대용량 통형 패키지에서 휴대용 개별 파우치나 스틱포 패키지로 전환되면서, 용량 대비 가격 불만이 평점 삭감 요인으로 일부 작용했을 개연성을 암시합니다. 
반면 평균 리뷰 수의 경우 휴대성을 전면에 기재한 14개 특화 제품군에서 평균 353건의 단단한 유저 피드백이 발생하여, 시장 수요의 실체적 존재를 증명해 줍니다. 
이 사실은 서비스 기획 관점에서 직장인 타겟 추천 시, 맛과 물 없이 먹는 복용 편의를 보장하는 '분말 스틱포' 제형군을 주력 큐레이션군으로 선정하고, 대시보드 내 휴대성 섹션에 적극 배치해야 시장 세일즈를 자극할 수 있음을 뚜렷하게 가이드해 줍니다.
-->

---

# 📊 14. 휴대성 소구 상품의 제형별 시장 반응 강도

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 8: 휴대성이 언급된 제품군의 제형별 리뷰수 비교</h2>
    <ul>
      <li><span class="accent">분말/파우더 제형 강세</span>: 휴대성을 강조한 제품군 내에서 평균 1,500건 이상의 압도적인 유저 리뷰 수 기록 확인</li>
      <li>정제나 기타 액상 제형 대비 스틱포 형태의 분말 제형에 대한 소비자 시장 선호도가 매우 뚜렷하게 도출됨</li>
      <li><span class="accent">비즈니스 큐레이션 룰</span>: 문진에서 '휴대성 중시' 및 '직장 내 섭취'를 선택한 유저에게 유산균, 콜라겐 카테고리 추천 시 캡슐 대신 '스틱 분말' 제품을 우선순위 노출</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/08_portability_form_reviews.png" alt="제형별 휴대성 리뷰">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 8: 휴대성 소구 제품의 제형별 평균 리뷰수</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
우측의 시각화 8 차트는 휴대성 키워드가 직접적으로 언급된 상품군 안에서 제형별로 평균 리뷰 수의 격차가 어떻게 벌어지는지를 규명합니다. 
가장 특징적인 것은 개별 스틱포 포장이 대중화된 분말/파우더 제형의 리뷰 반응 수가 타 제형군을 멀찌감치 따돌리고 압도적인 수치를 나타내고 있다는 사실입니다. 
이는 소비자가 휴대성을 염두에 두고 건강기능식품을 구매할 때 가장 직관적으로 떠올리고 선호하는 제형이 바로 분말 스틱포 형태임을 명증합니다. 
따라서 우리는 큐레이션 알고리즘 설계 시 유저가 문진을 통해 휴대성과 이동 편의를 최선호 사항으로 선택한 경우, 전통적인 통형 캡슐이나 정제 제품의 노출 랭킹 스코어를 낮추고 스틱포 형태의 유산균이나 콜라겐 제품을 최상단 노출 랭킹으로 정렬하도록 매핑 룰을 다듬을 것입니다.
-->

---

# 🏷️ 15. 파트 3: 8대 건강 고민 1차 라벨링 및 매핑

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>유저 문진 고민 1순위와 상품 핵심 성분 매핑 아키텍처</h2>
    <ul>
      <li><span class="accent">8대 건강 고민 카테고리</span>: 피로, 피부, 체중, 집중력, 장 건강, 수면, 스트레스, 눈 건강</li>
      <li><span class="accent">매핑 로직</span>: 각 건강 고민별 대표 기능성 성분 및 증상 명사 사전을 구축하고 상품명과 설명글을 다중 매핑하는 룰 정의</li>
      <li><span class="accent">매핑 사전 예시</span>:
        <ul>
          <li>피로 ➡️ 비타민B, 밀크씨슬, 홍삼, 아르기닌, 활력, 에너지 등</li>
          <li>장 건강 ➡️ 유산균, 프로바이오틱스, 프리바이오틱스, 차전자피 등</li>
          <li>피부 ➡️ 콜라겐, 히알루론산, 엘라스틴, 글루타치온, 이너뷰티 등</li>
        </ul>
      </li>
      <li><span class="accent">다중 매핑 대응</span>: 한 상품이 다중 고민에 매칭될 시 분석적 왜곡을 없애기 위해 판다스 `explode` 가공을 거쳐 고민별 통계 산출 진행</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="info-box">
      <p><b>[건강고민 매핑 구조]</b><br>
      - 문진 입력값: 피부 고민<br>
      - 매핑 사전 탐색: '콜라겐', '히알루론산'<br>
      - 매칭 필터링 ➡️ 해당 제품 추천 풀 진입<br><br>
      * 다중 고민 매칭(Exploded)을 허용하여 개인화 매칭 스펙트럼을 넓힙니다.</p>
    </div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
추천 알고리즘의 심장부가 될 8대 건강 고민 1차 라벨링 및 매핑 아키텍처 설계 장입니다. 
유저가 문진을 시작하여 가장 먼저 고르는 1순위 피지오지컬 페인포인트 즉, 피로, 피부, 체중, 집중력, 장 건강, 수면, 스트레스, 눈 건강의 8대 카테고리와 상품 데이터베이스를 엮기 위한 매핑 외적 규칙을 설계했습니다. 
각 고민별로 대표 기능성 원료 성분명 사전을 빌드했습니다. 
예를 들어 '피로'를 호소하는 유저에게는 에너지 대사를 돕는 비타민B군, 밀크씨슬, 홍삼 등과 활력, 에너지 같은 효능 키워드를 매치하게 하였고, '피부' 고민에는 콜라겐, 히알루론산, 글루타치온을 연결하였습니다. 
단일 제품이 피로 회복과 피부 관리를 동시에 타겟하는 다중 효능을 가질 수 있으므로, 데이터셋 설계 시 다중 라벨링을 지원하도록 구현하였고, 통계 산출 시에는 이를 개별 행으로 확장하는 `explode` 전처리 기법을 적용해 각 고민 카테고리별로 정밀한 통계를 확보했습니다. 
이 맵 구조는 유저가 특정 질환 완화나 예방 목적의 건기식을 서치할 때 가장 관련성 높은 성분의 제품을 첫 노출 상단에 랭킹해 주는 뼈대 룰셋으로 작용합니다.
-->

---

# 📊 16. 건강 고민별 상품 등록 분포 및 가격 스펙트럼

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 9 & 10: 기능성 카테고별 시장 공급 및 가격 분포</h2>
    <ul>
      <li><span class="accent">공급 탑 3 카테고리</span>: '피부'(993개), '피로'(881개), '수면'(679개) 순 ➡️ 이미 공급이 고도로 활성화된 레드오션 시장 구성</li>
      <li><span class="accent">블루오션 카테고리</span>: '체중'(220개), '스트레스'(188개) ➡️ 공급 품목 수는 적으나 현대 유저 니즈가 높아 특화 큐레이션 전략 영역으로 적합</li>
      <li><span class="accent">가격 분포 특징</span>: '피부'(평균 39,626원) 및 '집중력'(평균 38,079원) 기능성 상품 단가가 높게 포진, '수면'(25,081원)과 '눈 건강'(28,691원)은 가성비 대중화 정착</li>
    </ul>
  </div>
  <div class="visual-content">
    <div class="image-row">
      <img src="../images/09_health_concern_distribution.png" alt="건강 고민 분포">
      <img src="../images/10_health_concern_price_boxplot.png" alt="가격 분포">
    </div>
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 9 & 10: 8대 건강 고민별 등록 수 및 가격 분포</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
이번 장에서는 건강 고민별로 도출된 상품 공급 강도와 지불 예산 스펙트럼을 보여주는 시각화 9 및 시각화 10 그래프의 병렬 분석 리포트입니다. 
공급 측면에서 가장 물량이 쏟아지는 영역은 이너뷰티 붐을 타고 수많은 제조사가 진입한 '피부' 카테고리와 에너지를 표방하는 '피로', '수면' 순입니다. 
반면 '체중'과 '스트레스' 분야는 200개 미만의 소량 품목으로 구성되어 있으나 현대 소비자들의 멘탈 웰니스 및 다이어트 관심 폭증을 감안하면 뉴트리핏의 특화 큐레이션으로 집중 육성하기에 가장 알맞은 블루오션 영역입니다. 
더불어 가격 분포(Box Plot)를 보면, 피부와 집중력 기능성 제품군은 원료 품질 및 PS 고급화 마케팅에 힘입어 평균 3만 8~9천 원대의 고가 라인을 형성하고 있는 반면, 수면 개선 분야는 2만 5천 원대 수준으로 저렴하고 균일한 스펙트럼을 보입니다. 
이 단가 차이는 피부 고민 유저 유입 시 고품질 콜라겐 앰플을 제안하는 업셀링 마케팅 룰을 가동하고, 수면 고민 유저에게는 대용량 테아닌 복합제를 번들로 묶어 제공하는 가격 최적화 로직의 설계를 뒷받침합니다.
-->

---

# 🏆 17. 건강 고민별 이커머스 인기 제형 TOP 3

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

## 고민별 리뷰 누적 총합 기준 시장 크기 랭킹 (초기 디폴트 추천 룰셋)

| 건강 고민 | 1위 인기 제형 (리뷰 수) | 2위 인기 제형 (리뷰 수) | 3위 인기 제형 (리뷰 수) |
| :--- | :--- | :--- | :--- |
| **피로** | 캡슐 (53.9만) | 정제 (39.3만) | 기타/Unknown (8.8만) |
| **장 건강** | 기타/Unknown (51.2만) | 캡슐 (27.1만) | 정제 (26.3만) |
| **눈 건강** | 캡슐 (89.5만) | 정제 (36.6만) | 구미/젤리 (8.6만) |
| **피부** | 파우더/분말 (162.5만) | 정제 (79.5만) | 캡슐 (66.2만) |
| **수면** | 정제 (48.0만) | 캡슐 (28.7만) | 구미/젤리 (13.7만) |
| **스트레스**| 캡슐 (6.7만) | 정제 (6.6만) | 액상/샷 (1.4만) |

- **알고리즘 반영**: 피부 매치 시 파우더(스틱 포함) 스코어 가중 우선 배정, 수면 매치 시 정제 제형을 1선에 추천하는 동적 디폴트 정렬 룰 확립

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
우리가 데이터 분석을 통해 이끌어낸 아주 강력한 대시보드 핵심 지표이자 추천 룰의 디폴트 초기 테이블인 '고민별 인기 제형 TOP 3' 순위입니다. 
리뷰 누적 총합이라는 시장 점유도 (Market Volume)를 바탕으로 랭킹을 도출하여 한눈에 보이도록 도표로 정리했습니다. 
보시는 바와 같이 피로, 장 건강, 눈 건강, 수면 등 대부분의 주류 카테고리에서는 시장의 대량 유통을 주도하는 캡슐과 정제 제형이 1, 2위를 독식하고 있습니다. 
그러나 피부 건강 영역만큼은 다릅니다. 피부 건강에서는 가루로 타 먹거나 스틱포로 털어먹는 '파우더/분말' 제형이 무려 162.5만 건의 압도적 리뷰 반응을 얻으며 당당히 1위에 등극해 있습니다. 
이 팩트는 추천 엔진의 타겟 큐레이션을 아주 정밀하게 만들어 줍니다. 
예컨대 유저가 '피부 고민'을 체크하고 특별한 제형 기피 성향이 없을 때, 시스템은 디폴트로 캡슐이나 일반 알약이 아닌 '분말 스틱형 콜라겐' 제품군을 최상단 노출에 정렬해야 유저들의 대중적 지불 용의와 만족도 궤적에 부합함을 입증합니다. 
이와 반대로 수면 개선을 원하는 유저에게는 이미 시장 안정성과 규격 대중성이 확립되어 리뷰 48만 건으로 검증된 '정제(타블렛)'형 제품을 우선순위 1선으로 동적 세팅하는 룰의 직접적 정합성을 확인시켜 줍니다.
-->

---

# 📊 18. 가성비 분석 및 비즈니스 가설 검증

<div class="three-dots">
  <div class="dot dot-dark"></div>
  <div class="dot dot-medium"></div>
  <div class="dot dot-light"></div>
</div>

<div class="slide-container">
  <div class="text-content">
    <h2>시각화 11: 제형별 포지셔닝 맵 (평균 가격 vs 누적 리뷰 수)</h2>
    <ul>
      <li><span class="accent">가설 검증</span>: "젊은 2030은 편의성과 맛(구미, 액상, 스틱)을 위해 전통 알약 대비 고단가 비용을 기꺼이 지불할 것이다." ➡️ <span class="accent">절반의 기각 및 보완</span></li>
      <li><span class="accent">구미/젤리</span>: 평균 판매가 25,492원으로 주류 캡슐(35,928원)보다 오히려 매우 저렴하여, 젊은 층의 간식용 소량 구매 유입 뚜렷 (리뷰 160만 건 안착)</li>
      <li><span class="accent">파우더/분말 및 스틱</span>: 평균 단가가 무려 54,534원, 37,212원으로 고가에 형성되어 있으면서도 누적 리뷰 520만 건 및 24만 건 이상을 획득하며 가설에 가장 부합하는 확실한 프리미엄 시장 형성</li>
    </ul>
  </div>
  <div class="visual-content">
    <img src="../images/11_form_positioning_scatter.png" alt="제형별 가성비 산점도">
    <div style="font-size:0.75rem; color:#8A7A6A; margin-top:5px;">시각화 11: 제형별 가성비 포지셔닝 맵</div>
  </div>
</div>

<div class="footer-note">
  <span>NutriFit Data Innovation Group</span>
</div>

<!-- 
발표자 노트 (2분 분량):
마지막 장이자 비즈니스 분석 전문가로서 제안하는 대시보드 가설 검증의 하이라이트인 제형별 가성비 포지셔닝 맵입니다. 
우리는 '2030 유저들이 맛과 삼킴이 편한 젤리나 액상, 스틱 제형을 위해 기꺼이 더 높은 단가를 지불할 것이다'라는 가설을 세웠습니다. 
우측의 시각화 11 버블 차트를 보면 이 가설은 절반의 수정이 가해져야 합니다. 
첫째, 구미/젤리는 평균 단가가 약 2만 5천 원 선으로 오히려 대중 주류인 캡슐(3만 5천 원)보다 단가가 낮습니다. 
즉, 구미 젤리는 비싸서 안 먹는 제형이 아니라 가볍게 지갑을 열어 간식처럼 섭취하는 매스 가성비 입문용 제품으로 비즈니스 포지션을 유도해야 합니다. 
둘째, 가설의 진정한 주인공은 '파우더/분말(평균 54,000원)'과 '스틱포(평균 37,000원)' 제형이었습니다. 
이들은 전통 제형 대비 월등히 비싸지만 520만 건이 넘는 대규모 시장 리뷰 수요를 확보해 냈습니다. 
이 팩트 기반 포지셔닝 맵은 2030 직장인을 타겟으로 가격 가중치를 얹은 고급 '이너뷰티 분말' 또는 '에너지 스틱' 세트 상품을 상단에 큐레이션하여 장바구니 구매 금액을 높이고 채널 마진율을 극대화하는 가격 포지션 전략을 수립하는 데 있어 가장 명확한 비즈니스 정량적 시각 지표가 될 것입니다. 
이상으로 뉴트리핏 초정밀 EDA 및 추천 알고리즘 룰셋 가이드라인 발표를 모두 마치겠습니다. 경청해 주셔서 대단히 감사합니다.
-->
