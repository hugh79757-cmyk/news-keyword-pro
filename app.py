from flask import Flask, render_template, request, jsonify
import sys
import os
import re
import base64
from datetime import datetime, timezone, timedelta

from src.naver_api import get_search_volume, get_blog_count, get_autocomplete
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='output')

@app.route('/')
def index():
    return render_template('manual.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    raw_text = data.get('sentences', [])
    
    if not raw_text:
        return jsonify({'error': '입력된 문장이 없습니다.'})
    
    # 정제
    sentences = []
    for line in raw_text:
        line = line.strip()
        
        skip_patterns = [
            r'^\d+$',
            r'^\d{4}년',
            r'^daum$', r'^zum$', r'^nate$', r'^googletrend$',
            r'실시간 검색어',
            r'기준$',
            r'🔍',
            r'\d+,\d+',
            r'^\d+\s+\d+',
        ]
        
        skip = False
        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                skip = True
                break
        
        if skip or len(line) < 2:
            continue
        
        # 순위 숫자만 제거 (숫자 + 공백이 있을 때만)
        if re.match(r'^\d+\s+', line):
            line = re.sub(r'^\d+\s+', '', line).strip()
        
        # 20자 초과하면 제외
        if len(line) > 20:
            continue
        
        if line and len(line) >= 2:
            sentences.append(line)
    
    sentences = list(dict.fromkeys(sentences))
    
    if not sentences:
        return jsonify({'error': '유효한 키워드가 없습니다.'})
    
    title_keywords = sentences[:2]
    
    print(f"📝 {len(sentences)}개 키워드 정제됨")
    print(f"    → {sentences[:5]}...")
    
        # 롱테일 비활성화 - 입력 키워드만 사용
    all_keywords = list(set(sentences))
    print(f"📝 {len(all_keywords)}개 키워드 분석 시작")

    
    # 3. 직접 분석 (연관 키워드 제외)
    results = analyze_direct(all_keywords)
    
    
     # 필터링 없이 모든 결과 표시
    print(f"✅ {len(results)}개 키워드 분석 완료")

    
    # 4. 연관검색어 조회 (상위 10개)
    related_data = []
    for item in results[:10]:
        related = get_autocomplete(item['keyword'])
        related_data.append({
            'keyword': item['keyword'],
            'related': related[:5]
        })
    
    # 5. 아카이브 저장
    archive_path = save_manual_archive(title_keywords, results, related_data)
    print(f"📁 아카이브 저장: {archive_path}")
    
    return jsonify({
        'success': True,
        'total_keywords': len(all_keywords),
        'results': results,
        'related': related_data,
        'archive': archive_path
    })



def analyze_direct(keywords):
    """입력 키워드만 직접 분석 (필터링 없음)"""
    print(f"    🔍 {len(keywords)}개 키워드 검색량 조회 중...")
    search_volumes = get_search_volume(keywords)
    
    # 입력 키워드 우선 포함
    filtered_volumes = {}
    for kw in keywords:
        kw_clean = kw.replace(" ", "")
        for api_kw, volume in search_volumes.items():
            if api_kw.replace(" ", "") == kw_clean:
                filtered_volumes[kw] = volume
                break
        if kw not in filtered_volumes:
            filtered_volumes[kw] = 0
    
    print(f"    ✅ {len(filtered_volumes)}개 키워드 분석 대상")
    
    results = []
    count = 0
    for keyword, monthly in filtered_volumes.items():
        # 필터링 제거 - 모든 키워드 분석
        count += 1
        blog_count = get_blog_count(keyword)
        
        if monthly > 0:
            saturation = round(blog_count / monthly, 2)
        else:
            saturation = 0
        
        # 난이도 판정 (블로그 문서수 기준)
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
    
    # 블로그 문서수 기준 정렬 (적은 순)
    return sorted(results, key=lambda x: x['blog_count'])




def generate_longtail(keywords):
    """AI로 블로그 상위노출 가능한 틈새 키워드 추천"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("    ⚠️ OPENAI_API_KEY 없음")
        return []
    
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    keywords_text = "\n".join([f"- {kw}" for kw in keywords])
    
    prompt = f"""당신은 네이버 블로그 SEO 전문가입니다.

다음 키워드들에 대해 블로그 상위노출이 가능한 틈새 키워드를 추천해주세요.

입력 키워드:
{keywords_text}

규칙:
1) 검색량은 있지만 블로그 경쟁이 적을 것 같은 키워드
2) 반드시 입력 키워드를 포함해야 함
3) 3~4단어 롱테일 키워드 (예: 임영웅콘서트일정2026)
4) 구체적인 정보성 키워드 사용 (방법, 후기, 비용, 순위, 가격, 일정, 예약, 신청 등)
5) 각 키워드당 5개 생성
6) 띄어쓰기 없이 붙여쓰기
7) 키워드만 출력 (설명 금지)

