#!/usr/bin/env python3
"""백업된 아카이브 파일들의 네비게이션 링크를 수정하는 스크립트"""

import os
import re
from pathlib import Path

# 카테고리 정보
NEWS_CATEGORIES = {
    "stock": {"name": "증권/주식", "icon": "📈", "output": "stock.html"},
    "realestate": {"name": "부동산", "icon": "🏠", "output": "realestate.html"},
    "finance": {"name": "금융", "icon": "💰", "output": "finance.html"},
    "car": {"name": "자동차", "icon": "🚗", "output": "car.html"},
    "health": {"name": "건강/의료", "icon": "💊", "output": "health.html"},
    "tech": {"name": "IT/모바일", "icon": "📱", "output": "tech.html"},
    "policy": {"name": "정부정책", "icon": "🏛️", "output": "policy.html"},
}

def generate_correct_nav(current_category=None):
    """올바른 네비게이션 링크 생성 (archive 폴더용)"""
    prefix = "../"
    nav = f'<a href="{prefix}index.html" class="nav-btn">🏠 홈</a>'
    
    for cat_id, cat_info in NEWS_CATEGORIES.items():
        active = "active" if cat_id == current_category else ""
        nav += f'<a href="{prefix}{cat_info["output"]}" class="nav-btn {active}">{cat_info["icon"]} {cat_info["name"]}</a>'
    
    nav += f'<a href="{prefix}archive.html" class="nav-btn">🗂️ 아카이브</a>'
    nav += f'<a href="{prefix}manual-archive.html" class="nav-btn">📋 수동아카이브</a>'
    nav += '<a href="https://news-keyword-pro.onrender.com" class="nav-btn" target="_blank">🔍 수동검색</a>'
    
    return nav

def get_category_from_filename(filename):
    """파일명에서 카테고리 추출"""
    parts = filename.replace(".html", "").split("_")
    if len(parts) >= 3:
        return parts[2]
    return None

def fix_file(filepath):
    """파일의 네비게이션 링크 수정"""
    filename = os.path.basename(filepath)
    category = get_category_from_filename(filename)
    
    if not category:
        print(f"  ⚠️ 카테고리 추출 실패: {filename}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 기존 nav 영역 찾기
    nav_pattern = r'<nav class="nav">\s*.*?\s*</nav>'
    correct_nav = f'<nav class="nav">\n    {generate_correct_nav(category)}\n  </nav>'
    
    new_content = re.sub(nav_pattern, correct_nav, content, flags=re.DOTALL)
    
    # href="/" 를 href="../index.html" 로 변경
    new_content = new_content.replace('href="/"', 'href="../index.html"')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    backup_dir = Path("output/archive_backup")
    
    if not backup_dir.exists():
        print("❌ output/archive_backup 폴더가 없습니다.")
        return
    
    files = list(backup_dir.glob("*.html"))
    print(f"📁 {len(files)}개 파일 발견\n")
    
    success = 0
    for filepath in files:
        print(f"  🔧 수정 중: {filepath.name}")
        if fix_file(filepath):
            success += 1
    
    print(f"\n✅ {success}/{len(files)}개 파일 수정 완료!")
    print(f"\n다음 명령어로 archive 폴더로 이동:")
    print(f"  mv output/archive_backup/*.html output/archive/")

if __name__ == "__main__":
    main()
