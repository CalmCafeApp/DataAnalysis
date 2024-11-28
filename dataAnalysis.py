import os
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory, send_file
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
import requests
import json
from requests.models import Response
from flask_cors import CORS
from flask import make_response
from flasgger import Swagger
from PIL import Image, ImageDraw, ImageFont
import platform

app = Flask(__name__)
Swagger(app)


CORS(app, resources={r"/api/*": {"origins": "*"}})

# BASE_URL 설정: 환경 변수에서 가져오거나, 테스트 기본값("http://3.36.174.88:5001") 사용
BASE_URL = os.getenv("BASE_URL", "http://3.36.174.88:5001").rstrip("/")

matplotlib.use('Agg')

# CSV 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, '291.csv')
store_favorite_path = os.path.join(BASE_DIR, 'store_favorite.csv')
store_info_path = os.path.join(BASE_DIR, 'store(통합).csv')
user_data_path = os.path.join(BASE_DIR, 'survey.csv')

STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
# Static 폴더가 없으면 생성
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

# pandas 경고 무시 설정
pd.options.mode.chained_assignment = None

def create_image_with_text(data, output_path):
    """
    데이터 리스트를 이미지에 텍스트로 렌더링
    """
    width, height = 800, 600
    background_color = (255, 255, 255)
    text_color = (0, 0, 0)

    # 이미지와 드로잉 객체 생성
    img = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

   # 폰트 경로 설정
    try:
        if platform.system() == 'Darwin':  # macOS
            font_path = "/Library/Fonts/AppleSDGothicNeo.ttc"
        elif platform.system() == 'Windows':  # Windows
            font_path = "C:\\Windows\\Fonts\\malgun.ttf"
        else:  # Linux
            font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # Linux에서 사용하는 한글 폰트

        # 폰트 로드
        font = ImageFont.truetype(font_path, 20)
    except IOError:
        # 폰트 로드 실패 시 기본 폰트 사용
        font = ImageFont.load_default()

    # 텍스트 내용 작성
    x, y = 50, 50
    for rank, item in enumerate(data, start=1):
        text = f"{rank}. {item['name']} - {item['favorite_count']}"
        draw.text((x, y), text, fill=text_color, font=font)
        y += 30

    # 이미지 저장
    img.save(output_path)


@app.route('/api/gyeonggi-favorites-image', methods=['GET'])
def get_gyeonggi_favorites_image():
    """
    API to generate an image of cafe rankings in Gyeonggi-do.
    """
    try:
        # CSV 데이터 읽기
        store_favorite = pd.read_csv(store_favorite_path)
        store_info = pd.read_csv(store_info_path)

        # 데이터 병합
        merged_data = pd.merge(
            store_favorite, store_info, left_on='store_id', right_on='id', how='inner'
        )

        # 경기도 지역 필터링
        gyeonggi_data = merged_data[merged_data['address'].str.contains('경기도', case=False, na=False)]

        # 즐겨찾기 수 집계
        gyeonggi_favorites_with_name = (
            gyeonggi_data.groupby(['store_id', 'name'])
            .size()
            .reset_index(name='favorite_count')
            .sort_values(by='favorite_count', ascending=False)
        )

        results = gyeonggi_favorites_with_name[['name', 'favorite_count']].to_dict(
            orient='records'
        )

        # 이미지 생성
        output_path = os.path.join(STATIC_FOLDER, 'gyeonggi_favorites.png')
        create_image_with_text(results, output_path)

        # 이미지 URL 반환
        image_url = f"{BASE_URL}/static/gyeonggi_favorites.png"
        return jsonify({"imageUrl": image_url})

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=500,
        )


@app.route('/api/gyeonggi-favorites', methods=['GET'])
def get_gyeonggi_favorites():
    """
    API to return cafe rankings in Gyeonggi-do as JSON data.
    """
    try:
        # CSV 데이터 읽기
        store_favorite = pd.read_csv(store_favorite_path)
        store_info = pd.read_csv(store_info_path)

        # 데이터 병합
        merged_data = pd.merge(
            store_favorite, store_info, left_on='store_id', right_on='id', how='inner'
        )

        # 경기도 지역 필터링
        gyeonggi_data = merged_data[merged_data['address'].str.contains('경기도', case=False, na=False)]

        # 즐겨찾기 수 집계
        gyeonggi_favorites_with_name = (
            gyeonggi_data.groupby(['store_id', 'name'])
            .size()
            .reset_index(name='favorite_count')
            .sort_values(by='favorite_count', ascending=False)
        )

        results = gyeonggi_favorites_with_name[['name', 'favorite_count']].to_dict(
            orient='records'
        )

        response = make_response(jsonify(results))
        response.headers['Cache-Control'] = 'no-store'  # 캐시 비활성화
        return response

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=500,
        )

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
        api_url = f"{BASE_URL}/api/gyeonggi-favorites"
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
            gender_distribution[['남', '여']].plot(kind='bar', stacked=True, color=['skyblue', 'pink'])
            plt.title('Gender Distribution in Nearby Favorite Cafes', fontsize=18)
            plt.xlabel('Cafe Name', fontsize=14)
            plt.ylabel('Number of Favorites (People)', fontsize=14)
            plt.xticks(rotation=55, fontsize=10)
            plt.legend(title='Gender', labels=['Male', 'Female'], fontsize=12)
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
        API_URL = f"{BASE_URL}/api/gyeonggi-favorites"
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
        labels = ['Under 20s', '20s', '30s', '40s', '50s', '60s and Above']
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

            age_distribution[labels].plot(
                kind='bar', stacked=True, color=age_colors, ax=plt.gca()
            )
            plt.title('Age Distribution in Nearby Favorite Cafes', fontsize=18)
            plt.xlabel('Cafe Name', fontsize=14)
            plt.ylabel('Number of Favorites (People)', fontsize=14)
            plt.xticks(rotation=45, fontsize=12)
            plt.legend(title='Age Group', fontsize=12)
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




