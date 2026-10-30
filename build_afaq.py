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
    # Standalone-library edition: the library card is the single entry point.
    # Hide (rather than destroy) start-page nodes if event handlers still reference them.
    if subject=='reading' and grade=='3':
        s=s.replace('id="gameWrap" style="display:none"','id="gameWrap" style="display:block"')
        s=s.replace('</style>', '#landing{display:none!important}#gameWrap{display:block!important}</style>',1)
        # Keep the hidden start element for its pre-existing click handler.
    elif subject=='math' and grade=='3':
        s=s.replace('id="gameMain" style="display:none"','id="gameMain" style="display:block"')
        s=s.replace('</style>', '#landing{display:none!important}#gameMain{display:block!important}</style>',1)
        # Seven clear sequential stages, rather than a stage zero microphone or lesson labels.
        s=s.replace('i===0?"🎤 المرحلة الأولى":"الحصة "+["","الأولى","الثانية","الثالثة","الرابعة","الخامسة","السادسة"][i]',
                    '"المرحلة "+["الأولى","الثانية","الثالثة","الرابعة","الخامسة","السادسة","السابعة"][i]')
        s=s.replace('سؤالان في المرحلة الأولى، ثم سؤالان بعد كل حصة.', 'سؤالان في كل مرحلة من المراحل السبع.')
    elif subject=='math' and grade=='6':
        # Preserve the audio button by moving it out of the decorative hero.
        m=re.search(r'<button class="sound" id="soundBtn"[^>]*>.*?</button>',s,re.S)
        if m:
            button=m.group(0)
            s=re.sub(r'<section class="hero">.*?</section>', '', s, count=1, flags=re.S)
            s=s.replace('<h2 class="stage-heading"', '<div class="library-sound">'+button+'</div><h2 class="stage-heading"',1)
    # Other games: remove only the clearly isolated introductory panel when identifiable.
    if grade=='6' and subject in ('reading','science'):
        s=re.sub(r'<div class="program-credit"[^>]*>.*?</div>\s*</div>', '',s,count=1,flags=re.S)
        s=re.sub(r'<div class="cover-credits"[^>]*>.*?</div>\s*</div>', '',s,count=1,flags=re.S)
    # Avoid duplicated library and author attribution in all five game copies.
    s=re.sub(r'<div class="initiative">.*?</div>', '',s,flags=re.S)
    s=re.sub(r'<div class="program-credit">.*?</div>\s*</div>', '',s,flags=re.S)
    s=re.sub(r'<div class="credit author">.*?</div>', '',s,flags=re.S)
    # Remove explicit radio/lesson labels without altering any questions or their answers.
    for i,word in enumerate(WORDS):
        if i==0:
            s=s.replace('🎤 المرحلة الأولى','المرحلة الأولى')
        else:
            s=s.replace('الحصة '+WORDS[i-1], 'المرحلة '+word)
    s=s.replace('بعد كل حصة','في كل مرحلة').replace('الإذاعة الصباحية','المرحلة الأولى').replace('الإذاعة','المرحلة الأولى')
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
