import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rc('font', family = 'AppleGothic') # mac 
plt.rc('font', size = 12)
plt.rc('axes', unicode_minus = False)

data = pd.read_csv("사용자수.csv", encoding="utf-8", header = 0)
print(data.columns)

age_data = pd.read_csv("더미데이터_즐겨찾기.csv", encoding = "utf-8", header = 0)
print(age_data.columns)


plt.figure(figsize=(10, 5))
plt.bar(data['시간대'], data['방문자수'], color='#2E8465')
# 그래프 제목과 레이블 설정
plt.title('시간대별 방문자 수')
plt.xlabel('시간대')
plt.ylabel('방문자 수')

# 그래프 보이기
plt.xticks(rotation=45)  # x축 레이블 각도 조정
# plt.grid(axis='y')  # y축에 그리드 추가
plt.tight_layout()  # 레이아웃 조정
plt.show()

### 즐겨찾기 연령대

# 연령대 구간 정의
bins = [0, 19, 29, 39, 49, 100]
labels = ['10대 이하', '20대', '30대', '40대', '50대 이상']

# '나이'를 연령대로 변환하여 새로운 열 추가
age_data['연령대'] = pd.cut(age_data['나이'], bins=bins, labels=labels, right=True)

# 카페 종류별로 연령대 그룹화하여 개수 세기
grouped_data = age_data.groupby(['즐겨찾기 카페', '연령대']).size().unstack()

# 막대 그래프 그리기
ax = grouped_data.plot(kind='bar', figsize=(12, 6), color=['#2E8465','#F1C232','#1F6A51','#F28B82', '#AFDCEC'])

# 그래프 제목과 레이블 설정
plt.title('카페 종류별 연령대 분포')
plt.xlabel('카페 종류')
plt.ylabel('인원수')

# 범례 표시
plt.legend(title='연령대', bbox_to_anchor=(1.05, 1), loc='upper left')

# 레이아웃 조정 및 그래프 표시
plt.tight_layout()
# 그래프 보이기
plt.xticks(rotation=45)  # x축 레이블 각도 조정
# plt.grid(axis='y')  # y축에 그리드 추가
plt.show()


### 성비 비율

# 특정 카페 필터링 (예시: '카페A')
cafe_name = '스타벅스 동교점'
filtered_data = age_data[age_data['즐겨찾기 카페'] == cafe_name]

# 성별 비율 계산
gender_counts = filtered_data['성별'].value_counts()

# 파이 차트 그리기
plt.figure(figsize=(6, 6))
plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', startangle=90, colors=['#AFDCEC', '#F28B82'], explode=[0.05, 0])

# 그래프 제목 설정
plt.title(f'{cafe_name} 성비 비율')

# 원형 차트 모양을 원형으로 유지
plt.axis('equal')

# 그래프 표시
plt.show()

### 특정 카페 연령 분석
age_group_counts = age_data['연령대'].value_counts().sort_index()

x_pos = np.arange(len(age_group_counts))  # x축 위치
bar_width = 0.4  # 막대 너비를 줄이면 간격이 늘어남

# 막대 그래프 그리기
plt.subplot(1, 3, 2)  # 1행 2열에서 두 번째 그래프
plt.bar(age_group_counts.index, age_group_counts.values, width=bar_width, color='#2E8465')
plt.title(f'{cafe_name} 방문자 연령대 분포')
plt.xlabel('연령대')
plt.ylabel('방문자 수')
plt.xticks(x_pos, age_group_counts.index, rotation = 70)

# 레이아웃 조정 및 그래프 표시
plt.tight_layout()
plt.show()