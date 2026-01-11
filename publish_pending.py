#!/usr/bin/env python3
"""pending 폴더의 수동검색 결과를 archive로 이동하고 push"""

import os
import shutil
from pathlib import Path

def main():
    pending_dir = Path("output/pending")
    archive_dir = Path("output/archive")
    
    if not pending_dir.exists():
        print("❌ output/pending 폴더가 없습니다.")
        return
    
    files = list(pending_dir.glob("*.html"))
    
    if not files:
        print("📭 pending 폴더에 파일이 없습니다.")
        return
    
    print(f"📁 {len(files)}개 파일 발견:\n")
    for f in files:
        print(f"   - {f.name}")
    
    print(f"\n이 파일들을 archive로 이동하고 push할까요? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm != 'y':
        print("❌ 취소되었습니다.")
        return
    
    # archive 폴더로 이동
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for f in files:
        dest = archive_dir / f.name
        shutil.move(str(f), str(dest))
        print(f"   ✅ {f.name} → archive/")
    
    print(f"\n📤 Git push 중...")
    
    os.system("git add -A")
    os.system(f'git commit -m "수동검색 {len(files)}개 아카이브 추가"')
    os.system("git push")
    
    print(f"\n{'=' * 60}")
    print(f"✅ 완료! {len(files)}개 파일이 archive에 추가되었습니다.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
