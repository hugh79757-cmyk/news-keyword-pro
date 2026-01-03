import os
import requests

def crawl_news(category_id, query):
    """네이버 뉴스 API로 뉴스 헤드라인 가져오기"""
    print(f"    🔍 검색어: {query}")
    
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("    ❌ 네이버 API 키 없음")
        return []
    
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query,
        "display": 50,
        "sort": "date"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        headlines = []
        for item in items:
            # HTML 태그 제거
            title = item.get("title", "")
            title = title.replace("<b>", "").replace("</b>", "")
            title = title.replace("&quot;", '"').replace("&amp;", "&")
            title = title.replace("&lt;", "<").replace("&gt;", ">")
            
            if title and len(title) > 10:
                headlines.append(title)
        
        # 중복 제거
        headlines = list(dict.fromkeys(headlines))
        return headlines[:35]
        
    except Exception as e:
        print(f"    ❌ API 에러: {e}")
        return []
