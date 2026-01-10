"""분석 없이 빌드만 실행하는 스크립트 (DEV MODE)"""
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from config import NEWS_CATEGORIES
from src import builder

def main():
    print("=" * 60)
    print("⚡ 빠른 빌드 모드 (분석 스킵)")
    print("=" * 60)
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    print(f"⏰ 실행 시간: {now.strftime('%Y-%m-%d %H:%M')} KST")
    print(f"📂 카테고리: {len(NEWS_CATEGORIES)}개\n")
    
    # 더미 데이터로 카드 표시 (실제 분석 없이)
    all_results = {}
    for cat_id, cat_info in NEWS_CATEGORIES.items():
        all_results[cat_id] = [
            {"keyword": "샘플키워드1", "saturation": 0.5},
            {"keyword": "샘플키워드2", "saturation": 0.6},
            {"keyword": "샘플키워드3", "saturation": 0.7},
        ]
    
    print("📄 페이지 생성 중...")
    print("─" * 60)
    
    # 메인 페이지 생성 (카드 포함)
    builder.build_index_page(all_results)
    
    # 아카이브 페이지 생성
    builder.build_archive_page()
    builder.build_manual_archive_page()
    
    # 정적 파일 복사
    builder.copy_static_files()
    
    print("─" * 60)
    print("✅ 빌드 완료!")
    print("=" * 60)
    print("")
    print("🔍 확인할 항목:")
    print("   • output/index.html - 메인 페이지")
    print("   • output/archive.html - 아카이브")
    print("   • output/*.html - 카테고리 페이지")
    print("")
    print("💡 로컬 서버로 확인하려면:")
    print("   cd output && python -m http.server 8000")
    print("   → http://localhost:8000")


if __name__ == "__main__":
    main()
