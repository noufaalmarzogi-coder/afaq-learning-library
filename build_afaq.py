#!/usr/bin/env python3
"""Run in GitHub Actions: copy public source game repositories into afaq-learning-library.
Original repos are only cloned/read, never written to.
"""
from pathlib import Path
import subprocess, tempfile, shutil, re, json
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'games'
SOURCES=[
 ('little-chick-adventure','grade3-reading','3','reading','مغامرة الفرخ الصغير','🐥'),
 ('math-adventure-grade3.','grade3-math','3','math','مغامرة كنز الأرقام','🔢'),
 ('reading-adventure-grade6','grade6-reading','6','reading','مغامرة أسرار الكلمات','📖'),
 ('math-stars-grade6','grade6-math','6','math','مغامرة نجمات الرياضيات','⭐'),
 ('science-discovery-grade6','grade6-science','6','science','مغامرة العلوم','🔬'),
]
WORDS=['الأولى','الثانية','الثالثة','الرابعة','الخامسة','السادسة','السابعة']
LABELS=['الإذاعة الصباحية','الإذاعة','الحصة الأولى','الحصة الثانية','الحصة الثالثة','الحصة الرابعة','الحصة الخامسة','الحصة السادسة']

def change_html(s,grade,subject):
    # Remove program-identification components, not questions, audio, scripts or layout.
    s=re.sub(r'<div class="initiative">.*?</div>', f'<div class="initiative">مكتبة أفق التعلّم • الصف {"الثالث" if grade=="3" else "السادس"} الابتدائي</div>',s,flags=re.S)
    s=re.sub(r'<div class="program-credit"[^>]*>.*?(?=<button class="sound")', '<div class="program-credit"><div class="program-name">مكتبة أفق التعلّم</div><div class="program-author">إعداد وتصميم: نوف البقمي</div></div>',s,flags=re.S)
    # Keep the educator's own author credit; drop only old initiative leadership banner where present.
    s=re.sub(r'<div class="cover-credits">.*?</div>\s*</div>', '',s,flags=re.S)
    for i,word in enumerate(WORDS):
        if i==0:
            s=s.replace('الإذاعة الصباحية',f'المرحلة {word}').replace('الإذاعة',f'المرحلة {word}')
        else:
            s=s.replace('الحصة '+WORDS[i-1],f'المرحلة {word}')
    s=s.replace('برنامج اليوم الواحد لنافس','مكتبة أفق التعلّم').replace('كلنا داعمون','أفق التعلّم').replace('جسور التعلم والتواصل','أفق التعلّم')
    # Prevent original localStorage progress from being shared with the independent version.
    s=re.sub(r'([\"\'])duck_v2\1', '"afaq_duck_v1"', s)
    return s

def main():
    records=[]
    with tempfile.TemporaryDirectory() as d:
        for repo,folder,grade,subject,title,emoji in SOURCES:
            src=Path(d)/folder
            try:
                subprocess.run(['git','clone','--depth','1','--quiet',f'https://github.com/noufaalmarzogi-coder/{repo}.git',str(src)],check=True,timeout=150)
                valid=(src/'index.html')
                if not valid.exists() or valid.stat().st_size<5000:
                    valid=src/'test.html'
                if not valid.exists() or valid.stat().st_size<5000:
                    print('SKIP no usable HTML:',repo)
                    continue
                dest=TARGET/folder
                dest.mkdir(parents=True,exist_ok=True)
                for child in src.iterdir():
                    if child.name=='.git':continue
                    if child.is_file():shutil.copy2(child,dest/child.name)
                    elif child.is_dir():shutil.copytree(child,dest/child.name,dirs_exist_ok=True)
                html=change_html(valid.read_text(encoding='utf-8'),grade,subject)
                # Ensure default entrypoint has the game actually selected.
                (dest/'index.html').write_text(html,encoding='utf-8')
                if 'كلنا داعمون' in html or 'الحصة الأولى' in html or 'الإذاعة الصباحية' in html:
                    raise ValueError('Unmodified labels remain in '+repo)
                records.append(dict(grade=grade,subject=subject,title=title,desc='لعبة تعليمية تفاعلية',emoji=emoji,url=f'games/{folder}/'))
                print('PREPARED:',repo,'->',folder)
            except Exception as exc:print('SKIP:',repo,str(exc))
    if not records:raise SystemExit('No games could be prepared; original library left intact')
    index=ROOT/'index.html'
    html=index.read_text(encoding='utf-8')
    html,n=re.subn(r'const DATA=\[.*?\];\s*// قائمة الألعاب التعليمية عند إضافتها للمكتبة\.',lambda m:'const DATA='+json.dumps(records,ensure_ascii=False,separators=(',',':'))+'; // قائمة الألعاب التعليمية عند إضافتها للمكتبة.',html,count=1,flags=re.S)
    if n!=1:raise SystemExit('Library format changed; index.html not replaced')
    index.write_text(html,encoding='utf-8')
    print('AVAILABLE GAMES:',len(records))
if __name__=='__main__':main()
