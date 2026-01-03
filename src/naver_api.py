import os
import requests
import hashlib
import hmac
import base64
import time

def get_search_volume(keywords):
    """네이버 광고 API로 검색량 조회"""
    
    customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
    api_key = os.getenv("NAVER_AD_CLIENT_ID")          # 변경
    secret_key = os.getenv("NAVER_AD_CLIENT_SECRET")   # 변경
    
    if not all([customer_id, api_key, secret_key]):
        print("    ⚠️ 네이버 광고 API 키 없음")
        return {}
    
    url = "https://api.naver.com/keywordstool"
    
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, "GET", "/keywordstool", secret_key)
    
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": customer_id,
        "X-Signature": signature
    }
    
    results = {}
    
    # 5개씩 나눠서 요청
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        params = {
            "hintKeywords": ",".join(batch),
            "showDetail": "1"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("keywordList", []):
                    keyword = item.get("relKeyword", "").replace(" ", "")
                    monthly = item.get("monthlyPcQcCnt", 0)
                    mobile = item.get("monthlyMobileQcCnt", 0)
                    
                    if monthly == "< 10":
                        monthly = 5
                    if mobile == "< 10":
                        mobile = 5
                    
                    total = int(monthly or 0) + int(mobile or 0)
                    if keyword and total > 0:
                        results[keyword] = total
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"    ⚠️ 검색량 조회 에러: {e}")
    
    return results


def generate_signature(timestamp, method, path, secret_key):
    """API 서명 생성"""
    message = f"{timestamp}.{method}.{path}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')


def get_blog_count(keyword):
    """네이버 검색 API로 블로그 문서 수 조회"""
    
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not all([client_id, client_secret]):
        return 0
    
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {"query": keyword, "display": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get("total", 0)
    except:
        pass
    
    return 0


def get_autocomplete(keyword):
    """네이버 자동완성 API로 연관검색어 조회"""
    
    url = "https://mac.search.naver.com/mobile/ac"
    params = {
        "q": keyword,
        "st": "1",
        "frm": "mobile_nv",
        "r_format": "json",
        "r_enc": "UTF-8",
        "r_unicode": "0",
        "t_koreng": "1",
        "ans": "2",
        "run": "2"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [[]])[0]
            return [item[0] for item in items[:5] if item]
    except:
        pass
    
    return []


def analyze_keywords(keywords, limit=15):
    """키워드 분석 (검색량 + 블로그수 + 포화도)"""
    
    print(f"    📊 {len(keywords)}개 중 상위 {limit}개 분석...")
    
    keywords_to_check = keywords[:limit]
    
    # 검색량 조회
    search_volumes = get_search_volume(keywords_to_check)
    
    results = []
    
    for keyword in keywords_to_check:
        monthly_search = search_volumes.get(keyword, 0)
        
        if monthly_search < 500:
            continue
        
        blog_count = get_blog_count(keyword)
        time.sleep(0.05)
        
        if blog_count == 0:
            saturation = 0
        else:
            saturation = round(blog_count / monthly_search, 2)
        
        # 포화도 등급
        if saturation <= 0.5:
            possibility = "🟢 매우쉬움"
        elif saturation <= 1.0:
            possibility = "🟡 쉬움"
        elif saturation <= 1.5:
            possibility = "🟠 보통"
        else:
            possibility = "🔴 어려움"
        
        results.append({
            "keyword": keyword,
            "monthly_search": monthly_search,
            "blog_count": blog_count,
            "saturation": saturation,
            "possibility": possibility
        })
    
    # 포화도순 정렬
    results.sort(key=lambda x: x["saturation"])
    
    print(f"    ✅ {len(results)}개 키워드 분석 완료")
    return results
