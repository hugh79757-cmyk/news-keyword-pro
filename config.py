"""카테고리별 뉴스 소스 설정"""

NEWS_CATEGORIES = {
    "stock": {
        "name": "증권/주식",
        "query": "주식 OR 증권 OR 코스피 OR 삼성전자 OR SK하이닉스",
        "icon": "📈",
        "output": "stock.html"
    },
    "realestate": {
        "name": "부동산",
        "query": "아파트 OR 부동산 OR 청약 OR 분양 OR 전세",
        "icon": "🏠",
        "output": "realestate.html"
    },
    "finance": {
        "name": "금융",
        "query": "은행 OR 대출 OR 금리 OR 예금 OR 적금",
        "icon": "💰",
        "output": "finance.html"
    },
    "car": {
        "name": "자동차",
        "query": "자동차 OR 전기차 OR 현대차 OR 기아 OR 테슬라",
        "icon": "🚗",
        "output": "car.html"
    },
    "health": {
        "name": "건강/의료",
        "query": "건강 OR 다이어트 OR 영양제 OR 운동 OR 병원",
        "icon": "💊",
        "output": "health.html"
    },
    "tech": {
        "name": "IT/모바일",
        "query": "스마트폰 OR 아이폰 OR 갤럭시 OR AI OR 인공지능",
        "icon": "📱",
        "output": "tech.html"
    },
    "policy": {
        "name": "정부정책",
        "query": "정부 OR 지원금 OR 보조금 OR 복지 OR 청년",
        "icon": "🏛️",
        "output": "policy.html"
    }
}

# 카테고리당 체크할 키워드 수
KEYWORDS_PER_CATEGORY = 50

# 포화도 필터 기준
SATURATION_THRESHOLD = 1.0
