import pymysql
import pandas as pd

def get_db():
    my_db = pymysql.connect(host = 'localhost', user = 'root', passwd = '1234',
                            db = 'news', charset = 'utf8',
                            cursorclass = pymysql.cursors.DictCursor)

    # NewsDB 이용
    cursor = my_db.cursor()
    cursor.execute('USE news;')

    # 전체 데이터 table로 받아오기
    query = "SELECT * FROM newstbl"
    cursor.execute(query)
    result = cursor.fetchall()
    my_db.close()

    # 데이터 프레임으로 변환
    df = pd.DataFrame(result)
    df = df[:, 1:]
    return df