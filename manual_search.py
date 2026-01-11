#!/usr/bin/env python3
"""로컬 수동검색 - 결과를 pending 폴더에 저장 (push 안 함)"""

import os
import re
from datetime import datetime, timezone, timedelta
from src.naver_api import get_search_volume, get_blog_count, get_autocomplete
from dotenv import load_dotenv

load_dotenv()

def analyze_keywords(keywords):
    """키워드 분석"""
    print(f"    🔍 {len(keywords)}개 키워드 검색량 조회 중...")
    search_volumes = get_search_volume(keywords)
    
    filtered_volumes = {}
    for kw in keywords:
        kw_clean = kw.replace(" ", "")
        for api_kw, volume in search_volumes.items():
            if api_kw.replace(" ", "") == kw_clean:
                filtered_volumes[kw] = volume
                break
        if kw not in filtered_volumes:
            filtered_volumes[kw] = 0
    
    results = []
    count = 0
    for keyword, monthly in filtered_volumes.items():
        count += 1
        blog_count = get_blog_count(keyword)
        
        if monthly > 0:
            saturation = round(blog_count / monthly, 2)
        else:
            saturation = 0
        
        if blog_count <= 1000:
            possibility = "🟢"
        elif blog_count <= 10000:
            possibility = "🟡"
        elif blog_count <= 50000:
            possibility = "🟠"
        else:
            possibility = "🔴"
        
        results.append({
            'keyword': keyword,
            'monthly_search': monthly,
            'blog_count': blog_count,
            'saturation': saturation,
            'possibility': possibility
        })
        
        if count % 10 == 0:
            print(f"    ⏳ {count}개 분석 중...")
    
    return sorted(results, key=lambda x: x['blog_count'])


def save_to_pending(title, results, related_data):
    """pending 폴더에 저장 (push 안 함)"""
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d_%H-%M")
    update_time = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    
    # 파일명 생성
    import hashlib
    title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
    filename = f"{date_str}_manual_{title_hash}.html"
    
    # pending 폴더 생성
    pending_dir = "output/pending"
    os.makedirs(pending_dir, exist_ok=True)
    
    # 테이블 행 생성
    table_rows = ""
    for idx, item in enumerate(results, 1):
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
            <td><a href="{naver_url}" target="_blank" class="search-link">🔍</a></td>
        </tr>"""
    
    # 연관검색어 HTML
    related_html = ""
    for item in related_data:
        related_list = "".join([
            f'<li><a href="https://search.naver.com/search.naver?query={kw}" target="_blank">{kw}</a></li>'
            for kw in item['related']
        ]) or '<li>연관검색어 없음</li>'
        related_html += f"""
        <div class="related-card">
            <h4>{item['keyword']}</h4>
            <ul>{related_list}</ul>
        </div>"""
    
    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 {title} - 수동분석</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #1e3a8a; --green: #10b981; --bg: #f0f4ff; --card-bg: #ffffff; --text: #1f2937; --border: #e5e7eb; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Noto Sans KR', sans-serif; background: var(--bg); min-height: 100vh; color: var(--text); line-height: 1.7; }}
        .header {{ background: linear-gradient(135deg, var(--primary) 0%, #1e40af 100%); padding: 2rem; text-align: center; color: white; }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .nav {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; padding: 1rem; background: white; border-bottom: 1px solid var(--border); }}
        .nav-btn {{ padding: 8px 16px; border-radius: 20px; text-decoration: none; color: var(--text); background: var(--bg); font-size: 0.9rem; }}
        .nav-btn:hover {{ background: var(--primary); color: white; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        .card {{ background: var(--card-bg); border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .card h2 {{ color: var(--primary); margin-bottom: 1rem; }}
        .keyword-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .keyword-table th, .keyword-table td {{ border: 1px solid var(--border); padding: 12px 8px; text-align: center; }}
        .keyword-table th {{ background: var(--primary); color: white; cursor: pointer; }}
        .keyword-table th:hover {{ background: #1e40af; }}
        .keyword-table tr:nth-child(even) {{ background: #f9fafb; }}
        .keyword-table td:nth-child(2) {{ text-align: left; }}
        .search-link {{ display: inline-block; padding: 4px 10px; background: var(--green); color: white; border-radius: 4px; text-decoration: none; }}
        .related-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }}
        .related-card {{ background: #f8f9fa; border-radius: 8px; padding: 1rem; border: 1px solid var(--border); }}
        .related-card h4 {{ margin-bottom: 0.5rem; color: var(--primary); }}
        .related-card ul {{ list-style: none; }}
        .related-card a {{ color: var(--text); text-decoration: none; }}
        .footer {{ background: var(--primary); color: white; text-align: center; padding: 1.5rem; margin-top: 3rem; }}
    </style>
</head>
<body>
    <header class="header">
        <h1>🔍 {title}</h1>
        <p>수동 키워드 분석 결과</p>
        <small>📅 {update_time}</small>
    </header>
    <nav class="nav">
        <a href="../index.html" class="nav-btn">🏠 홈</a>
        <a href="../archive.html" class="nav-btn">🗂️ 아카이브</a>
        <a href="../manual-archive.html" class="nav-btn">📁 수동아카이브</a>
    </nav>
    <main class="container">
        <section class="card">
            <h2>📊 분석 결과 ({len(results)}개 키워드)</h2>
            <table class="keyword-table">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>키워드</th>
                        <th>월간검색량</th>
                        <th>블로그문서수</th>
                        <th>포화도</th>
                        <th>난이도</th>
                        <th>검색</th>
                    </tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </section>
        <section class="card">
            <h2>🔗 연관 검색어</h2>
            <div class="related-grid">{related_html}</div>
        </section>
    </main>
    <footer class="footer">
        <p>🤖 Powered by Naver API</p>
    </footer>
</body>
</html>"""
    
    filepath = os.path.join(pending_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filepath


def main():
    print("=" * 60)
    print("🔍 로컬 수동 키워드 검색")
    print("=" * 60)
    print("\n키워드를 입력하세요 (한 줄에 하나씩, 빈 줄 입력 시 종료):\n")
    
    keywords = []
    while True:
        line = input()
        if not line.strip():
            break
        # 순위 숫자 제거
        clean = re.sub(r'^\d+\s+', '', line.strip())
        if clean and len(clean) >= 2 and len(clean) <= 20:
            keywords.append(clean)
    
    if not keywords:
        print("❌ 입력된 키워드가 없습니다.")
        return
    
    keywords = list(dict.fromkeys(keywords))  # 중복 제거
    print(f"\n📝 {len(keywords)}개 키워드 분석 시작...")
    
    # 분석
    results = analyze_keywords(keywords)
    
    # 연관검색어
    print(f"\n🔗 연관검색어 조회 중...")
    related_data = []
    for item in results[:10]:
        related = get_autocomplete(item['keyword'])
        related_data.append({
            'keyword': item['keyword'],
            'related': related[:5]
        })
    
    # 저장
    title = ", ".join(keywords[:2]) if keywords else "수동분석"
    filepath = save_to_pending(title, results, related_data)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 분석 완료! {len(results)}개 키워드")
    print(f"📁 저장 위치: {filepath}")
    print(f"{'=' * 60}")
    print(f"\n💡 나중에 push하려면:")
    print(f"   python publish_pending.py")


if __name__ == "__main__":
    main()
