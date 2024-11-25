import os
import pandas as pd
import matplotlib.pyplot as plt
import requests

# API에서 경기도 즐겨찾기 데이터 가져오기
API_URL = "http://127.0.0.1:5001/api/gyeonggi-favorites"

response = requests.get(API_URL)
if response.status_code == 200:
    data = response.json()
else:
    print("데이터를 가져오는 데 실패했습니다.")
    data = []

# API 데이터프레임 생성
df_api = pd.DataFrame(data)

# CSV 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
store_favorite_path = os.path.join(BASE_DIR, 'store_favorite.csv')  # 경로 수정
store_info_path = os.path.join(BASE_DIR, 'store(통합).csv')

# 사용자 정보 읽기
user_data_path = os.path.join(BASE_DIR, 'survey.csv')
user_data = pd.read_csv(user_data_path)
store_favorite = pd.read_csv(store_favorite_path)

# 즐겨찾기한 사용자 정보 병합 (성별 추가)
user_gender_data = pd.merge(
    store_favorite, user_data[['user_id', 'gender']], on='user_id', how='inner'
)

# 병합 결과 확인 (성별 정보가 제대로 붙었는지 확인)
print("병합된 사용자 성별 정보:")
print(user_gender_data.head())

# 각 store_id별로 성별 합계 계산
gender_distribution = user_gender_data.groupby(['store_id', 'gender']).size().unstack(fill_value=0)

# 성별 컬럼을 '남성'과 '여성'으로 정리
gender_distribution = gender_distribution.rename(columns={"남": "남", "여": "여"})
gender_distribution = gender_distribution.reindex(columns=['남', '여'], fill_value=0)

# 각 카페의 성별 정보가 잘 반영되었는지 확인
print("성별 분포 (gender_distribution):")
print(gender_distribution)

# store_info에서 store_id와 name을 병합
store_info = pd.read_csv(store_info_path)

# 'name' 컬럼 공백 및 대소문자 정리
store_info['name'] = store_info['name'].str.strip().str.lower()
df_api['name'] = df_api['name'].str.strip().str.lower()

# 'store_id'와 'name'을 기준으로 병합하여 df_api에 'store_id' 추가
df_api = pd.merge(df_api, store_info[['id', 'name']], left_on='name', right_on='name', how='left')

# 성비 데이터와 API 데이터 병합
gender_distribution = pd.merge(
    gender_distribution, df_api[['name', 'favorite_count', 'id']], left_index=True, right_on='id', how='inner'
)

# 'favorite_count'를 숫자형으로 변환
gender_distribution['favorite_count'] = pd.to_numeric(gender_distribution['favorite_count'], errors='coerce')

# 결측치 확인 및 처리
print("결측치 확인:")
print(gender_distribution.isna().sum())

# 결측값 제거
gender_distribution = gender_distribution.dropna()

# 인덱스를 카페 이름으로 설정
gender_distribution.set_index('name', inplace=True)

# 확인 출력
print(gender_distribution.head())

# 남성, 여성 데이터가 모두 있는지 확인 후 그래프 생성
if not gender_distribution.empty:  # 데이터가 비어 있지 않으면 그래프를 그립니다.
    # 성별이 0인 카페는 제외
    gender_distribution = gender_distribution[(gender_distribution['남'] > 0) | (gender_distribution['여'] > 0)]

    # 남성, 여성 데이터가 모두 없는 경우 예외 처리
    if not gender_distribution.empty:  # 남성 또는 여성 데이터가 하나라도 있는 경우
        plt.figure(figsize=(12, 8))
        plt.rc('font', family='AppleGothic')  # 폰트 설정 (AppleSDGothicNeo 사용)

        # 남성, 여성 성비에 따른 즐겨찾기 수를 stacked bar 그래프로 생성
        gender_distribution[['남', '여']].plot(
            kind='bar', stacked=True, color=['skyblue', 'pink'], ax=plt.gca()
        )

        # 그래프 스타일 설정
        plt.title('주변 즐겨찾기 카페 성별 분포', fontsize=18)
        plt.xlabel('카페 이름', fontsize=14)
        plt.ylabel('즐겨찾기 수 (명)', fontsize=14)
        plt.xticks(rotation=45, fontsize=12)
        plt.legend(title='성별', labels=['남성', '여성'], fontsize=12)

        # y축의 값 범위 설정
        max_favorite_count = gender_distribution['favorite_count'].max()
        plt.yticks(range(0, max_favorite_count + 1, max(1, max_favorite_count // 10)))  # y축 범위를 조정

        # 그리드 설정
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # 그래프 화면에 표시
        plt.tight_layout()
        plt.show(block=True)  # block=True로 설정하여 차단 모드에서 실행
    else:
        print("성별 데이터가 없는 카페가 있어 그래프를 그릴 수 없습니다.")
else:
    print("병합된 데이터가 비어 있습니다. 확인이 필요합니다.")
