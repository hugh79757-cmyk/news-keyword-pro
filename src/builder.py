import os
import shutil
from datetime import datetime, timezone, timedelta
from config import NEWS_CATEGORIES, SATURATION_THRESHOLD

def build_category_page(category_id, category_info, keyword_results, related_data=None):
    """카테고리별 HTML 페이지 생성"""
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    update_time = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    date_prefix = now.strftime("%Y-%m-%d_%H-%M")
    
    # 포화도 필터링
    filtered_results = [r for r in keyword_results if r["saturation"] <= SATURATION_THRESHOLD]
    
    # 템플릿 읽기
    try:
        with open("templates/category.html", "r", encoding="utf-8") as f:
            template = f.read()
    except:
        print(f"    ❌ 템플릿 파일 없음")
        return
    
    # 키워드 테이블 생성
    table_rows = ""
    for idx, item in enumerate(filtered_results, 1):
        keyword = item['keyword']
        naver_url = f"https://search.naver.com/search.naver?query={keyword}"
        table_rows += f"""
        <tr>
            <td>{idx}</td>
            <td><strong>{keyword}</strong></td>
            <td>{item['monthly_search']:,}</td>
            <td>{item['blog_count']:,}</td>
            <td>{item['saturation']}</td>
            <td>{item['possibility']}</td>
            <td><a href="{naver_url}" target="_blank" class="analyze-btn">🔍</a></td>
        </tr>
        """
    
    # 연관검색어 카드 생성
    related_cards = ""
    if related_data:
        for item in related_data[:10]:
            keyword = item['keyword']
            related = item['related']
            naver_url = f"https://search.naver.com/search.naver?query={keyword}"
            
            related_items = ""
            for rel_kw in related:
                rel_url = f"https://search.naver.com/search.naver?query={rel_kw}"
                related_items += f'<li><a href="{rel_url}" target="_blank">{rel_kw}</a></li>'
            
            if not related:
                related_items = '<li class="no-data">연관검색어 없음</li>'
            
            related_cards += f"""
            <div class="related-card">
                <div class="related-header">
                    <strong>{keyword}</strong>
                    <a href="{naver_url}" target="_blank" class="analyze-btn">🔍</a>
                </div>
                <ul class="related-list">{related_items}</ul>
            </div>
            """
    
    # 템플릿 치환
    html = template.replace("{{category_name}}", category_info['name'])
    html = html.replace("{{category_icon}}", category_info['icon'])
    html = html.replace("{{update_time}}", update_time)
    html = html.replace("{{keyword_rows}}", table_rows)
    html = html.replace("{{related_cards}}", related_cards)
    html = html.replace("{{keyword_count}}", str(len(filtered_results)))
    
    # 네비게이션 생성
    nav_html = generate_nav_links(category_id)
    html = html.replace("{{nav_links}}", nav_html)
    
    # 저장
    output_path = f"output/{category_info['output']}"
    
    # 🔴 아카이브 백업 (기존 파일이 있으면)
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    if os.path.exists(output_path):
        archive_filename = f"{date_prefix}_{category_id}.html"
        archive_path = os.path.join(archive_dir, archive_filename)
        shutil.copy(output_path, archive_path)
    
    # 새 파일 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"    ✅ {output_path} 생성 완료 ({len(filtered_results)}개 키워드)")


def generate_nav_links(current_category=None):
    """네비게이션 링크 생성"""
    nav = '<a href="index.html" class="nav-btn">🏠 홈</a>'
    
    for cat_id, cat_info in NEWS_CATEGORIES.items():
        active = "active" if cat_id == current_category else ""
        nav += f'<a href="{cat_info["output"]}" class="nav-btn {active}">{cat_info["icon"]} {cat_info["name"]}</a>'
    
    nav += '<a href="archive.html" class="nav-btn">📚 아카이브</a>'
    return nav


def build_index_page(all_results):
    """메인 인덱스 페이지 생성"""
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    update_time = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    
    try:
        with open("templates/layout.html", "r", encoding="utf-8") as f:
            template = f.read()
    except:
        print("    ❌ 템플릿 파일 없음")
        return
    
    # 카테고리별 요약 카드 생성
    summary_cards = ""
    for cat_id, results in all_results.items():
        if not results:
            continue
        
        cat_info = NEWS_CATEGORIES[cat_id]
        filtered = [r for r in results if r["saturation"] <= SATURATION_THRESHOLD]
        top_keywords = filtered[:3]
        
        if not top_keywords:
            continue
        
        keywords_preview = ", ".join([r['keyword'] for r in top_keywords])
        
        summary_cards += f"""
        <div class="summary-card">
            <div class="summary-header">
                <span class="summary-icon">{cat_info['icon']}</span>
                <h3>{cat_info['name']}</h3>
            </div>
            <p class="summary-keywords">{keywords_preview}</p>
            <div class="summary-footer">
                <span>{len(filtered)}개 키워드</span>
                <a href="{cat_info['output']}" class="view-btn">자세히 보기 →</a>
            </div>
        </div>
        """
    
    # 네비게이션
    nav_html = generate_nav_links()
    
    # 템플릿 치환
    html = template.replace("{{update_time}}", update_time)
    html = html.replace("{{summary_cards}}", summary_cards)
    html = html.replace("{{nav_links}}", nav_html)
    
    # 저장
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("    ✅ output/index.html 생성 완료")


def build_archive_page():
    """아카이브 페이지 생성"""
    
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    files = sorted(
        [f for f in os.listdir(archive_dir) if f.endswith('.html')],
        reverse=True
    )
    
    try:
        with open("templates/archive.html", "r", encoding="utf-8") as f:
            template = f.read()
    except:
        template = get_default_archive_template()
    
    # 파일 목록 생성
    file_list = ""
    for filename in files:
        parts = filename.replace('.html', '').split('_')
        if len(parts) >= 3:
            date_part = parts[0]
            time_part = parts[1]
            category = parts[2]
            
            # 카테고리 이름 찾기
            cat_name = category
            for cat_id, cat_info in NEWS_CATEGORIES.items():
                if cat_id == category:
                    cat_name = f"{cat_info['icon']} {cat_info['name']}"
                    break
            
            try:
                date_obj = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H-%M")
                display_date = date_obj.strftime("%Y년 %m월 %d일 %H:%M")
            except:
                display_date = date_part
            
            file_list += f'''
            <li>
                <a href="archive/{filename}">
                    <span class="archive-date">📅 {display_date}</span>
                    <span class="archive-category">{cat_name}</span>
                </a>
            </li>
            '''
    
    html = template.replace("{{archive_count}}", str(len(files)))
    html = html.replace("{{archive_list}}", file_list)
    html = html.replace("{{nav_links}}", generate_nav_links())
    
    with open("output/archive.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"    ✅ output/archive.html 생성 완료 ({len(files)}개 아카이브)")


def get_default_archive_template():
    """기본 아카이브 템플릿"""
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>아카이브 - 뉴스 키워드</title>
</head>
<body>
    <h1>아카이브</h1>
    <p>{{archive_count}}개 저장됨</p>
    <ul>{{archive_list}}</ul>
</body>
</html>"""