# 요일 순서 지정 및 한글 매핑
weekday_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
weekday_korean = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def generate_busiest_and_least_busy_times():
    """
    요일별 가장 붐비는 시간대, 가장 한가한 시간대, 평균 혼잡도 시각화
    """
    # 데이터 불러오기
    data = pd.read_csv(file_path)
    data['weekday'] = pd.Categorical(data['weekday'], categories=weekday_order, ordered=True)
    data['weekday_korean'] = data['weekday'].map(dict(zip(weekday_order, weekday_korean)))

    # 요일별로 가장 붐비는 시간 찾기
    busiest_times = data.loc[data.groupby('weekday')['predicted_people'].idxmax()]
    busiest_times['weekday_korean'] = busiest_times['weekday'].map(dict(zip(weekday_order, weekday_korean)))

    # 요일별로 가장 한가한 시간 찾기
    least_busy_times = data.loc[data.groupby('weekday')['predicted_people'].idxmin()]
    least_busy_times['weekday_korean'] = least_busy_times['weekday'].map(dict(zip(weekday_order, weekday_korean)))

    # 요일별 평균 혼잡도 계산
    average_congestion = data.groupby('weekday')['predicted_people'].mean().reset_index()
    average_congestion['weekday_korean'] = average_congestion['weekday'].map(dict(zip(weekday_order, weekday_korean)))

    # 그래프 1: 가장 붐비는 시간대와 가장 한가한 시간대
    plt.figure(figsize=(10, 6))

    # 가장 붐비는 시간대
    plt.bar(busiest_times['weekday_korean'], busiest_times['predicted_people'], color='lightcoral', label='Busiest Time')
    for i, row in busiest_times.iterrows():
        plt.text(
            row['weekday_korean'], 
            row['predicted_people'] + 0.5,  # 텍스트를 막대 위로 배치
            f"{int(row['hour'])}o'clock", 
            ha='center', 
            va='bottom', 
            fontsize=10
        )

    # 가장 한가한 시간대
    plt.bar(least_busy_times['weekday_korean'], least_busy_times['predicted_people'], color='skyblue', label='Calmest Time')
    for i, row in least_busy_times.iterrows():
        plt.text(
            row['weekday_korean'], 
            row['predicted_people'] + 0.2,  # 텍스트를 막대 위로 배치
            f"{int(row['hour'])}o'clock", 
            ha='center', 
            va='bottom', 
            fontsize=10, 
            color='black',
            bbox=dict(facecolor='none', edgecolor='none', alpha=0.7)  # 텍스트 배경 추가
        )
    plt.title('Busiest and Calmest Time Periods by Day of the Week', fontsize=16)
    plt.xlabel('Week', fontsize=10)
    plt.ylabel('Congestion', fontsize=12)
    plt.ylim(0, data['predicted_people'].max() + 2) 
    plt.legend()
    plt.tight_layout()

    busiest_and_least_busy_path = os.path.join(STATIC_FOLDER, 'busiest_and_least_busy.png')
    plt.savefig(busiest_and_least_busy_path)
    plt.close()

    # 그래프 2: 평균 혼잡도
    plt.figure(figsize=(10, 6))
    plt.bar(average_congestion['weekday_korean'], average_congestion['predicted_people'], color='#2E8465', label='평균 혼잡도')
    plt.title('Average Congestion by Day of the Week', fontsize=16)
    plt.xlabel('Week', fontsize=10)
    plt.ylabel('Congestion', fontsize=12)
    plt.ylim(0, data['predicted_people'].max() + 2) 
    plt.legend()
    plt.tight_layout()

    average_congestion_path = os.path.join(STATIC_FOLDER, 'average_congestion.png')
    plt.savefig(average_congestion_path)
    plt.close()

    return busiest_and_least_busy_path, average_congestion_path


