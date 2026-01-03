import os
import time
from openai import OpenAI

def extract_keywords(headlines, category_name=""):
    """OpenAI GPT로 키워드 추출"""
    
    print("    🧠 AI 분석 중...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("    ❌ OPENAI_API_KEY 없음")
        return []
    
    client = OpenAI(api_key=api_key)
    
    headlines_text = "\n".join([f"- {h}" for h in headlines])
    
    prompt = f"""다음은 [{category_name}] 관련 뉴스 헤드라인입니다:

{headlines_text}

위 헤드라인에서 블로그 검색에 적합한 키워드를 최대한 많이 추출해주세요.

규칙:
1. 각 헤드라인에서 4-6개의 키워드 추출
2. 키워드는 띄어쓰기 없이 붙여쓰기 (예: 삼성전자주가, 아파트청약)
3. 너무 일반적인 단어 제외 (뉴스, 오늘, 발표, 관련, 대한 등)
4. 다양한 형태로 추출:
   - 기업명: 삼성전자, 현대차, SK하이닉스
   - 상품명: 갤럭시S25, 아이폰16
   - 복합키워드: 전기차보조금, 청년주택청약, 코스피전망
   - 이슈키워드: 금리인하, 부동산대책
5. 비슷한 키워드도 다른 형태로 포함 (예: 삼성전자, 삼성전자주가, 삼성전자전망)
6. 최소 50개 이상의 키워드 추출
7. 키워드만 쉼표로 구분하여 출력 (설명 없이)

응답 형식: 키워드1, 키워드2, 키워드3, ..."""

    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048
            )
            
            result = response.choices[0].message.content
            
            keywords = [kw.strip().replace(" ", "") for kw in result.split(",")]
            keywords = [kw for kw in keywords if len(kw) >= 2]
            keywords = list(dict.fromkeys(keywords))
            
            print(f"    ✅ {len(keywords)}개 키워드 추출")
            return keywords
            
        except Exception as e:
            error_str = str(e)
            print(f"    ⚠️ 에러: {error_str[:100]}")
            
            if "429" in error_str or "rate" in error_str.lower():
                wait_time = (attempt + 1) * 10
                print(f"    ⏳ {wait_time}초 대기 후 재시도...")
                time.sleep(wait_time)
            else:
                return []
    
    print("    ❌ 최대 재시도 초과")
    return []
