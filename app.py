from flask import Flask, render_template, request, jsonify
import sys
import os
import re
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
        
        if re.match(r'^\d+\s+', line):
            line = re.sub(r'^\d+\s+', '', line).strip()
        
        if len(line) > 20:
            continue
        
        if line and len(line) >= 2:
            sentences.append(line)
    
    sentences = list(dict.fromkeys(sentences))
    
    if not sentences:
        return jsonify({'error': '유효한 키워드가 없습니다.'})
    
    print(f"📝 {len(sentences)}개 키워드 정제됨")
    print(f"    → {sentences[:5]}...")
    
    all_keywords = list(set(sentences))
    print(f"�� {len(all_keywords)}개 키워드 분석 시작")
    
    # 직접 분석
    results = analyze_direct(all_keywords)
    print(f"✅ {len(results)}개 키워드 분석 완료")
    
    # 연관검색어 조회 (상위 10개)
    related_data = []
    for item in results[:10]:
        related = get_autocomplete(item['keyword'])
        related_data.append({
            'keyword': item['keyword'],
            'related': related[:5]
        })
    
    # 아카이브 저장 제거 - 화면에만 표시 (휘발)
    
    return jsonify({
        'success': True,
        'total_keywords': len(all_keywords),
        'results': results,
        'related': related_data,
        'archive': None  # 저장 안 함
    })


def analyze_direct(keywords):
    """입력 키워드만 직접 분석 (필터링 없음)"""
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
    
    print(f"    ✅ {len(filtered_volumes)}개 키워드 분석 대상")
    
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
