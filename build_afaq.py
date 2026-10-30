#!/usr/bin/env python3
"""Create independent game copies for Afaq library. Original repositories are read-only."""
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

# For large sixth-grade game HTML, preserve all handlers and assets. Activate the
# original start control on page load rather than deleting interactive DOM nodes.
AUTO_START = r'''<script id="afaq-auto-start">
(function(){
  if (window.__afaqAutoStartInstalled) return;
  window.__afaqAutoStartInstalled = true;
  let fired=false, attempts=0;
  const matches = el => {
    const t=(el.textContent||el.value||el.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim();
    return /^(?:▶\s*)?(?:ابدأ|ابدئي|إبدأ|إبدئي)\s*(?:اللعبة|اللعب|المغامرة|الرحلة|الآن)?\s*(?:▶|⏵|►)?$/u.test(t) ||
      /^(?:start\s*(?:game|playing|adventure)?|play)$/i.test(t);
  };
  function launch(){
    if(fired || attempts++ > 24) return;
    const selectors=['#startBtn','#startGameBtn','#btnStart','#playBtn',
      '.start-btn','.startBtn','.btn-start','.play-btn',
      '[data-action="start"]','button[onclick*="start"]',
      'a[onclick*="start"]'];
    const candidates=[...document.querySelectorAll(selectors.join(',')),
      ...document.querySelectorAll('button,a,[role="button"],input[type="button"]')];
    const el=candidates.find(x=>matches(x)) || candidates.find(x=>
      /^(?:start|play)(?:Game)?$/i.test(x.id||''));
    if(el){ fired=true; el.click(); return; }
    setTimeout(launch,250);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',launch,{once:true});
  else launch();
})();
</script>'''

def change_html(s,grade,subject):
    # Keep questions, sound and application scripts; remove duplicate textual attribution.
    s=re.sub(r'<div class="initiative">.*?</div>', '',s,flags=re.S)
    s=re.sub(r'<div class="program-credit"[^>]*>.*?(?=<button class="sound")', '',s,flags=re.S)
    s=re.sub(r'<div class="credit author">.*?</div>', '',s,flags=re.S)
    s=s.replace('برنامج اليوم الواحد لنافس','مكتبة أفق التعلّم').replace('كلنا داعمون','أفق التعلّم').replace('جسور التعلم والتواصل','أفق التعلّم')
    if subject=='reading' and grade=='3':
        s=s.replace('id="gameWrap" style="display:none"','id="gameWrap" style="display:block"')
        s=s.replace('</style>', '#landing{display:none!important}#gameWrap{display:block!important}</style>',1)
    elif subject=='math' and grade=='3':
        s=s.replace('id="gameMain" style="display:none"','id="gameMain" style="display:block"')
        s=s.replace('</style>', '#landing{display:none!important}#gameMain{display:block!important}</style>',1)
        s=s.replace('i===0?"🎤 المرحلة الأولى":"الحصة "+["","الأولى","الثانية","الثالثة","الرابعة","الخامسة","السادسة"][i]',
                    '"المرحلة "+["الأولى","الثانية","الثالثة","الرابعة","الخامسة","السادسة","السابعة"][i]')
        s=s.replace('سؤالان في المرحلة الأولى، ثم سؤالان بعد كل حصة.', 'سؤالان في كل مرحلة من المراحل السبع.')
    elif subject=='math' and grade=='6':
        m=re.search(r'<button class="sound" id="soundBtn"[^>]*>.*?</button>',s,re.S)
        if m:
            button=m.group(0)
            s=re.sub(r'<section class="hero">.*?</section>', '', s, count=1, flags=re.S)
            s=s.replace('<h2 class="stage-heading"', '<div class="library-sound">'+button+'</div><h2 class="stage-heading"',1)
    if grade=='6' and subject in ('reading','science'):
        # The original covers can be elaborate and their start listeners vary.
        # Trigger the original control to keep JS initialization intact.
        # Do not delete graphical cover nodes, which may contain game controls.
        if '</body>' in s:
            s=s.replace('</body>',AUTO_START+'\n</body>',1)
        else:
            s+=AUTO_START
    for i,word in enumerate(WORDS):
        if i==0:
            s=s.replace('🎤 المرحلة الأولى','المرحلة الأولى')
        else:
            s=s.replace('الحصة '+WORDS[i-1], 'المرحلة '+word)
    s=s.replace('بعد كل حصة','في كل مرحلة').replace('الإذاعة الصباحية','المرحلة الأولى').replace('الإذاعة','المرحلة الأولى')
    s=re.sub(r'(["\'])duck_v2\1', '"afaq_duck_v1"', s)
    return s

def main():
    records=[]
    with tempfile.TemporaryDirectory() as d:
        for repo,folder,grade,subject,title,emoji in SOURCES:
            src=Path(d)/folder
            try:
                subprocess.run(['git','clone','--depth','1','--quiet',f'https://github.com/noufaalmarzogi-coder/{repo}.git',str(src)],check=True,timeout=150)
                valid=src/'index.html'
                if not valid.exists() or valid.stat().st_size<5000:valid=src/'test.html'
                if not valid.exists() or valid.stat().st_size<5000:
                    print('SKIP no usable HTML:',repo);continue
                dest=TARGET/folder
                dest.mkdir(parents=True,exist_ok=True)
                for child in src.iterdir():
                    if child.name=='.git':continue
                    if child.is_file():shutil.copy2(child,dest/child.name)
                    elif child.is_dir():shutil.copytree(child,dest/child.name,dirs_exist_ok=True)
                html=change_html(valid.read_text(encoding='utf-8'),grade,subject)
                (dest/'index.html').write_text(html,encoding='utf-8')
                if 'كلنا داعمون' in html or 'الحصة الأولى' in html or 'الإذاعة الصباحية' in html:
                    raise ValueError('Unmodified labels remain in '+repo)
                records.append(dict(grade=grade,subject=subject,title=title,desc='لعبة تعليمية تفاعلية',emoji=emoji,url=f'games/{folder}/'))
                print('PREPARED:',repo,'->',folder)
            except Exception as exc:print('SKIP:',repo,str(exc))
    if not records:raise SystemExit('No games could be prepared; original library left intact')
    index=ROOT/'index.html'
    html=index.read_text(encoding='utf-8')
    html,n=re.subn(r'const DATA=\[.*?\];\s*//[^\n]*',lambda m:'const DATA='+json.dumps(records,ensure_ascii=False,separators=(',',':'))+'; // الألعاب المنشورة في أفق التعلّم.',html,count=1,flags=re.S)
    if n!=1:raise SystemExit('Library format changed; index.html not replaced')
    index.write_text(html,encoding='utf-8')
    print('AVAILABLE GAMES:',len(records))
if __name__=='__main__':main()