def visualize_favorites_by_store():
    """
    특정 카페를 좋아요한 사용자의 성별, 연령대, 선호 메뉴를 시각화합니다.
    """
    try:
        # 데이터 로드
        store_info = pd.read_csv(store_info_path)
        favorite_data = pd.read_csv(store_favorite_path)
        survey_data = pd.read_csv(user_data_path)
        
        # 혼잡도 파일의 카페 id를 읽음
        target_id = int(os.path.basename(file_path).split('.')[0])  # 예: '291.csv' -> 291
        
        # store(통합).csv에서 해당 카페 정보 찾기
        target_store = store_info[store_info['id'] == target_id]
        if target_store.empty:
            raise ValueError("해당 ID의 카페가 store(통합).csv에 존재하지 않습니다.")
        
        # 좋아요 누른 사용자 id 찾기
        liked_users = favorite_data[favorite_data['store_id'] == target_id]
        if liked_users.empty:
            raise ValueError("해당 카페를 좋아요한 사용자가 없습니다.")
        
        # 설문조사 데이터와 매칭
        liked_user_ids = liked_users['user_id'].unique()
        matched_survey_data = survey_data[survey_data['user_id'].isin(liked_user_ids)]
        if matched_survey_data.empty:
            raise ValueError("해당 사용자의 설문조사 데이터가 없습니다.")
        
        # 성별 분포
        gender_counts = matched_survey_data['gender'].value_counts()
        gender_counts.plot(kind='bar', color=['lightpink', 'skyblue'], rot=0, title='Gender Distribution')
        plt.ylabel('Number of People')
        gender_path = os.path.join(STATIC_FOLDER, 'gender_distribution_target_store.png')
        plt.savefig(gender_path)
        plt.close()
        
        # 연령대별 분포
        age_bins = [0, 19, 29, 39, 49, 59, 120]
        age_labels = ['Under 20s', '20s', '30s', '40s', '50s', '60s and Above']
        matched_survey_data['age_group'] = pd.cut(matched_survey_data['age'], bins=age_bins, labels=age_labels, right=False)
        age_counts = matched_survey_data['age_group'].value_counts().sort_index()
        age_counts.plot(kind='bar', color='#e38a6d', rot=0, title='Age Distribution')
        plt.rc('font', family='AppleGothic')
        plt.ylabel('Number of People')
        age_path = os.path.join(STATIC_FOLDER, 'age_distribution_target_store.png')
        plt.savefig(age_path)
        plt.close()
        
        # 선호 메뉴 분포
        favorite_menu_counts = matched_survey_data['favorite_menu'].value_counts()
        favorite_menu_counts.plot(kind='bar', color='#8a6857', rot=45, title='Favorite Menu Distribution')
        plt.ylabel('Preference')
        menu_path = os.path.join(STATIC_FOLDER, 'favorite_menu_distribution_target_store.png')
        plt.savefig(menu_path, bbox_inches='tight')
        plt.close()
        
        return gender_path, age_path, menu_path
    
    except Exception as e:
        raise RuntimeError(f"데이터 시각화 중 오류 발생: {e}")


@app.route('/api/get-calmcafe-data-image', methods=['GET'])
def get_target_store_visualization():
    try:
        # 타겟 카페의 성별, 연령대, 선호 메뉴 시각화 이미지 생성
        gender_path, age_path, menu_path = visualize_favorites_by_store()
        
        # 요일별 가장 붐비는 시간대와 평균 혼잡도 이미지 생성
        busiest_and_least_busy_path, average_congestion_path = generate_busiest_and_least_busy_times()

        # 성별 분포 이미지 생성
        gender_distribution_path = os.path.join(STATIC_FOLDER, 'gender_distribution.png')
        success_gender = generate_gender_distribution_image(gender_distribution_path)
        
        # 연령대 분포 이미지 생성
        age_distribution_path = os.path.join(STATIC_FOLDER, 'age_distribution.png')
        success_age = generate_age_distribution_image(age_distribution_path)

        if not (success_gender and success_age):
            raise ValueError("성별 또는 연령대 분포 이미지를 생성하는 데 실패했습니다.")

        # 모든 이미지 URL 반환
        return jsonify({
            "genderImageUrl": f"{BASE_URL}/static/gender_distribution_target_store.png",
            "ageImageUrl": f"{BASE_URL}/static/age_distribution_target_store.png",
            "menuImageUrl": f"{BASE_URL}/static/favorite_menu_distribution_target_store.png",
            "busiestAndLeastBusyImageUrl": f"{BASE_URL}/static/busiest_and_least_busy.png",
            "averageCongestionImageUrl": f"{BASE_URL}/static/average_congestion.png",
            "genderDistributionImageUrl": f"{BASE_URL}/static/gender_distribution.png?cache_buster=12345",
            "ageDistributionImageUrl": f"{BASE_URL}/static/age_distribution.png"
        })

    except Exception as e:
        return Response(
            json.dumps({"error": f"시각화 오류: {str(e)}"}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=500,
        )



# static 디렉토리의 파일을 클라이언트가 접근할 수 있게 설정
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/static/<filename>')
def serve_image(filename):
    return send_file(f'./static/{filename}', mimetype='image/png')

@app.route('/favicon.ico')
def favicon():
    return '', 404  # 빈 응답을 반환하여 404 오류 처리


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
