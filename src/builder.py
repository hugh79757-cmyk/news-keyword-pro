import os
import shutil
import csv

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
    ad_code = """
        <tr>
            <td colspan="7" style="text-align:center; padding: 20px; background: #f9f9f9;">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-6677996696534146"
                     data-ad-slot="4514938349"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
            </td>
        </tr>
        """
    
    for idx, item in enumerate(filtered_results, 1):
        keyword = item['keyword']
        naver_url = f"https://search.naver.com/search.naver?query={keyword}"
        table_rows += f"""
        <tr>
            <td>{idx}</td>
            <td><strong>{keyword}</strong></td>
            <td>{item['monthly_search']:,}</td>
            <td>{item.get('blog_count', 0):,}</td>
            <td>{item['saturation']}</td>
            <td>{item['possibility']}</td>
            <td><a href="{naver_url}" target="_blank" class="analyze-btn">🔍</a></td>
        </tr>
        """
        # 5개마다 광고 삽입
        # 테이블 중간 광고 비활성화 (정렬 문제)
        # if idx % 5 == 0:
        #     table_rows += ad_code
    
    related_cards = ""
    related_ad_code = """
    <div style="text-align:center; padding: 20px; background: #f9f9f9; border-radius: 12px; margin-bottom: 15px;">
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-6677996696534146"
             data-ad-slot="4514938349"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </div>
    """
    
    if related_data:
        for idx, item in enumerate(related_data[:10], 1):
            keyword = item['keyword']
            related = item['related']
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
            
            # 3개마다 광고 삽입
            if idx % 3 == 0:
                related_cards += related_ad_code

    
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
    
    # 아카이브 백업 (단순화된 네비게이션 적용)
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    archive_filename = f"{date_prefix}_{category_id}.html"
    archive_path = os.path.join(archive_dir, archive_filename)
    
    # 아카이브용 HTML 생성 (단순화된 네비게이션)
    archive_nav_html = generate_nav_links(category_id, is_archive=True)
    archive_html = template.replace("{{category_name}}", category_info['name'])
    archive_html = archive_html.replace("{{category_icon}}", category_info['icon'])
    archive_html = archive_html.replace("{{update_time}}", update_time)
    archive_html = archive_html.replace("{{keyword_rows}}", table_rows)
    archive_html = archive_html.replace("{{related_cards}}", related_cards)
    archive_html = archive_html.replace("{{keyword_count}}", str(len(filtered_results)))
    archive_html = archive_html.replace("{{nav_links}}", archive_nav_html)
    
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(archive_html)
    
    # 새 파일 저장 (일반 네비게이션)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"    ✅ {output_path} 생성 완료 ({len(filtered_results)}개 키워드)")


def generate_nav_links(current_category=None, is_archive=False):
    """네비게이션 링크 생성"""
    prefix = "../" if is_archive else ""
    
    # 아카이브 파일은 단순화된 네비게이션
    if is_archive:
        nav = f'<a href="/" class="nav-btn">🏠 홈</a>'
        nav += f'<a href="{prefix}archive.html" class="nav-btn">🗂️ 아카이브</a>'
        nav += f'<a href="{prefix}manual-archive.html" class="nav-btn">📋 수동아카이브</a>'
        nav += '<a href="https://news-keyword-pro.onrender.com" class="nav-btn" target="_blank">🔍 수동검색</a>'
        return nav
    
    # 일반 페이지는 전체 네비게이션
    nav = f'<a href="/" class="nav-btn">🏠 홈</a>'
    
    for cat_id, cat_info in NEWS_CATEGORIES.items():
        active = "active" if cat_id == current_category else ""
        nav += f'<a href="{prefix}{cat_info["output"]}" class="nav-btn {active}">{cat_info["icon"]} {cat_info["name"]}</a>'
    
    nav += f'<a href="{prefix}archive.html" class="nav-btn">🗂️ 아카이브</a>'
    nav += f'<a href="{prefix}manual-archive.html" class="nav-btn">📋 수동아카이브</a>'
    nav += '<a href="https://news-keyword-pro.onrender.com" class="nav-btn" target="_blank">🔍 수동검색</a>'

    return nav


