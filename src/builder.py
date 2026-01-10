import os
import shutil
import csv

from datetime import datetime, timezone, timedelta
from config import NEWS_CATEGORIES, SATURATION_THRESHOLD
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def read_file(path):
    full_path = BASE_DIR / path
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()
    
def render_page(content_template_path, context):
    base = read_file("templates/base.html")
    content = read_file(content_template_path)
    for k, v in context.items():
        token = "{{" + k + "}}"
        content = content.replace(token, str(v))
    context2 = dict(context)
    context2["content"] = content
    for k, v in context2.items():
        token = "{{" + k + "}}"
        base = base.replace(token, str(v))
    return base

def load_partials():
    share_buttons = read_file("templates/partials/share_buttons.html")
    share_js = read_file("templates/partials/share_buttons_js.html")
    return share_buttons, share_js

def generate_nav_links(current_category=None, is_archive_detail=False):
    """네비게이션 링크 생성
    
    is_archive_detail: archive/ 폴더 안의 개별 파일인 경우 True (../ 필요)
    """
    prefix = "../" if is_archive_detail else ""
    
    nav = f'<a href="{prefix}index.html" class="nav-btn">🏠 홈</a>'
    
    for cat_id, cat_info in NEWS_CATEGORIES.items():
        active = "active" if cat_id == current_category else ""
        nav += f'<a href="{prefix}{cat_info["output"]}" class="nav-btn {active}">{cat_info["icon"]} {cat_info["name"]}</a>'
    
    nav += f'<a href="{prefix}archive.html" class="nav-btn">🗂️ 아카이브</a>'
    nav += f'<a href="{prefix}manual-archive.html" class="nav-btn">📋 수동아카이브</a>'
    nav += '<a href="https://news-keyword-pro.onrender.com" class="nav-btn" target="_blank">🔍 수동검색</a>'
    
    return nav

def build_category_page(category_id, category_info, keyword_results, related_data=None):
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    update_time = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    date_prefix = now.strftime("%Y-%m-%d_%H-%M")
    
    filtered_results = [r for r in keyword_results if r.get("saturation", 999999) <= SATURATION_THRESHOLD]
    
    table_rows = ""
    for idx, item in enumerate(filtered_results, 1):
        keyword = item.get("keyword", "")
        naver_url = f"https://search.naver.com/search.naver?query={keyword}"
        table_rows += f"""
        <tr>
            <td>{idx}</td>
            <td><strong>{keyword}</strong></td>
            <td>{item.get('monthly_search', 0):,}</td>
            <td>{item.get('blog_count', 0):,}</td>
            <td>{item.get('saturation', '')}</td>
            <td>{item.get('possibility', '')}</td>
            <td><a href="{naver_url}" target="_blank" class="analyze-btn">🔍</a></td>
        </tr>
        """
    
    related_cards = ""
    if related_data:
        for item in related_data[:10]:
            keyword = item.get("keyword", "")
            related = item.get("related", [])
            naver_url = f"https://search.naver.com/search.naver?query={keyword}"
            
            related_items = ""
            for rel_kw in related[:5]:
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
    
    share_buttons, share_js = load_partials()
    
    context = {
        "page_title": f"{category_info['icon']} {category_info['name']} - 뉴스 키워드",
        "meta_tags": "",
        "head_extra": "",
        "body_extra": "",
        "header_title": f"{category_info['icon']} {category_info['name']} 키워드",
        "header_subtitle": f"상위노출 가능한 블로그 키워드 {len(filtered_results)}개",
        "update_time": update_time,
        "share_buttons": share_buttons,
        "share_js": share_js,
        "nav_links": generate_nav_links(current_category=category_id, is_archive_detail=False),
        "keyword_rows": table_rows,
        "related_cards": related_cards,
    }
    
    html = render_page("templates/pages/category.html", context)
    
    output_path = BASE_DIR / "output" / category_info["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 아카이브 저장
    archive_dir = BASE_DIR / "output" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_filename = f"{date_prefix}_{category_id}.html"
    archive_path = archive_dir / archive_filename
    
    archive_context = dict(context)
    archive_context["nav_links"] = generate_nav_links(current_category=category_id, is_archive_detail=True)
    archive_html = render_page("templates/pages/category.html", archive_context)
    
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(archive_html)
    
    print(f"    ✅ {output_path} 생성 완료 ({len(filtered_results)}개 키워드)")

def save_to_csv(category_name, keyword_results):
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    csv_dir = "output/csv"
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = f"{csv_dir}/{date_str}.csv"
    
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['시간', '카테고리', '키워드', '월간검색량', '블로그', '포화도', '난이도'])
        
        for item in keyword_results:
            writer.writerow([
                time_str,
                category_name,
                item['keyword'],
                item['monthly_search'],
                item.get('blog_count', 0),
                item['saturation'],
                item['possibility']
            ])

def build_index_page(all_results):
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    update_time = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    
    summary_cards = ""
    for cat_id, results in all_results.items():
        if not results:
            continue
        cat_info = NEWS_CATEGORIES[cat_id]
        filtered = [r for r in results if r["saturation"] <= SATURATION_THRESHOLD]
        top_keywords = filtered[:3]
        if not top_keywords:
            continue
        
        keywords_preview = ", ".join([r["keyword"] for r in top_keywords])
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
    
    share_buttons, share_js = load_partials()
    
    context = {
        "page_title": "뉴스 키워드 인사이트 Pro - 블로그 상위노출 키워드 분석",
        "meta_tags": "",
        "head_extra": "",
        "body_extra": "",
        "header_title": "🎯 뉴스 키워드 인사이트 Pro",
        "header_subtitle": "카테고리별 고단가 블로그 키워드 분석",
        "update_time": update_time,
        "share_buttons": share_buttons,
        "share_js": share_js,
        "nav_links": generate_nav_links(is_archive_detail=False),
        "summary_cards": summary_cards,
    }
    
    html = render_page("templates/pages/index.html", context)
    
    output_path = BASE_DIR / "output" / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("    ✅ output/index.html 생성 완료")

