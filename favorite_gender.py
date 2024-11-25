import os
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import requests
from flask import Flask, jsonify, send_from_directory, Response
from flask_cors import CORS
from flasgger import Swagger
import json

# Flask 앱 설정
app = Flask(__name__)
Swagger(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

matplotlib.use('Agg')

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

store_favorite_path = os.path.join(BASE_DIR, 'store_favorite.csv')
store_info_path = os.path.join(BASE_DIR, 'store(통합).csv')
user_data_path = os.path.join(BASE_DIR, 'survey.csv')

# pandas 경고 무시 설정
pd.options.mode.chained_assignment = None


def preprocess_data(api_url, user_data_path, store_favorite_path, store_info_path):
    """
    데이터를 API 및 파일에서 병합하고 정리
    """
    try:
        # API 데이터 가져오기
        response = requests.get(api_url)
        if response.status_code == 200:
            api_data = pd.DataFrame(response.json())
        else:
            raise ValueError("API에서 데이터를 가져오지 못했습니다.")

        # 데이터 파일 읽기
        user_data = pd.read_csv(user_data_path)
        store_favorite = pd.read_csv(store_favorite_path)
        store_info = pd.read_csv(store_info_path)

        # 카페 이름 데이터 정리
        store_info['name'] = store_info['name'].str.strip().str.lower()
        api_data['name'] = api_data['name'].str.strip().str.lower()

        # 병합
        merged_api_data = pd.merge(api_data, store_info[['id', 'name']], on='name', how='left')
        return user_data, store_favorite, merged_api_data
    except Exception as e:
        print(f"데이터 처리 오류: {e}")
        return None, None, None


def generate_gender_distribution_image(output_path):
    """
    성별 분포 그래프를 생성하고 이미지를 저장
    """
    try:
        api_url = "http://127.0.0.1:5001/api/gyeonggi-favorites"
        user_data, store_favorite, api_data = preprocess_data(
            api_url, user_data_path, store_favorite_path, store_info_path
        )

        if user_data is None or store_favorite is None or api_data is None:
            raise ValueError("데이터 병합 중 오류 발생.")

        # 성별 데이터 병합 및 정리
        user_gender_data = pd.merge(
            store_favorite, user_data[['user_id', 'gender']], on='user_id', how='inner'
        )
        gender_distribution = user_gender_data.groupby(['store_id', 'gender']).size().unstack(fill_value=0)

        # 병합 결과 정리
        gender_distribution = pd.merge(
            gender_distribution, api_data[['name', 'favorite_count', 'id']], left_index=True, right_on='id', how='inner'
        )
        gender_distribution.set_index('name', inplace=True)

        # 그래프 생성
        if not gender_distribution.empty:
            plt.figure(figsize=(12, 8))
            plt.rc('font', family='AppleGothic')
            gender_distribution[['남', '여']].plot(kind='bar', stacked=True, color=['skyblue', 'pink'])
            plt.title('주변 즐겨찾기 카페 성별 분포', fontsize=18)
            plt.xlabel('카페 이름', fontsize=14)
            plt.ylabel('즐겨찾기 수 (명)', fontsize=14)
            plt.xticks(rotation=55, fontsize=10)
            plt.legend(title='성별', labels=['남성', '여성'], fontsize=12)
            plt.tight_layout()
            plt.savefig(output_path)
            plt.close()
            return True
        else:
            print("성별 데이터가 부족합니다.")
            return False
    except Exception as e:
        print(f"성별 분포 그래프 생성 오류: {e}")
        return False


def generate_age_distribution_image(output_path):
    """
    연령대 분포 그래프를 생성하고 이미지를 저장
    """
    try:
        # API 데이터 가져오기
        API_URL = "http://127.0.0.1:5001/api/gyeonggi-favorites"
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
        else:
            print("데이터를 가져오는 데 실패했습니다.")
            data = []

        df_api = pd.DataFrame(data)

        # 데이터 파일 읽기
        user_data = pd.read_csv(user_data_path)
        store_favorite = pd.read_csv(store_favorite_path)
        store_info = pd.read_csv(store_info_path)

        # 데이터 병합 및 정제
        user_age_data = pd.merge(
            store_favorite, user_data[['user_id', 'age']], on='user_id', how='inner'
        )

        bins = [0, 19, 29, 39, 49, 59, 120]
        labels = ['20대 미만', '20대', '30대', '40대', '50대', '60대 이상']
        user_age_data['age_group'] = pd.cut(user_age_data['age'], bins=bins, labels=labels, right=False)

        # 연령대별 카페별 방문자 수 집계
        user_age_data['age_group'] = user_age_data['age_group'].astype(str)  # 문자열로 변환
        age_distribution = user_age_data.groupby(['store_id', 'age_group']).size().unstack(fill_value=0)

        # API 데이터와 Store 정보 병합
        store_info['name'] = store_info['name'].str.strip().str.lower()
        df_api['name'] = df_api['name'].str.strip().str.lower()
        df_api = pd.merge(df_api, store_info[['id', 'name']], left_on='name', right_on='name', how='left')

        # 병합 결과 정리
        age_distribution = pd.merge(
            age_distribution, df_api[['name', 'favorite_count', 'id']], left_index=True, right_on='id', how='inner'
        )

        # 데이터 정리
        age_distribution['favorite_count'] = pd.to_numeric(age_distribution['favorite_count'], errors='coerce')
        age_distribution = age_distribution.dropna()
        age_distribution.set_index('name', inplace=True)

        if not age_distribution.empty:

            age_colors = ['#f09e90', '#edd75f', '#67c967', '#5c95cc', '#faa7d4', '#c4a6e0']

            # 그래프 생성
            plt.figure(figsize=(12, 8))
            plt.rc('font', family='AppleGothic')

            age_distribution[labels].plot(
                kind='bar', stacked=True, color=age_colors, ax=plt.gca()
            )
            plt.title('주변 즐겨찾기 카페 연령대 분포', fontsize=18)
            plt.xlabel('카페 이름', fontsize=14)
            plt.ylabel('즐겨찾기 수 (명)', fontsize=14)
            plt.xticks(rotation=45, fontsize=12)
            plt.legend(title='연령대', fontsize=12)
            plt.tight_layout()

            # 이미지 저장
            plt.savefig(output_path)
            plt.close()
            return True
        else:
            print("연령대 데이터가 없는 카페가 있어 그래프를 그릴 수 없습니다.")
            return False
    except Exception as e:
        print(f"오류 발생: {e}")
        return False



@app.route('/api/gender-distribution-image', methods=['GET'])
def get_gender_distribution_image():
    output_path = os.path.join(STATIC_FOLDER, 'gender_distribution.png')
    success = generate_gender_distribution_image(output_path)
    if success:
        return jsonify({"imageUrl": f"http://127.0.0.1:5002/static/gender_distribution.png"})
    return Response(
        json.dumps({"error": "성별 분포 이미지를 생성하지 못했습니다."}, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=500,
    )


@app.route('/api/age-distribution-image', methods=['GET'])
def get_age_distribution_image():
    output_path = os.path.join(STATIC_FOLDER, 'age_distribution.png')
    success = generate_age_distribution_image(output_path)
    if success:
        return jsonify({"imageUrl": f"http://127.0.0.1:5002/static/age_distribution.png"})
    return Response(
        json.dumps({"error": "연령대 분포 이미지를 생성하지 못했습니다."}, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=500,
    )


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
