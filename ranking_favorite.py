import os
import matplotlib
matplotlib.use('Agg')  # 비-GUI 백엔드 설정

import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from io import BytesIO

# Flask 앱 생성
app = Flask(__name__)
Swagger(app)
CORS(app, resources={r"/plot": {"origins": "*"}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, 'store_favorite.csv')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

# Static 폴더가 없으면 생성
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

@app.route('/plot', methods=['POST'])
def generate_plot():
    """
    API for generating a popularity plot of cafes based on favorite count.
    
    ---
    responses:
      200:
        description: Cafe popularity plot image URL
        content:
          application/json:
            schema:
              type: object
              properties:
                plotUrl:
                  type: string
                  description: URL to access the plot image
    """
    try:
        # POST 요청의 JSON 데이터 처리
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input"}), 400
        
        latitude_range = data.get('latitude_range', [37.6, 37.7])
        longitude_range = data.get('longitude_range', [126.8, 126.9])

        # CSV 파일 읽기
        df = pd.read_csv(csv_path, encoding="utf-8", header=0)
        filtered_df = df[(df['latitude'] >= latitude_range[0]) & (df['latitude'] <= latitude_range[1]) &
                         (df['longitude'] >= longitude_range[0]) & (df['longitude'] < longitude_range[1])]
        sorted_data = filtered_df.sort_values(by='favorite_count', ascending=False)[['name', 'favorite_count']]

        # 그래프 생성
        plt.figure(figsize=(10, 6))
        plt.rc('font', family='AppleGothic')
        plt.rc('font', size=12)
        plt.rc('axes', unicode_minus=False)
        plt.barh(sorted_data['name'], sorted_data['favorite_count'], color='green')
        plt.xlabel('Favorite Count')
        plt.ylabel('Cafe Name')
        plt.title('Cafe Popularity by Favorite Count')
        plt.gca().invert_yaxis()

        # 이미지 파일 경로 설정
        plot_filename = 'cafe_popularity.png'
        plot_path = os.path.join(STATIC_FOLDER, plot_filename)

        # 이미지 저장
        plt.savefig(plot_path, bbox_inches='tight')


        # 이미지 URL 반환 (static 폴더에서 접근 가능한 URL로)
        plot_url = f"http://127.0.0.1:5001/static/{plot_filename}"
        return jsonify({"plotUrl": plot_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/store-names', methods=['GET'])
def get_store_names():
    """
    API to retrieve the names of stores filtered by location.

    ---
    responses:
      200:
        description: List of cafe store names
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
    """
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", header=0)
        filtered_df = df[(df['latitude'] >= 37.6) & (df['latitude'] <= 37.7) &
                         (df['longitude'] >= 126.8) & (df['longitude'] < 126.9)]
        store_names = filtered_df['name'].tolist()
        return jsonify(store_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# static 디렉토리의 파일을 클라이언트가 접근할 수 있게 설정
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
