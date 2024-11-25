import os
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
import json
from requests.models import Response
from flask_cors import CORS
from flask import make_response
from flasgger import Swagger
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
Swagger(app)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# CSV 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
store_favorite_path = os.path.join(BASE_DIR, 'store_favorite.csv')
store_info_path = os.path.join(BASE_DIR, 'store(통합).csv')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

# Static 폴더가 없으면 생성
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)


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

    # 폰트 설정
    try:
        font_path = "/Library/Fonts/AppleSDGothicNeo.ttc"  # MacOS 시스템 폰트
        font = ImageFont.truetype(font_path, 20)
    except IOError:
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
        image_url = f"http://127.0.0.1:5001/static/gyeonggi_favorites.png"
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


# static 디렉토리의 파일을 클라이언트가 접근할 수 있게 설정
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
