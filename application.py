from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_wtf import FlaskForm
from wtforms import widgets, StringField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import InputRequired, StopValidation
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import get_db as gdb
import news_crawl as nwc
import requests
#import model
#import okt_tok as oktt
#from transformers import ElectraTokenizerFast

app = Flask(__name__)
csrf = CSRFProtect(app)
SECRET_KEY = "my super secret key"    # CSRF 설정

# 코랩 연결 코드
COLAB_URL = "https://48db-34-124-202-167.ngrok-free.app"    # 코랩(실행 시마다 새로운 URL 붙여넣기)
COLAB_API_URL_CON = COLAB_URL+"/connect"
COLAB_API_URL_NLP = COLAB_URL+"/predict"
COLAB_API_URL_OKT = COLAB_URL+"/okt_tokenize"
#COLAB_API_URL_TRN = COLAB_URL+"/train"

#DB 접근
DATABASE_URI="mysql+pymysql://root:1234@localhost/news"

#데이터 베이스 추가
app.config['SQLALCHEMY_DATABASE_URI']=DATABASE_URI

#폼 비밀키 설정
app.config['SECRET_KEY']=SECRET_KEY

#DB 초기화
db=SQLAlchemy(app)

#table 생성
class Newstbl(db.Model):
    __table_name__='newstbl'
    
    idx=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(50), nullable=False)
    label=db.Column(db.Integer, nullable=False)

#폼 클래스
class NewsForm(FlaskForm):
    url=TextAreaField("네이버 뉴스 URL 입력", validators=[InputRequired()])
    submit=SubmitField("Submit")

    
@app.route("/")
def hello():
    # conn_res=ngrok_connnect()    #ngrok 연결 검증
    # if conn_res==1:
    #     print("Colab 연결 완료...")
    # else:
    #     print("Colab 연결 실패...")
    session.clear()    #세션을 비워준다.
    return render_template("index.html")


@app.route("/input_url", methods=["GET", "POST"])
def input_url():
    url=None
    form=NewsForm(request.form) 

    if request.method=="POST" and form.validate():    #폼 입력 검증(세션으로 정보 crawl로 정보 넘김)
        session.pop('user_data', None) 
        session['user_data']=form.url.data
        print(form.url.data)
        return redirect(url_for('crawl'), code=307)
    return render_template("input_url.html", form=form, url=url)
    
    
@app.route("/crawl", methods=["GET", "POST"])
def crawl():
    url_data=session.get('user_data', None)
    print('URL 받음: ', url_data)
    
    title_data, article_data=nwc.news_crawl(url_data)    #뉴스 크롤링(제목, 본문)
    
    threhold_article=1700       #article 축약
    if len(article_data)>threhold_article:
        article_data=article_data[:threhold_article]+'...'
    print(title_data, article_data)      
    
    tokenized_title_data=make_okt_token(title_data)
    predicted_label, predicted_percent=make_nlp_predict(tokenized_title_data)
    predicted_value = "True" if predicted_label == 1.0 else "Fake"
    print(predicted_value, predicted_percent)
    
    #DB에 insert
    # insert_dict={'title':title_data, 'label':predicted_label}
    # news=Newstbl(**insert_dict)
    # db.session.add(news)
    # db.session.commit()
        
    #결과 페이지 이동(URL, 제목, 기사, 예측 라벨, 퍼센트 전달)
    pred_data_dict={'url': url_data, 'title': title_data, 'article': article_data, 'predicted_value':predicted_value, 'predicted_percent': predicted_percent}
    print('*****', pred_data_dict)
    
    if pred_data_dict is not None:
        session['pred_data'] = pred_data_dict
    else:
        session['pred_data'] = pred_data_dict

    return redirect(url_for('result'), code=307)
    
    
@app.route("/result", methods=["GET", "POST"])        #view.py 참고(실제 뿌려주는 부분-> 네이버 팩트 체크)
def result():
    pred_data_dict=session.get('pred_data', None)
    print('result: ', pred_data_dict)
    return render_template("results.html", pred_data_result=pred_data_dict)


@app.route("/creator")
def creator():
    return render_template("creator.html")


@app.route("/add_on")
def add_on():
    return render_template("add_on.html")


@app.route("/kakao_request", methods=["POST"])
@csrf.exempt
def kakao_request():
    data = request.get_json()
    news_title = data["action"]["params"]["user_request"]  # 카카오톡 메시지에서 뉴스 제목 추출

    tokenized_title_data = make_okt_token(news_title)
    predicted_label, predicted_percent = make_nlp_predict(tokenized_title_data)

    # 라벨에 따라 '진실' 또는 '거짓'으로 표시
    label_text = "진실" if predicted_label == 1 else "거짓"
    response_text = f"위 내용은 {predicted_percent}%의 확률로 {label_text}이에요."

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": response_text,
                        "buttons": [
                            {
                                "action": "block",
                                "label": "질문하기",
                                "blockId": "658ce0d173ad18111a17797a"
                            },
                            {
                                "action": "block",
                                "label": "처음으로",
                                "blockId": "658396ed8fc86a2f6b8c7407"
                            }
                        ]
                    }
                }
            ]
        }
    }
    return jsonify(response)

 
    
#코랩 연결 확인
def ngrok_connnect():
    data={'연결': "from_groom_ide"}
    response=requests.post(COLAB_API_URL_CON, json=data)    #JSON 형식(dict)으로 통신
    result=response.json()
    if result['재연결']=='from_colab':
        return 1
    else:
        return 0


#코랩 내 형태소 분석기로 데이터 넘기기
def make_okt_token(title_data):
    data={'제목': title_data}
    response=requests.post(COLAB_API_URL_OKT, json=data)    #JSON 형식(dict)으로 통신
    result=response.json()
    return result['tokenized_title']


#코랩 내 모델 예측
def make_nlp_predict(tokenized_title_data):
    data={'토큰화_제목': tokenized_title_data}
    response=requests.post(COLAB_API_URL_NLP, json=data)
    result=response.json()
    return result['label'], result['percent']


#코랩 내 모델 다시 Train
def make_model_fit(DB_df):
    data={'DB': DB_df}
    response=requests.post(COLAB_API_URL_TRN, json=data)
    result=response.json()
    if result==1:
        print('Train Success')
    else: 
        print('Train Failed')


# #구름IDE 내 형태소 분석기로 데이터 넘기기
# def make_test_okt_token(title_data):
#     title = [title_data]
#     title_cleaned = oktt.okt_func(title)
#     return title_cleaned
    
# #구름IDE 내 모델 예측
# def make_nlp_predict(tokenized_title_data):
#     predicted_label, predicted_percent = predict.predict(tokenized_title_data)
#     return predicted_label, predicted_percent
    
    
if __name__=="__main__":
    # DB_df=gdb.get_db()       #DB 데이터 가져오기
    # make_model_fit(DB_df)    #DB_df로 비동기적 train    
    # model_name="beomi/KcELECTRA-base-v2022"
    # model_save_path="/workspace/nlp_project/project/model_pth/ElectraModel_CNN.pth"
    # loaded_model=model.BertCNNClassifier(model_name).to(device)
    # loaded_model.load_state_dict(torch.load(model_save_path))
    # tokenizer=ElectraTokenizerFast.from_pretrained(model_name)
    # print("done..")
    app.run(host='0.0.0.0', port=80, debug=True)
    
    
