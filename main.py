import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from config import NEWS_CATEGORIES, KEYWORDS_PER_CATEGORY
from src import news_crawler, analyzer, naver_api, builder

def main():
    print("=" * 60)
    print("🚀 뉴스 키워드 분석 봇 (Pro Edition)")
    print("=" * 60)
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    print(f"⏰ 실행 시간: {now.strftime('%Y-%m-%d %H:%M')} KST")
    print(f"📂 카테고리: {len(NEWS_CATEGORIES)}개\n")
    
    all_results = {}
    
    for category_id, category_info in NEWS_CATEGORIES.items():
        print(f"\n{'─'*60}")
        print(f"{category_info['icon']} [{category_info['name']}] 처리 시작")
        print("─" * 60)
        
        # 1. 뉴스 API 호출
        print(f"\n  [1/4] 뉴스 수집 중...")
        headlines = news_crawler.crawl_news(category_id, category_info['query'])
        
        if not headlines:
            print(f"    ⚠️ 뉴스 없음, 스킵")
            all_results[category_id] = []
            continue
        
        print(f"    ✅ {len(headlines)}개 헤드라인 수집")
        
        # 2. AI 키워드 추출
        print(f"\n  [2/4] AI 키워드 추출 중...")
        keywords = analyzer.extract_keywords(headlines, category_info['name'])
        
        if not keywords:
            print(f"    ⚠️ 키워드 추출 실패, 스킵")
            all_results[category_id] = []
            continue
        
        # 3. 네이버 API 분석
        print(f"\n  [3/4] 키워드 분석 중...")
        keyword_results = naver_api.analyze_keywords(keywords, KEYWORDS_PER_CATEGORY)
        
        # 연관검색어 조회 (상위 5개만)
        related_data = []
        for item in keyword_results[:15]:
            related = naver_api.get_autocomplete(item['keyword'])
            related_data.append({
                "keyword": item['keyword'],
                "related": related[:5]
            })
        
        all_results[category_id] = keyword_results
        
        # 4. 카테고리 페이지 생성
        print(f"\n  [4/4] 페이지 생성 중...")
        builder.build_category_page(category_id, category_info, keyword_results, related_data)
        
        # 5. CSV에 저장
        builder.save_to_csv(category_info['name'], keyword_results)
    
    # 메인 페이지 생성
    print(f"\n{'='*60}")
    print("📄 메인 페이지 및 아카이브 생성")
    print("=" * 60)
    
    builder.build_index_page(all_results)
    builder.build_archive_page()
    
    # 완료 요약
    print(f"\n{'='*60}")
    print("✅ 모든 작업 완료!")
    print("=" * 60)
    
    total_keywords = sum(len(results) for results in all_results.values())
    print(f"📊 총 {total_keywords}개 키워드 분석됨")
    
    for cat_id, results in all_results.items():
        cat_info = NEWS_CATEGORIES[cat_id]
        print(f"   {cat_info['icon']} {cat_info['name']}: {len(results)}개")
    
    print(f"\n📁 CSV 저장: output/history.csv")


if __name__ == "__main__":
    main()
