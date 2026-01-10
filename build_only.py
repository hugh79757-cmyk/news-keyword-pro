"""분석 없이 빌드만 실행하는 스크립트 (DEV MODE)"""
import os
import sys
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
    
    # 빈 결과로 초기화 (분석 스킵)
    all_results = {cat_id: [] for cat_id in NEWS_CATEGORIES}
    
    print("📄 페이지 생성 중...")
    print("─" * 60)
    
    # 메인 페이지 생성
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