def save_to_csv(category_name, keyword_results):
    """키워드 결과를 날짜별 CSV에 저장"""
    
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
    
    nav_html = generate_nav_links()
    
    html = template.replace("{{update_time}}", update_time)
    html = html.replace("{{summary_cards}}", summary_cards)
    html = html.replace("{{nav_links}}", nav_html)
    
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("    ✅ output/index.html 생성 완료")


def build_archive_page():
    """아카이브 페이지 생성 (페이지네이션 포함)"""
    
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
    
    items_per_page = 50
    total_files = len(files)
    total_pages = (total_files + items_per_page - 1) // items_per_page
    if total_pages == 0:
        total_pages = 1
    
    for page in range(1, total_pages + 1):
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_files = files[start_idx:end_idx]
        
        file_list = ""
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
        
        for idx, filename in enumerate(page_files, 1):
            parts = filename.replace('.html', '').split('_')

            if len(parts) >= 3:
                date_part = parts[0]
                time_part = parts[1]
                category = parts[2]
                
                cat_name = category
                if category == "manual":
                    cat_name = "🔍 수동분석"
                else:
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
                   # 5개마다 광고 삽입
                if idx % 5 == 0:
                    file_list += ad_code
        
        pagination = '<div class="pagination">'
        
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
        pagination += '</div>'
        
        html = template.replace("{{archive_count}}", str(total_files))
        html = html.replace("{{archive_list}}", file_list)
        html = html.replace("{{nav_links}}", generate_nav_links(is_archive=True))
        html = html.replace("{{pagination}}", pagination)
        
        if page == 1:
            output_file = "output/archive.html"
        else:
            output_file = f"output/archive-{page}.html"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
    
    print(f"    ✅ 아카이브 생성 완료 ({total_files}개, {total_pages}페이지)")


def get_default_archive_template():
    """기본 아카이브 템플릿"""
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>아카이브</title>
</head>
<body>
    <h1>아카이브</h1>
    <p>{{archive_count}}개</p>
    <ul>{{archive_list}}</ul>
    {{pagination}}
