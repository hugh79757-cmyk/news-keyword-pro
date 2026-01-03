"""카테고리별 뉴스 소스 설정"""

NEWS_CATEGORIES = {
    "stock": {
        "name": "증권/주식",
        "query": "주식 증권 코스피",
        "icon": "📈",
        "output": "stock.html"
    },
    "realestate": {
        "name": "부동산",
        "query": "아파트 부동산 청약",
        "icon": "🏠",
        "output": "realestate.html"
    },
    "finance": {
        "name": "금융",
        "query": "은행 대출 금리",
        "icon": "💰",
        "output": "finance.html"
    },
    "car": {
        "name": "자동차",
        "query": "자동차 전기차 현대차",
        "icon": "🚗",
        "output": "car.html"
    },
    "health": {
        "name": "건강/의료",
        "query": "건강 다이어트 영양제",
        "icon": "💊",
        "output": "health.html"
    },
    "tech": {
        "name": "IT/모바일",
        "query": "스마트폰 아이폰 AI",
        "icon": "📱",
        "output": "tech.html"
    },
    "policy": {
        "name": "정부정책",
        "query": "정부 지원금 복지",
        "icon": "🏛️",
        "output": "policy.html"
    }
}

# 카테고리당 체크할 키워드 수
KEYWORDS_PER_CATEGORY = 30

# 포화도 필터 기준
SATURATION_THRESHOLD = 2.0