def build_archive_page():
    archive_dir = BASE_DIR / "output" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # manual 파일 제외
    files = sorted(
        [p.name for p in archive_dir.glob("*.html") if "_manual_" not in p.name], 
        reverse=True
    )
    
    items_per_page = 50
    total_files = len(files)
    total_pages = (total_files + items_per_page - 1) // items_per_page
    if total_pages == 0:
        total_pages = 1
    
    ad_code = """
    <li style="list-style:none; text-align:center; padding: 20px; background: #f9f9f9; margin: 10px 0;">
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-6677996696534146"
             data-ad-slot="4514938349"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </li>
    """
    
    kst = timezone(timedelta(hours=9))
    update_time = datetime.now(kst).strftime("%Y년 %m월 %d일 %H시 %M분")
    share_buttons, share_js = load_partials()
    
    for page in range(1, total_pages + 1):
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_files = files[start_idx:end_idx]
        
        file_list = ""
        for idx, filename in enumerate(page_files, 1):
            parts = filename.replace(".html", "").split("_")
            if len(parts) >= 3:
                date_part = parts[0]
                time_part = parts[1]
                category = parts[2]
                
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
                
                file_list += f"""
                <li>
                    <a href="archive/{filename}">
                        <span class="archive-date">📅 {display_date}</span>
                        <span class="archive-category">{cat_name}</span>
                    </a>
                </li>
                """
                
                if idx % 5 == 0:
                    file_list += ad_code
        
        pagination = '<div class="pagination">'
        if page > 1:
            prev_link = "archive.html" if page == 2 else f"archive-{page-1}.html"
            pagination += f'<a href="{prev_link}" class="page-btn">← 이전</a>'
        
        for p in range(1, total_pages + 1):
            p_link = "archive.html" if p == 1 else f"archive-{p}.html"
            active = "active" if p == page else ""
            pagination += f'<a href="{p_link}" class="page-btn {active}">{p}</a>'
        
        if page < total_pages:
            pagination += f'<a href="archive-{page+1}.html" class="page-btn">다음 →</a>'
        pagination += "</div>"
        
        context = {
            "page_title": "🗂️ 아카이브 - 뉴스 키워드 인사이트 Pro",
            "meta_tags": "",
            "head_extra": "",
            "body_extra": "",
            "header_title": "🗂️ 아카이브",
            "header_subtitle": "날짜별 생성된 리포트 모음",
            "update_time": update_time,
            "share_buttons": share_buttons,
            "share_js": share_js,
            "nav_links": generate_nav_links(is_archive_detail=False),
            "archive_count": str(total_files),
            "archive_list": file_list,
            "pagination": pagination,
        }
        
        html = render_page("templates/pages/archive.html", context)
        
        if page == 1:
            output_file = BASE_DIR / "output" / "archive.html"
        else:
            output_file = BASE_DIR / "output" / f"archive-{page}.html"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
    
    print(f"    ✅ 아카이브 생성 완료 ({total_files}개, {total_pages}페이지)")

def copy_static_files():
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    src_sw = BASE_DIR / "src" / "static" / "service-worker.js"
    dst_sw = output_dir / "service-worker.js"
    
    if not src_sw.exists():
        print(f"⚠️ service-worker.js 없음: {src_sw} (복사 스킵)")
        return
    
    shutil.copy2(src_sw, dst_sw)
    print(f"    ✅ service-worker 복사 완료: {dst_sw}")

def build_manual_archive_page():
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    files = sorted(
        [f for f in os.listdir(archive_dir) if f.endswith(".html") and "_manual_" in f],
        reverse=True
    )
    
    total_files = len(files)
    
    manual_list = ""
    ad_code = """
    <li style="list-style:none; text-align:center; padding: 20px; background: #f9f9f9; margin: 10px 0;">
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-6677996696534146"
             data-ad-slot="4514938349"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </li>
    """
    
    for idx, filename in enumerate(files, 1):
        parts = filename.replace(".html", "").split("_manual_")
        if len(parts) < 2:
            continue
        
        date_time = parts[0]
        keyword = parts[1]
        
        try:
            date_part, time_part = date_time.split("_")
            date_obj = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H-%M")
            display_date = date_obj.strftime("%Y년 %m월 %d일 %H:%M")
        except:
            display_date = date_time
        
        manual_list += f"""
        <li>
          <a href="archive/{filename}">
            <span class="archive-date">📅 {display_date}</span>
            <span class="archive-category">🔍 {keyword}</span>
          </a>
        </li>
        """
        
        if idx % 5 == 0:
            manual_list += ad_code
    
    kst = timezone(timedelta(hours=9))
    update_time = datetime.now(kst).strftime("%Y년 %m월 %d일 %H시 %M분")
    share_buttons, share_js = load_partials()
    
    context = {
        "page_title": "📋 수동 분석 아카이브",
        "meta_tags": "",
        "head_extra": "",
        "body_extra": "",
        "header_title": "📋 수동 분석 아카이브",
        "header_subtitle": "직접 분석한 키워드 리포트",
        "update_time": update_time,
        "share_buttons": share_buttons,
        "share_js": share_js,
        "nav_links": generate_nav_links(is_archive_detail=False),
        "manual_count": str(total_files),
        "manual_list": manual_list,
    }
    
    html = render_page("templates/pages/manual_archive.html", context)
    
    output_path = BASE_DIR / "output" / "manual-archive.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"    ✅ 수동 아카이브 생성 완료 ({total_files}개)")