</body>
</html>"""


def build_manual_archive_page():
    """수동 분석 아카이브 페이지 생성"""
    
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    # _manual_ 파일만 필터링
    files = sorted(
        [f for f in os.listdir(archive_dir) if f.endswith('.html') and '_manual_' in f],
        reverse=True
    )
    
    total_files = len(files)
    
    file_list = ""
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
        parts = filename.replace('.html', '').split('_manual_')
        if len(parts) >= 2:
            date_time = parts[0]
            keyword = parts[1]
            
            try:
                date_part, time_part = date_time.split('_')
                date_obj = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H-%M")
                display_date = date_obj.strftime("%Y년 %m월 %d일 %H:%M")
            except:
                display_date = date_time
            
            file_list += f'''
            <li>
                <a href="archive/{filename}">
                    <span class="archive-date">📅 {display_date}</span>
                    <span class="archive-category">🔍 {keyword}</span>
                </a>
            </li>
            '''
            
            # 5개마다 광고 삽입
            if idx % 5 == 0:
                file_list += ad_code
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📋 수동 분석 아카이브</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6677996696534146" crossorigin="anonymous"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #1e3a8a;
            --gold: #f59e0b;
            --bg: #f0f4ff;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Noto Sans KR', sans-serif;
            background: linear-gradient(180deg, var(--bg) 0%, #f8fafc 100%);
            min-height: 100vh;
            color: var(--text);
            line-height: 1.7;
        }}
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, #1e40af 100%);
            padding: 2rem;
            text-align: center;
            color: white;
        }}
        .header h1 {{ font-size: 1.8rem; }}
        .nav {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            padding: 1rem;
            background: white;
            border-bottom: 1px solid var(--border);
        }}
        .nav-btn {{
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            color: var(--text);
            background: var(--bg);
            font-size: 0.9rem;
        }}
        .nav-btn:hover {{ background: var(--primary); color: white; }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        .count-box {{
            background: #fffbeb;
            border: 2px solid var(--gold);
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .count-box strong {{ font-size: 1.5rem; color: var(--primary); }}
        .archive-list {{ list-style: none; }}
        .archive-list li {{
            background: var(--card-bg);
            margin-bottom: 10px;
            border-radius: 8px;
            border: 1px solid var(--border);
            transition: all 0.2s;
        }}
        .archive-list li:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(30,58,138,0.15);
        }}
        .archive-list a {{
            display: flex;
            justify-content: space-between;
            padding: 14px 18px;
            color: var(--text);
            text-decoration: none;
        }}
        .archive-date {{ color: var(--text-light); }}
        .archive-category {{ color: var(--primary); font-weight: 500; }}
        .footer {{
            background: var(--primary);
            color: white;
            text-align: center;
            padding: 1.5rem;
            margin-top: 3rem;
        }}
        .share-buttons {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            max-width: 280px;
            margin: 1rem auto 0;
            gap: 10px;
        }}
        .share-buttons a {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            transition: all 0.3s;
        }}
        .share-buttons a:hover {{
            transform: scale(1.1);
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>📋 수동 분석 아카이브</h1>
        <p>직접 분석한 키워드 리포트</p>
        <div class="share-buttons">
            <a href="https://buymeacoffee.com/infohotinfo" target="_blank" title="커피 후원" style="background:#FFDD00;"><svg style="width:22px;height:22px;" viewBox="0 0 24 24"><path fill="#000" d="M20 3H4v10a4 4 0 004 4h6a4 4 0 004-4v-3h2a2 2 0 002-2V5a2 2 0 00-2-2zm0 5h-2V5h2v3zM4 19h16v2H4z"/></svg></a>
            <a href="javascript:void(0)" onclick="shareKakao()" title="카카오톡" style="background:#FEE500;"><svg style="width:24px;height:24px;" viewBox="0 0 24 24"><path fill="#000" d="M12 3c-5.52 0-10 3.59-10 8 0 2.84 1.89 5.33 4.73 6.73-.21.78-.77 2.82-.88 3.26-.14.54.2.53.42.39.17-.12 2.69-1.82 3.78-2.57.62.09 1.27.14 1.95.14 5.52 0 10-3.59 10-8s-4.48-8-10-8z"/></svg></a>
            <a href="javascript:void(0)" onclick="shareNaver()" title="네이버" style="background:#03C75A;"><svg style="width:22px;height:22px;fill:white;" viewBox="0 0 24 24"><path d="M16.273 12.845L7.376 0H0v24h7.727V11.155L16.624 24H24V0h-7.727z"/></svg></a>
            <a href="javascript:void(0)" onclick="shareLine()" title="라인" style="background:#06C755;"><svg style="width:22px;height:22px;fill:white;" viewBox="0 0 24 24"><path d="M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg></a>
            <a href="javascript:void(0)" onclick="shareFacebook()" title="페이스북" style="background:#1877F2;"><svg style="width:22px;height:22px;fill:white;" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></a>
            <a href="javascript:void(0)" onclick="shareTwitter()" title="X" style="background:#000;"><svg style="width:20px;height:20px;fill:white;" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
            <a href="javascript:void(0)" onclick="shareThreads()" title="스레드" style="background:#000;"><svg style="width:20px;height:20px;fill:white;" viewBox="0 0 24 24"><path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.96-.065-1.182.408-2.256 1.332-3.023.88-.73 2.088-1.146 3.396-1.324 1.242-.168 2.463-.102 3.631.196.034-1.165-.06-2.057-.393-2.73-.363-.73-1.013-1.17-1.93-1.323-.697-.116-1.432-.053-2.073.178l-.567-1.905c.93-.333 1.98-.44 2.964-.306 1.532.207 2.71.92 3.4 2.06.513.85.74 1.9.758 3.343.018 1.524-.214 2.685-.713 3.584-.663 1.193-1.69 1.975-3.04 2.323-.91.234-1.957.23-2.992-.012.044.453.223.847.535 1.148.51.494 1.3.732 2.288.692 1.188-.06 2.098-.467 2.709-1.21.64-.779.998-1.925 1.066-3.407l.025-.542 2.106.078-.025.585c-.097 2.14-.71 3.891-1.82 5.198C18.647 23.078 16.528 23.98 13.7 24h-.007z"/></svg></a>
            <a href="javascript:void(0)" onclick="copyLink()" title="링크복사" style="background:#6B7280;"><svg style="width:20px;height:20px;fill:white;" viewBox="0 0 24 24"><path d="M7.024 3.75c0-.966.784-1.75 1.75-1.75H20.25c.966 0 1.75.784 1.75 1.75v11.498a1.75 1.75 0 01-1.75 1.75H8.774a1.75 1.75 0 01-1.75-1.75V3.75zm1.75-.25a.25.25 0 00-.25.25v11.498c0 .139.112.25.25.25H20.25a.25.25 0 00.25-.25V3.75a.25.25 0 00-.25-.25H8.774z"/></svg></a>
            <a href="javascript:void(0)" onclick="addToHomeScreen()" title="홈화면 추가" style="background:#3B82F6;"><svg style="width:20px;height:20px;fill:white;" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg></a>
        </div>
    </header>
    
    <nav class="nav">
        <a href="/" class="nav-btn">🏠 홈</a>
        <a href="archive.html" class="nav-btn">🗂️ 자동 아카이브</a>
        <a href="https://news-keyword-pro.onrender.com" class="nav-btn" target="_blank">🔍 수동검색</a>
    </nav>
    
    <main class="container">
        <div class="count-box">
            <strong>{total_files}</strong>개의 수동 분석 결과가 저장되어 있습니다.
        </div>
        <ul class="archive-list">
            {file_list}
        </ul>
    </main>
    
    <footer class="footer">
        <p>🤖 Powered by GPT-4o-mini & Naver API</p>
    </footer>
    <script>
        function shareKakao() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent(document.title);
            if (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
                window.location.href = 'kakaolink://send?text=' + text + '&url=' + url;
                setTimeout(() => { window.open('https://sharer.kakao.com/talk/friends/picker/link?url=' + decodeURIComponent(url), '_blank'); }, 1000);
            } else {
                window.open('https://sharer.kakao.com/talk/friends/picker/link?url=' + decodeURIComponent(url), '_blank', 'width=600,height=400');
            }
        }
        function shareNaver() {
            const url = encodeURIComponent(window.location.href);
            const title = encodeURIComponent(document.title);
            window.open('https://share.naver.com/web/shareView?url=' + url + '&title=' + title, '_blank', 'width=600,height=400');
        }
        function shareLine() {
            const url = encodeURIComponent(window.location.href);
            window.open('https://social-plugins.line.me/lineit/share?url=' + url, '_blank', 'width=600,height=400');
        }
        function shareFacebook() {
            const url = encodeURIComponent(window.location.href);
            window.open('https://www.facebook.com/sharer/sharer.php?u=' + url, '_blank', 'width=600,height=400');
        }
        function shareTwitter() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent(document.title);
            window.open('https://twitter.com/intent/tweet?url=' + url + '&text=' + text, '_blank', 'width=600,height=400');
        }
        function shareThreads() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent(document.title);
            window.open('https://www.threads.net/intent/post?text=' + text + ' ' + url, '_blank', 'width=600,height=400');
        }
        function copyLink() {
            navigator.clipboard.writeText(window.location.href).then(() => { alert('링크가 복사되었습니다!'); });
        }
        function addToHomeScreen() {
            alert('브라우저 메뉴에서 "홈 화면에 추가"를 선택하세요!\n\niPhone: 공유 버튼 → 홈 화면에 추가\nAndroid: 메뉴 → 홈 화면에 추가');
        }
    </script>
</body>
</html>"""
    
    with open("output/manual-archive.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"    ✅ 수동 아카이브 생성 완료 ({total_files}개)")


