import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, jsonify, send_from_directory, Response
from flask_cors import CORS
from flasgger import Swagger
import json
import matplotlib
import matplotlib.pyplot as plt

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

# 파일 경로 설정
file_path = os.path.join(BASE_DIR, '291.csv')  # 혼잡도 데이터 파일 경로
store_favorite_path = os.path.join(BASE_DIR, 'store_favorite.csv')
store_info_path = os.path.join(BASE_DIR, 'store(통합).csv')
user_data_path = os.path.join(BASE_DIR, 'survey.csv')

# 요일 순서 지정 및 한글 매핑
weekday_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
weekday_korean = ['일', '월', '화', '수', '목', '금', '토']


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
    plt.rc('font', family='AppleGothic')

    # 가장 붐비는 시간대
    plt.bar(busiest_times['weekday_korean'], busiest_times['predicted_people'], color='lightcoral', label='가장 붐비는 시간대')
    for i, row in busiest_times.iterrows():
        plt.text(
            row['weekday_korean'], 
            row['predicted_people'] + 0.5,  # 텍스트를 막대 위로 배치
            f"{int(row['hour'])}시", 
            ha='center', 
            va='bottom', 
            fontsize=10
        )

    # 가장 한가한 시간대
    plt.bar(least_busy_times['weekday_korean'], least_busy_times['predicted_people'], color='skyblue', label='가장 한가한 시간대')
    for i, row in least_busy_times.iterrows():
        plt.text(
            row['weekday_korean'], 
            row['predicted_people'] + 0.2,  # 텍스트를 막대 위로 배치
            f"{int(row['hour'])}시", 
            ha='center', 
            va='bottom', 
            fontsize=10, 
            color='black',
            bbox=dict(facecolor='none', edgecolor='none', alpha=0.7)  # 텍스트 배경 추가
        )
    plt.title('요일별 가장 붐비는 시간대와 한가한 시간대', fontsize=16)
    plt.xlabel('요일', fontsize=10)
    plt.ylabel('혼잡도 (예측 인원 수)', fontsize=12)
    plt.ylim(0, data['predicted_people'].max() + 2) 
    plt.legend()
    plt.tight_layout()

    busiest_and_least_busy_path = os.path.join(STATIC_FOLDER, 'busiest_and_least_busy.png')
    plt.savefig(busiest_and_least_busy_path)
    plt.close()

    # 그래프 2: 평균 혼잡도
    plt.figure(figsize=(10, 6))
    plt.bar(average_congestion['weekday_korean'], average_congestion['predicted_people'], color='#2E8465', label='평균 혼잡도')
    plt.title('요일별 평균 혼잡도', fontsize=16)
    plt.xlabel('요일', fontsize=10)
    plt.ylabel('평균 혼잡도 (예측 인원 수)', fontsize=12)
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
        plt.rc('font', family='AppleGothic')
        gender_counts = matched_survey_data['gender'].value_counts()
        gender_counts.plot(kind='bar', color=['lightpink', 'skyblue'], rot=0, title='성별 분포')
        plt.ylabel('인원 수')
        gender_path = os.path.join(STATIC_FOLDER, 'gender_distribution_target_store.png')
        plt.savefig(gender_path)
        plt.close()
        
        # 연령대별 분포
        age_bins = [0, 19, 29, 39, 49, 59, 120]
        age_labels = ['20대 미만', '20대', '30대', '40대', '50대', '60대 이상']
        matched_survey_data['age_group'] = pd.cut(matched_survey_data['age'], bins=age_bins, labels=age_labels, right=False)
        age_counts = matched_survey_data['age_group'].value_counts().sort_index()
        age_counts.plot(kind='bar', color='#e38a6d', rot=0, title='연령대별 분포')
        plt.rc('font', family='AppleGothic')
        plt.ylabel('인원 수')
        age_path = os.path.join(STATIC_FOLDER, 'age_distribution_target_store.png')
        plt.savefig(age_path)
        plt.close()
        
        # 선호 메뉴 분포
        favorite_menu_counts = matched_survey_data['favorite_menu'].value_counts()
        favorite_menu_counts.plot(kind='bar', color='#8a6857', rot=45, title='선호 메뉴 분포')
        plt.rc('font', family='AppleGothic')
        plt.ylabel('선호도')
        menu_path = os.path.join(STATIC_FOLDER, 'favorite_menu_distribution_target_store.png')
        plt.savefig(menu_path, bbox_inches='tight')
        plt.close()
        
        return gender_path, age_path, menu_path
    
    except Exception as e:
        raise RuntimeError(f"데이터 시각화 중 오류 발생: {e}")


@app.route('/api/congestion-images', methods=['GET'])
def get_congestion_images():
    try:
        busiest_and_least_busy_path, average_congestion_path = generate_busiest_and_least_busy_times()

        return jsonify({
            "busiestAndLeastBusyImageUrl": f"http://127.0.0.1:5003/static/busiest_and_least_busy.png",
            "averageCongestionImageUrl": f"http://127.0.0.1:5003/static/average_congestion.png"
        })
    except Exception as e:
        return Response(
            json.dumps({"error": f"이미지 생성 오류: {str(e)}"}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=500,
        )


@app.route('/api/target-store-visualization', methods=['GET'])
def get_target_store_visualization():
    """
    특정 카페의 좋아요 사용자 데이터를 기반으로 성별, 연령대, 선호 메뉴 시각화 반환
    """
    try:
        gender_path, age_path, menu_path = visualize_favorites_by_store()
        return jsonify({
            "genderImageUrl": f"http://127.0.0.1:5003/static/gender_distribution_target_store.png",
            "ageImageUrl": f"http://127.0.0.1:5003/static/age_distribution_target_store.png",
            "menuImageUrl": f"http://127.0.0.1:5003/static/favorite_menu_distribution_target_store.png"
        })
    except Exception as e:
        return Response(
            json.dumps({"error": f"시각화 오류: {str(e)}"}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=500,
        )


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
