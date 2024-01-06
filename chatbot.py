from flask import Flask, request, jsonify
from wtforms import TextAreaField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = "my super secret key"  # CSRF 설정

# 코랩 연결 코드
COLAB_URL = "https://06d8-34-125-85-124.ngrok-free.app"  # 코랩(URL 넣기)
COLAB_API_URL_NLP = COLAB_URL + "/predict"
COLAB_API_URL_OKT = COLAB_URL + "/okt_tokenize"

# DB 접근
DATABASE_URI = "mysql+pymysql://root:1234@localhost/news"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)

# Table 생성
class Newstbl(db.Model):
    __tablename__ = 'newstbl'
    idx = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    label = db.Column(db.Integer, nullable=False)

# 폼 클래스
class NewsForm(FlaskForm):
    url = TextAreaField("네이버 뉴스 URL 입력", validators=[InputRequired()])
    submit = SubmitField("Submit")

# 코랩 내 형태소 분석기로 데이터 넘기기
def make_okt_token(title_data):
    data = {'제목': title_data}
    response = requests.post(COLAB_API_URL_OKT, json=data)
    result = response.json()
    return result['tokenized_title']

# 코랩 내 모델 예측
def make_nlp_predict(tokenized_title_data):
    data = {'토큰화_제목': tokenized_title_data}
    response = requests.post(COLAB_API_URL_NLP, json=data)
    result = response.json()
    return result['label'], result['percent']

# 카카오톡 서버로부터 요청을 받는 라우트 추가
@app.route("/kakao_request", methods=["POST"])
def kakao_request():
    data = request.get_json()
    news_title = data["action"]["detailParams"]['sys.text'][value]  # 카카오톡 메시지에서 뉴스 제목 추출

    tokenized_title_data = make_okt_token(news_title)
    predicted_label, predicted_percent = make_nlp_predict(tokenized_title_data)
    predicted_percent = round(predicted_percent * 100, 2)  # 백분율로 변환

    # 라벨에 따라 '진실' 또는 '거짓'으로 표시
    label_text = '진실' if predicted_label == 1 else '거짓'
    response_text = f"본 문장은 {predicted_percent}%의 확률로 {label_text}입니다."

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": response_text
                    }
                }
            ]
        }
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, threaded=True)