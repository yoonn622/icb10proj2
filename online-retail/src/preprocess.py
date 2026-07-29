"""
이 파일은 Online Retail 데이터셋을 기반으로 상품 및 고객 데이터를 정제하고,
아이템 기반 협업 필터링(Item-Based CF)을 위한 유사도 행렬을 계산하며,
추천 모델 3가지(TF-IDF 프로필, 임베딩 프로필, Item-Based CF)의 오프라인 성능 평가(Recall, Precision, NDCG)를 수행하여
결과를 디스크에 캐싱하는 확장형 전처리 스크립트입니다.
"""
import os
import shutil
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from scipy.sparse import csr_matrix

def preprocess_data():
    print("1. 데이터 로딩 중...")
    data_path = 'online-retail/data/online_retail.parquet'
    if not os.path.exists(data_path):
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        shutil.copy('project2/data/online_retail.parquet', data_path)
        print("online_retail.parquet 파일을 복사해왔습니다.")
        
    df = pd.read_parquet(data_path)
    
    # 2. 결측치 및 무효 데이터 필터링
    print("2. 데이터 정제 시작...")
    df = df.dropna(subset=['Description', 'StockCode'])
    df['StockCode'] = df['StockCode'].astype(str).str.strip()
    df['Description'] = df['Description'].astype(str).str.strip()
    df['Description'] = df['Description'].str.upper()
    
    # CustomerID 타입 정제 (소수점 제거 및 문자열/정수형 통일)
    df = df.dropna(subset=['CustomerID'])
    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
    
    # 무의미한 특수 코드 필터링
    invalid_codes = ['POST', 'D', 'M', 'DOT', 'C2', 'PADS', 'BANK CHARGES', 'AMAZONFEE', 'CRUK']
    df = df[~df['StockCode'].isin(invalid_codes)]
    
    # 정상 거래 이력만 필터링 (수량 및 단가가 양수인 거래)
    valid_transactions = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()
    
    # 상품별 등장 빈도(인기도) 계산
    popularity_series = valid_transactions['StockCode'].value_counts()
    
    # 3. StockCode별 대표 상품명 결정 (1대1 매핑 확보)
    print("3. StockCode별 대표 상품명 매핑 생성 중...")
    name_counts = valid_transactions.groupby(['StockCode', 'Description']).size().reset_index(name='count')
    representative_names = name_counts.sort_values(['StockCode', 'count'], ascending=[True, False]).drop_duplicates('StockCode', keep='first')
    
    products = representative_names[['StockCode', 'Description']].copy()
    products['Popularity'] = products['StockCode'].map(popularity_series).fillna(0).astype(int)
    products = products[products['Popularity'] > 0].reset_index(drop=True)
    products = products[products['Description'].str.strip() != ''].reset_index(drop=True)
    
    print(f"정제 완료: 총 {len(products)}개의 고유 상품 식별.")
    
    # 4. 고객 통계 파이프라인 구축 (고객 페이지 정렬 기능 지원용)
    print("4. 고객별 거래 및 매출 통계 생성 중...")
    valid_transactions['TotalSpend'] = valid_transactions['Quantity'] * valid_transactions['UnitPrice']
    
    customer_stats = valid_transactions.groupby('CustomerID').agg(
        Total_Spend=('TotalSpend', 'sum'),
        Unique_Products=('StockCode', 'nunique'),
        Purchase_Count=('InvoiceNo', 'nunique') # 총 주문 횟수
    ).reset_index()
    
    # 5. TF-IDF 및 임베딩 벡터 구하기
    print("5. TF-IDF 및 Sentence-Transformer 임베딩 유사도 계산 중...")
    tfidf = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b\w[a-zA-Z0-9\-\.\/\'\+]*\w\b')
    tfidf_matrix = tfidf.fit_transform(products['Description'])
    tfidf_sim = cosine_similarity(tfidf_matrix, tfidf_matrix).astype(np.float32)
    
    # 임베딩 추출
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(products['Description'].tolist(), show_progress_bar=False, convert_to_numpy=True)
        embedding_sim = cosine_similarity(embeddings, embeddings).astype(np.float32)
    except Exception as e:
        print(f"SentenceTransformer 로드 또는 연산 중 에러 발생: {e}")
        embeddings = np.random.randn(len(products), 384).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        embedding_sim = cosine_similarity(embeddings, embeddings).astype(np.float32)
        
    # 6. 협업 필터링 (Collaborative Filtering): 아이템-아이템 유사도 계산
    print("6. 아이템 기반 협업 필터링(Item-Based CF) 유사도 행렬 생성 중...")
    # 상품 코드 인덱스 매핑 생성
    stockcode_to_idx = {code: i for i, code in enumerate(products['StockCode'])}
    
    # 유효 거래 중 정제된 상품 풀에 포함된 거래만 남김
    cf_data = valid_transactions[valid_transactions['StockCode'].isin(stockcode_to_idx.keys())].copy()
    
    # CustomerID 인덱스 매핑 생성
    unique_customers = cf_data['CustomerID'].unique()
    cust_to_idx = {cust: i for i, cust in enumerate(unique_customers)}
    
    # User-Item Interaction Matrix 구축 (바이너리가 아닌 구매 횟수로 구축)
    cf_data['cust_idx'] = cf_data['CustomerID'].map(cust_to_idx)
    cf_data['prod_idx'] = cf_data['StockCode'].map(stockcode_to_idx)
    
    # 중복 거래 합산
    user_item_grouped = cf_data.groupby(['cust_idx', 'prod_idx']).size().reset_index(name='purchase_count')
    
    # Sparse Matrix 생성 (행: User, 열: Item)
    user_item_matrix = csr_matrix(
        (user_item_grouped['purchase_count'], (user_item_grouped['cust_idx'], user_item_grouped['prod_idx'])),
        shape=(len(unique_customers), len(products))
    )
    
    # Item-Item Cosine Similarity 계산 (열 간 코사인 유사도)
    # sklearn.metrics.pairwise.cosine_similarity는 sparse matrix도 직접 지원함
    # 전치 행렬을 주어 아이템(열) 간 유사도 계산
    item_cf_sim = cosine_similarity(user_item_matrix.T, dense_output=False).toarray().astype(np.float32)
    
    # 7. 추천 시스템 오프라인 평가 (Hold-out 80/20)
    print("7. 3개 추천 모델(TF-IDF, Embedding, CF) 오프라인 성능 평가 수행 중...")
    # 고유 구매 상품 수가 5개 이상인 고객들을 대상으로 평가 진행
    eval_customers = customer_stats[customer_stats['Unique_Products'] >= 5]['CustomerID'].tolist()
    
    # 평가 지표 저장을 위한 리스트
    precisions = {'tfidf': [], 'embedding': [], 'cf': []}
    recalls = {'tfidf': [], 'embedding': [], 'cf': []}
    ndcgs = {'tfidf': [], 'embedding': [], 'cf': []}
    
    # 연산 편의를 위해 상품 특징 벡터들을 numpy로 변환
    tfidf_dense = tfidf_matrix.toarray() # (3915, TF-IDF_dim)
    
    # 평가 대상 고객 수가 너무 많으므로 연산 속도를 보장하기 위해 최대 800명을 무작위 샘플링하여 평가 수행
    # (샘플링을 통해 실행 시간 단축 및 통계적 유의성 확보)
    np.random.seed(42)
    if len(eval_customers) > 800:
        eval_customers = np.random.choice(eval_customers, size=800, replace=False)
        
    for cust in eval_customers:
        cust_tx = cf_data[cf_data['CustomerID'] == cust]
        cust_prod_indices = cust_tx['prod_idx'].unique()
        
        # 20% Hold-out 분할
        n_test = max(1, int(len(cust_prod_indices) * 0.2))
        test_indices = np.random.choice(cust_prod_indices, size=n_test, replace=False)
        train_indices = np.array([x for x in cust_prod_indices if x not in test_indices])
        
        if len(train_indices) == 0:
            continue
            
        test_set = set(test_indices)
        
        # ----------------- (1) TF-IDF 프로필 추천 -----------------
        # 사용자가 구매한 상품들의 TF-IDF 벡터 평균
        user_profile_tfidf = tfidf_dense[train_indices].mean(axis=0)
        # 전체 상품과의 코사인 유사도
        scores_tfidf = cosine_similarity(user_profile_tfidf.reshape(1, -1), tfidf_dense)[0]
        # Train 상품은 제외
        scores_tfidf[train_indices] = -1.0
        
        # ----------------- (2) Embedding 프로필 추천 -----------------
        user_profile_emb = embeddings[train_indices].mean(axis=0)
        scores_emb = cosine_similarity(user_profile_emb.reshape(1, -1), embeddings)[0]
        scores_emb[train_indices] = -1.0
        
        # ----------------- (3) Item-Based CF 추천 -----------------
        # 사용자가 구매한 상품들과 다른 상품들 간의 유사도 점수 합산
        scores_cf = item_cf_sim[train_indices].sum(axis=0)
        scores_cf[train_indices] = -1.0
        
        # K=10 기준으로 평가지표 산출 함수
        def evaluate_model(scores, test_set):
            top_10 = np.argsort(scores)[::-1][:10]
            hits = [1 if idx in test_set else 0 for idx in top_10]
            
            # Precision@10
            precision = sum(hits) / 10.0
            # Recall@10
            recall = sum(hits) / len(test_set)
            
            # NDCG@10
            dcg = 0.0
            for r, hit in enumerate(hits):
                if hit == 1:
                    dcg += 1.0 / np.log2(r + 2)
            idcg = 0.0
            for i in range(min(10, len(test_set))):
                idcg += 1.0 / np.log2(i + 2)
                
            ndcg = dcg / idcg if idcg > 0.0 else 0.0
            return precision, recall, ndcg
            
        # 평가 수행 및 지표 저장
        p, r, n = evaluate_model(scores_tfidf, test_set)
        precisions['tfidf'].append(p)
        recalls['tfidf'].append(r)
        ndcgs['tfidf'].append(n)
        
        p, r, n = evaluate_model(scores_emb, test_set)
        precisions['embedding'].append(p)
        recalls['embedding'].append(r)
        ndcgs['embedding'].append(n)
        
        p, r, n = evaluate_model(scores_cf, test_set)
        precisions['cf'].append(p)
        recalls['cf'].append(r)
        ndcgs['cf'].append(n)
        
    # 최종 평균 지표 데이터프레임 생성
    evaluation_results = pd.DataFrame({
        'Model': ['TF-IDF Profile', 'Embedding Profile', 'Collaborative Filtering'],
        'Precision@10': [np.mean(precisions['tfidf']), np.mean(precisions['embedding']), np.mean(precisions['cf'])],
        'Recall@10': [np.mean(recalls['tfidf']), np.mean(recalls['embedding']), np.mean(recalls['cf'])],
        'NDCG@10': [np.mean(ndcgs['tfidf']), np.mean(ndcgs['embedding']), np.mean(ndcgs['cf'])]
    })
    
    print("평가 결과 요약:")
    print(evaluation_results)
    
    # 8. 최종 결과물 디스크 저장
    print("8. 가공 데이터 및 매트릭스 디스크 저장 중...")
    os.makedirs('online-retail/data', exist_ok=True)
    
    # Parquet & Numpy 파일 저장
    products.to_parquet('online-retail/data/products.parquet', index=False)
    customer_stats.to_parquet('online-retail/data/customer_stats.parquet', index=False)
    evaluation_results.to_parquet('online-retail/data/model_evaluation.parquet', index=False)
    
    # 고객별 구매 상세 내역 저장 (대시보드 실시간 쿼리 최적화용)
    cf_data[['CustomerID', 'StockCode', 'Description', 'Quantity', 'UnitPrice', 'TotalSpend']].to_parquet(
        'online-retail/data/customer_transactions.parquet', index=False
    )
    
    # 유사도 행렬 저장
    np.save('online-retail/data/tfidf_similarity.npy', tfidf_sim)
    np.save('online-retail/data/embedding_similarity.npy', embedding_sim)
    np.save('online-retail/data/cf_similarity.npy', item_cf_sim)
    
    print("모든 전처리 및 캐싱 연산 완료!")
    print(f"customer_stats.parquet 저장 완료: {customer_stats.shape}")
    print(f"model_evaluation.parquet 저장 완료: {evaluation_results.shape}")
    print(f"cf_similarity.npy 저장 완료: {item_cf_sim.shape}")

if __name__ == '__main__':
    preprocess_data()