예시:
입력: 임영웅
출력: 임영웅콘서트일정2026, 임영웅팬미팅예약방법, 임영웅굿즈구매후기, 임영웅신곡가사해석, 임영웅공연티켓가격

입력: 그린란드
출력: 그린란드트럼프합병이유, 그린란드미국영토편입, 그린란드독립찬반여론, 그린란드자원매장량, 그린란드덴마크관계

잘못된 예시 (이렇게 하지 마세요):
- 콘서트일정 (입력 키워드 없음)
- 임영웅 (너무 짧음)
- 임영웅이 최근 콘서트를 발표했습니다 (문장 금지)"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.4
        )
        
        content = response.choices[0].message.content.strip()
        
        # 키워드만 필터링
        raw_keywords = [kw.strip() for kw in content.split(",") if kw.strip()]
        longtail = [kw for kw in raw_keywords if len(kw) <= 25 and " " not in kw and len(kw) >= 5]
        
        print(f"    ✅ AI 추천 키워드: {longtail[:10]}...")
        return longtail
        
    except Exception as e:
        print(f"    ⚠️ AI 키워드 추천 오류: {e}")
        return []




def save_manual_archive(title_keywords, results, related_data):
    """수동 분석 결과 아카이브 저장"""
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d_%H-%M")
    update_time = now.strftime("%Y년 %m월 %d일 %H시 %M분")
    
    title_text = ", ".join(title_keywords) if title_keywords else "수동분석"
    safe_title = re.sub(r'[^\w가-힣\s]', '', title_text)[:30]
    
    filename = f"{date_str}_manual_{safe_title}.html"
    
    archive_dir = "output/archive"
    os.makedirs(archive_dir, exist_ok=True)
    
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
        </tr>
        """
    
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
        </div>
        """
    
    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 {title_text} - 수동분석</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #1e3a8a; --green: #10b981; --bg: #f0f4ff; --card-bg: #ffffff; --text: #1f2937; --border: #e5e7eb; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Noto Sans KR', sans-serif; background: var(--bg); min-height: 100vh; color: var(--text); line-height: 1.7; }}
        .header {{ background: linear-gradient(135deg, var(--primary) 0%, #1e40af 100%); padding: 2rem; text-align: center; color: white; }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .nav-buttons {{ display: flex; justify-content: center; gap: 1rem; padding: 1rem; background: var(--card-bg); border-bottom: 1px solid var(--border); flex-wrap: wrap; }}
        .nav-btn {{ padding: 10px 20px; background: var(--primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 500; }}
        .nav-btn:hover {{ background: #1e40af; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        .card {{ background: var(--card-bg); border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .card h2 {{ color: var(--primary); margin-bottom: 1rem; }}
        .keyword-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .keyword-table th, .keyword-table td {{ border: 1px solid var(--border); padding: 12px 8px; text-align: center; }}
        .keyword-table th {{ background: var(--primary); color: white; cursor: pointer; user-select: none; }}
        .keyword-table th:hover {{ background: #1e40af; }}
        .keyword-table th::after {{ content: ' ↕'; opacity: 0.5; }}
        .keyword-table th.sort-asc::after {{ content: ' ↑'; opacity: 1; }}
        .keyword-table th.sort-desc::after {{ content: ' ↓'; opacity: 1; }}
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
        <h1>🔍 {title_text}</h1>
        <p>수동 키워드 분석 결과</p>
        <small>📅 {update_time}</small>
    </header>
    <nav class="nav-buttons">
        <a href="https://news-keyword-pro.onrender.com" class="nav-btn">🔍 새 분석</a>
        <a href="https://8.informationhot.kr/manual-archive.html" class="nav-btn">📁 수동아카이브</a>
        <a href="https://8.informationhot.kr/" class="nav-btn">🏠 홈</a>
    </nav>
    <main class="container">
        <section class="card">
            <h2>📊 분석 결과 ({len(results)}개 키워드)</h2>
            <table class="keyword-table" id="keywordTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">순위</th>
                        <th onclick="sortTable(1)">키워드</th>
                        <th onclick="sortTable(2)">월간검색량</th>
                        <th onclick="sortTable(3)">블로그문서수</th>
                        <th onclick="sortTable(4)">포화도</th>
                        <th onclick="sortTable(5)">난이도</th>
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
        <p>🤖 Powered by GPT-4o-mini & Naver API</p>
    </footer>
    <script>
        function sortTable(columnIndex) {{
            const table = document.getElementById('keywordTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headers = table.querySelectorAll('th');
            const currentOrder = table.dataset.sortOrder;
            const currentColumn = table.dataset.sortColumn;
            let newOrder = 'asc';
            if (currentColumn == columnIndex && currentOrder === 'asc') {{ newOrder = 'desc'; }}
            rows.sort((a, b) => {{
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();
                const aNum = parseFloat(aVal.replace(/,/g, ''));
                const bNum = parseFloat(bVal.replace(/,/g, ''));
                if (!isNaN(aNum) && !isNaN(bNum)) {{ return newOrder === 'asc' ? aNum - bNum : bNum - aNum; }}
                return newOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }});
            rows.forEach(row => tbody.appendChild(row));
            table.dataset.sortOrder = newOrder;
            table.dataset.sortColumn = columnIndex;
            headers.forEach((h, i) => {{
                h.classList.remove('sort-asc', 'sort-desc');
                if (i === columnIndex) {{ h.classList.add(newOrder === 'asc' ? 'sort-asc' : 'sort-desc'); }}
            }});
        }}
    </script>
</body>
</html>"""

    # 로컬 파일 저장
    filepath = os.path.join(archive_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    # GitHub에 아카이브 파일 저장
    github_url = save_to_github(filename, html)
    
    # manual-archive.html 목록 업데이트
    update_manual_archive_list()
    
    if github_url:
        return github_url
    return f"archive/{filename}"

def save_to_github(filename, content):
    """GitHub에 아카이브 파일 저장"""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    
    if not token or not repo:
        print("    ⚠️ GitHub 설정 없음, 로컬 저장만 진행")
        return None
    
    import requests as req
    
    path = f"output/archive/{filename}"
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 파일 존재 여부 확인
    response = req.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        sha = response.json().get("sha")
    
    # 파일 업로드
    data = {
        "message": f"아카이브 추가: {filename}",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
    
    response = req.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"    ✅ GitHub 저장 완료: {path}")
        return f"https://hugh79757-cmyk.github.io/news-keyword-pro/archive/{filename}"
    else:
        print(f"    ⚠️ GitHub 저장 실패: {response.status_code}")
        return None

    
    filepath = os.path.join(archive_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"archive/{filename}"

def update_manual_archive_list():
    """manual-archive.html 목록 자동 업데이트"""
    import glob
    
    archive_dir = "output/archive"
    files = glob.glob(f"{archive_dir}/*_manual_*.html")
    files.sort(reverse=True)  # 최신순
    
    if not files:
        print("    ⚠️ 수동분석 아카이브 파일 없음")
        return
    
    # 목록 HTML 생성
    list_items = ""
    for f in files[:50]:  # 최근 50개만
        filename = os.path.basename(f)
        parts = filename.replace(".html", "").split("_manual_")
        if len(parts) == 2:
            date_part = parts[0].replace("_", " ").replace("-", ".")
            title = parts[1]
            list_items += f'''
                <tr>
                    <td>{date_part}</td>
                    <td><a href="https://8.informationhot.kr/archive/{filename}">{title}</a></td>
                </tr>'''
    
    # 새 manual-archive.html 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📁 수동 분석 아카이브</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #1e3a8a; --bg: #f0f4ff; --card-bg: #ffffff; --text: #1f2937; --border: #e5e7eb; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Noto Sans KR', sans-serif; background: var(--bg); min-height: 100vh; color: var(--text); line-height: 1.7; }}
        .header {{ background: linear-gradient(135deg, var(--primary) 0%, #1e40af 100%); padding: 2rem; text-align: center; color: white; }}
        .header h1 {{ font-size: 1.8rem; }}
        .nav {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; padding: 1rem; background: white; border-bottom: 1px solid var(--border); }}
        .nav-btn {{ padding: 8px 16px; border-radius: 20px; text-decoration: none; color: var(--text); background: var(--bg); font-size: 0.9rem; }}
        .nav-btn:hover, .nav-btn.active {{ background: var(--primary); color: white; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 2rem 1rem; }}
        .card {{ background: var(--card-bg); border-radius: 16px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .card h2 {{ color: var(--primary); margin-bottom: 1rem; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid var(--border); padding: 12px; text-align: left; }}
        th {{ background: var(--primary); color: white; }}
        tr:nth-child(even) {{ background: #f9fafb; }}
        a {{ color: var(--primary); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{ background: var(--primary); color: white; text-align: center; padding: 1.5rem; margin-top: 3rem; }}
    </style>
</head>
<body>
    <header class="header">
        <h1>📁 수동 분석 아카이브</h1>
        <p>수동 키워드 분석 결과 모음</p>
    </header>
    <nav class="nav">
        <a href="https://8.informationhot.kr/" class="nav-btn">🏠 홈</a>
        <a href="https://8.informationhot.kr/stock.html" class="nav-btn">📈 증권/주식</a>
        <a href="https://8.informationhot.kr/realestate.html" class="nav-btn">🏠 부동산</a>
        <a href="https://8.informationhot.kr/finance.html" class="nav-btn">💰 금융</a>
        <a href="https://8.informationhot.kr/car.html" class="nav-btn">🚗 자동차</a>
        <a href="https://8.informationhot.kr/health.html" class="nav-btn">💊 건강/의료</a>
        <a href="https://8.informationhot.kr/tech.html" class="nav-btn">📱 IT/모바일</a>
        <a href="https://8.informationhot.kr/policy.html" class="nav-btn">🏛️ 정부정책</a>
        <a href="https://8.informationhot.kr/archive.html" class="nav-btn">📚 아카이브</a>
        <a href="https://8.informationhot.kr/manual-archive.html" class="nav-btn active">📁 수동아카이브</a>
        <a href="https://news-keyword-pro.onrender.com/" class="nav-btn">🔍 수동분석</a>
    </nav>
    <main class="container">
        <section class="card">
            <h2>📋 분석 결과 목록 ({len(files)}개)</h2>
            <table>
                <thead>
                    <tr>
                        <th>날짜</th>
                        <th>제목</th>
                    </tr>
                </thead>
                <tbody>{list_items}</tbody>
            </table>
        </section>
    </main>
    <footer class="footer">
        <p>🤖 Powered by GPT-4o-mini & Naver API</p>
    </footer>
</body>
</html>"""
    
    # 로컬 저장
    with open("output/manual-archive.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # GitHub에도 저장
    save_manual_archive_to_github(html)
    print("    ✅ manual-archive.html 목록 업데이트 완료")



def save_manual_archive_to_github(content):
    """manual-archive.html을 GitHub에 저장"""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    
    if not token or not repo:
        return
    
    import requests as req
    
    path = "output/manual-archive.html"
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 기존 파일 SHA 가져오기
    response = req.get(url, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None
    
    # 파일 업로드
    data = {
        "message": "수동아카이브 목록 업데이트",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
    
    req.put(url, headers=headers, json=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

