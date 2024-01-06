from bs4 import BeautifulSoup 
import numpy as np
import time, random, re
import requests 
import traceback
import warnings
warnings.filterwarnings("ignore") 

def news_crawl(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    web=requests.get(url, headers=headers).content
    source_news=BeautifulSoup(web, 'html.parser')
    title_=source_news.find('h2', {'class' : 'media_end_head_headline'}).get_text()
    title_=title_.replace("'", "").replace('"', '')
    title=re.sub(r"[^ㄱ-ㅎㅏ-ㅣ가-힣A-Za-z0-9\s.!?]", "", title_)

    
    article_=source_news.find('article', {'id' : 'dic_area'}).get_text()
    article_=article_.replace("'", "").replace('"', '').replace("\n", "").replace("동영상 뉴스", "").strip()
    article=re.sub(r"[^ㄱ-ㅎㅏ-ㅣ가-힣A-Za-z0-9\s.!?]", "", article_)
    
    return title, article
    
#url='https://n.news.naver.com/article/308/0000033946?sid=102'
#news_crawl(url)