import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, send_file, jsonify

# Flask 앱 생성
app = Flask(__name__)

# 데이터 분석 및 그래프 생성 API
@app.route('/plot', methods=['GET'])
def generate_plot():
    # 데이터 불러오기
    df = pd.read_csv("store(통합).csv", encoding="utf-8", header=0)

    # 조건에 맞는 데이터 필터링
    filtered_df = df[(df['latitude'] >= 37.6) & (df['latitude'] <= 37.7) & 
                     (df['longitude'] >= 126.8) & (df['longitude'] < 126.9)]

    # favorite_count 기준으로 내림차순 정렬
    sorted_data = filtered_df.sort_values(by='favorite_count', ascending=False)[['name', 'favorite_count']]

    # 그래프 생성
    plt.figure(figsize=(10, 6))
    plt.rc('font', family='AppleGothic')  # mac
    plt.rc('font', size=12)
    plt.rc('axes', unicode_minus=False)
    plt.barh(sorted_data['name'], sorted_data['favorite_count'], color='skyblue')
    plt.xlabel('Favorite Count')
    plt.ylabel('Cafe Name')
    plt.title('Cafe Popularity by Favorite Count')
    plt.gca().invert_yaxis()  # 이름 순서대로 내림차순 표시

    # 그래프를 이미지 파일로 저장
    image_path = 'cafe_popularity.png'
    plt.savefig(image_path, bbox_inches='tight')
    plt.close()

    # 이미지 파일을 클라이언트에 반환
    return send_file(image_path, mimetype='image/png')

# 가게 이름 리스트 API
@app.route('/store-names', methods=['GET'])
def get_store_names():
    df = pd.read_csv("store(통합).csv", encoding="utf-8", header=0)
    filtered_df = df[(df['latitude'] >= 37.6) & (df['latitude'] <= 37.7) & 
                     (df['longitude'] >= 126.8) & (df['longitude'] < 126.9)]
    store_names = filtered_df['name'].tolist()
    return jsonify(store_names)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
