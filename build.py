import re, json, collections, math, os, html
NASB='/Users/andersontao/Documents/nasb1996-cunp-interlaced-bible/assets/nasb/books'
BOOKS=[('Mat','Matthew',40),('Mrk','Mark',41),('Luk','Luke',42),('Jhn','John',43),('Act','Acts',44),('Rom','Romans',45),('1Co','1 Corinthians',46),('2Co','2 Corinthians',47),('Gal','Galatians',48),('Eph','Ephesians',49),('Php','Philippians',50),('Col','Colossians',51),('1Th','1 Thessalonians',52),('2Th','2 Thessalonians',53),('1Ti','1 Timothy',54),('2Ti','2 Timothy',55),('Tit','Titus',56),('Phm','Philemon',57),('Heb','Hebrews',58),('Jas','James',59),('1Pe','1 Peter',60),('2Pe','2 Peter',61),('1Jn','1 John',62),('2Jn','2 John',63),('3Jn','3 John',64),('Jud','Jude',65),('Rev','Revelation',66)]
abbr={a:(n,i) for a,n,i in BOOKS}
# imperatives: MorphGNT (SBLGNT) supplies positions/parse; TAGNT supplies contextual English glosses
import glob, unicodedata
def norm(w): return ''.join(c for c in unicodedata.normalize('NFD',w) if c.isalpha() and not unicodedata.combining(c)).lower().replace('ς','σ')
tg=collections.defaultdict(list); lemgloss={}
for f in ['data/tagnt-mat-jhn.txt','data/tagnt-act-rev.txt']:
    for l in open(f,encoding='utf8'):
        m=re.match(r'^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)(?:\{[^}]*\})?#(\d+)=(\w+)\t',l)
        if not m or m.group(1) not in abbr: continue
        p=l.split('\t')
        if len(p)<5: continue
        g=re.sub(r'\s*\(.*\)','',p[1]).strip(); tr=re.search(r'\((.*)\)',p[1])
        lm,_,lg=p[4].partition('=')
        lemgloss.setdefault(norm(lm),lg)
        tg[(m.group(1),int(m.group(2)),int(m.group(3)))].append((norm(g),p[2],tr.group(1) if tr else ''))
ab=[a for a,_,_ in BOOKS]
imps=collections.defaultdict(list)
for f in sorted(glob.glob('data/morphgnt/*.txt')):
    for l in open(f,encoding='utf8'):
        p=l.split()
        if p[2][3]!='D': continue
        k=(ab[int(p[0][:2])-1],int(p[0][2:4]),int(p[0][4:]))
        w=norm(p[5]); gl='';tr=''
        for n,g,t in tg.get(k,[]):
            if n==w: gl=g;tr=t;break
        lg=lemgloss.get(norm(p[6]),'')
        pr=p[2]; parse=('Pres' if pr[1]=='P' else 'Aor' if pr[1]=='A' else 'Perf' if pr[1]=='X' else pr[1])+' '+pr[2]+' Imp '+pr[0]+('sg' if pr[5]=='S' else 'pl')
        imps[k].append(dict(greek=re.sub(r'[^\w]','',p[3]),tr=tr,gloss=gl,lemma=norm(p[6]),lg=lg,strong='',parse=parse))
# load NASB
verses={}
for a,n,b in BOOKS:
    d=f'{NASB}/{b}'
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json') and fn!='book.json':
            for v in json.load(open(f'{d}/{fn}',encoding='utf8')): verses[(a,v['chapter'],v['verse'])]=v['text']
STOP=set('do not a an the to of be is are am was were you your he him his she her it they them their we us our let must shall will would should can may might and or but in on at by for with from that this these those then also just only never so if as who whom which what'.split())
def stem(w):
    w=w.lower().replace('’',"'")
    if w.endswith("'s"): w=w[:-2]
    for s_ in ('ing','ied','ies','ed','es','s','d'):
        if w.endswith(s_) and len(w)-len(s_)>=3:
            w=w[:-len(s_)]; break
    if w.endswith('e') and len(w)>3: w=w[:-1]
    if len(w)>3 and w[-1]==w[-2]: w=w[:-1]
    return w
IRREG={'go':['went','gone','goes'],'come':['came'],'give':['gave','given'],'take':['took','taken'],'see':['saw','seen'],'know':['knew','known'],'say':['said'],'speak':['spoke'],'be':['was'],'get':['got'],'hear':['heard'],'keep':['kept'],'leave':['left'],'rise':['arose','risen','rose'],'stand':['stood'],'sit':['sat'],'bring':['brought'],'think':['thought'],'lay':['laid'],'put':['put'],'flee':['fled'],'run':['ran'],'write':['wrote','written'],'drink':['drank'],'eat':['ate','eaten'],'send':['sent'],'tell':['told'],'find':['found'],'hold':['held'],'seek_':['sought'],'build':['built'],'sell':['sold'],'bind':['bound'],'wake':['awake','awoke'],'stay':['abide','remain'],'fear':['afraid'],'love':['beloved']}
def tok(t): return [(m.group(0),m.start(),m.end()) for m in re.finditer(r"[A-Za-z]+(?:['’][A-Za-z]+)*",t)]
# lemma association
tot=collections.Counter(); N=0
vt={}
for k,t in verses.items():
    s=set(stem(w) for w,_,_ in tok(t)); vt[k]=s; N+=1
    for x in s: tot[x]+=1
lemv=collections.defaultdict(list)
for k,L in imps.items():
    for i in L: lemv[i['lemma']].append(k)
assoc={}
for lem,ks in lemv.items():
    c=collections.Counter()
    for k in set(ks):
        for x in vt.get(k,()): c[x]+=1
    n=len(set(ks))
    assoc[lem]={x:(v/n)/(tot[x]/N) for x,v in c.items() if v>=2 and v/n>=0.25 and (v/n)/(tot[x]/N)>3} if n>=3 else {}
PRE={'do','not','never','let','also','just','only','must','don’t',"don't",'just'}
PRON={'him','her','them','us','it','me'}
BAD={'say','said','answer','repli','speak','jesu','lord','god','him','them','the'}
SYN={'announce':['report','tell','proclaim','declare'],'report':['tell','announce'],'proclaim':['preach','announce'],'preach':['proclaim'],'say':['tell','speak','answer'],'tell':['say'],'speak':['say','tell'],'hear':['listen','heed'],'listen':['hear'],'look':['see','behold','watch','beware','guard'],'see':['look','behold','beware','guard','watch','alert'],'behold':['see','look'],'become':['be','done','become'],'be':['become','done'],'go':['depart','leave','away','get','come'],'depart':['go','away','leave'],'stand':['rise','arise','get'],'rise':['arise','get','stand'],'arise':['rise','get','stand'],'awake':['wake','rouse'],'wake':['awake'],'believe':['trust'],'watch':['beware','alert','awake'],'beware':['watch','guard','look'],'worship':['bow'],'stop':['cease','permit','let','enough'],'permit':['let','allow','stop'],'allow':['let','permit'],'abide':['remain','stay','continue','dwell'],'remain':['abide','stay','continue'],'continue':['abide','remain'],'rejoice':['glad','joy'],'greet':['salute','greeting'],'bring':['carry','bear'],'bear':['bring','produce'],'love':['loved'],'pray':['prayer'],'repent':['repentance'],'follow':['come'],'die':['death'],'rule':['reign'],'give':['grant','pay','bestow'],'take':['pick','receive','get','accept','remove','away'],'pick':['take','lift'],'lift':['take','pick'],'receive':['take','accept','welcome'],'do':['make','practice','perform'],'seek':['inquire','search','look'],'make':['do','bear','produce','disciples'],'release':['forgive','let','leave','permit','allow','get','forsake'],'rejoice':['glad','joy','greetings','greeting'],'turn':['put','return'],'deliver':['rescue','save'],'decease':['die','death','dies'],'keep':['guard','hold','observe','obey','continue'],'learn':['receive','instruction'],'quiet':['silence','muzzled','still'],'keep':['guard','hold','observe','obey'],'obey':['keep','heed'],'submit':['subject','subjection'],'put':['lay','set','cast'],'cast':['throw','put'],'come':['came']}
out=[]; unmatched=0
for k in sorted(imps, key=lambda k:(ab.index(k[0]),k[1],k[2])):
    if k not in verses: continue
    text=verses[k]; toks=tok(text); used=set(); res=[None]*len(imps[k]); last=-1
    for use_assoc in (False,True):
      for n_,it in enumerate(imps[k]):
        if res[n_] is not None: continue
        gw=[w for w in re.findall(r"[A-Za-z]+",re.sub(r'\[.*?\]','',it['gloss'])) if w.lower() not in STOP]
        lw=[w for w in re.findall(r"[A-Za-z]+",it['lg']) if (w.lower() not in STOP or w.lower() in ('do','be')) and w.lower()!='to']
        gsw=[w.lower() for w in re.findall(r"[A-Za-z]+",it['gloss']) if w.lower() in ('be','become','let')]
        want={}
        def add(w,v):
            w=w.lower()
            for x in [w]+IRREG.get(w,[]): want[stem(x)]=max(want.get(stem(x),0),v)
            for x in SYN.get(w,[]): want[stem(x)]=max(want.get(stem(x),0),v-1.5)
        for w in gw: add(w,4)
        for w in lw: add(w,3)
        if not want:
            for w in gsw or ['be']: want[stem(w)]=3
        if use_assoc:
            for s_,v in assoc.get(it['lemma'],{}).items():
                if s_ not in BAD and v>6: want.setdefault(s_,1.0)
        exact={w.lower() for w in gw+lw}
        cand=[]
        for i,(w,a,b) in enumerate(toks):
            if i in used: continue
            sc=want.get(stem(w),0)
            if w.lower() in STOP and sc<3 and w.lower() not in exact: sc=0
            if not sc: continue
            if w.lower() in exact: sc+=0.7
            prev=text[:a].rstrip()
            if i==0 or prev[-1:] in '\'’“"[,;:—.!?' or (i>0 and toks[i-1][0].lower() in ('and','but','not','then','do','let','never')): sc+=0.8
            if i>last: sc+=0.3
            cand.append((sc,-i,i))
        if cand:
            cand.sort(reverse=True); i=cand[0][2]
            used.add(i); last=i; j=i
            def adj(x): return text[toks[x-1][2]:toks[x][1]].strip()==''
            while j>0 and adj(j) and (j-1) not in used and (toks[j-1][0].lower() in PRE or (toks[j-1][0].lower() in PRON and j>1 and adj(j-1) and toks[j-2][0].lower()=='let')): j-=1
            j=max(j,i-3)
            res[n_]=(toks[j][1],toks[i][2],it)
    marks=[r if r else (None,None,it) for r,it in zip(res,imps[k])]
    unmatched+=sum(1 for r in res if r is None)
    out.append(dict(ref=k,text=text,marks=marks))
print(len(out),'verses',sum(len(o['marks']) for o in out),'words','unmatched',unmatched)
json.dump([dict(b=k[0],c=k[1],v=k[2],text=o['text'],m=[dict(s=a,e=b,**{x:y for x,y in it.items()}) for a,b,it in o['marks']]) for o in out for k in [o['ref']]],open('data/imperatives.json','w'),ensure_ascii=False)
# HTML
names={a:n for a,n,_ in BOOKS}
def render(o):
    t=o['text']; ms=sorted([m for m in o['marks'] if m[0] is not None])
    # merge overlaps
    segs=[];pos=0
    for s,e,it in ms:
        if s<pos: continue
        segs.append(html.escape(t[pos:s])); segs.append(f'<mark>{html.escape(t[s:e])}</mark>'); pos=e
    segs.append(html.escape(t[pos:])); return ''.join(segs)
body=[];cur=None;seen=None
nbooks=collections.Counter()
for o in out:
    a,c,v=o['ref']
    if a!=cur:
        if cur: body.append('</section>')
        cur=a; body.append(f'<section id="{a}"><h2>{names[a]}</h2>')
    nbooks[a]+=1
    g=''.join(f'<span class="i" data-w="{html.escape(o["text"][a_:b_]) if a_ is not None else ""}"><span class="gk" lang="grc">{html.escape(it["greek"])}</span> <span class="ln">{html.escape(it["tr"])} — {html.escape(it["lg"])} <i>{it["parse"]}</i></span></span>' for a_,b_,it in o['marks'])
    idc=f' id="{a}.{c}.{v}"'
    body.append(f'<div class="v"{idc} data-b="{a}" data-c="{c}" data-ref="{names[a]} {c}:{v}"><span class="r">{c}:{v}</span><button class="cb" title="Copy verse" aria-label="Copy verse"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg></button><p>{render(o)}</p><div class="g">{g}</div></div>')
body.append('</section>')
nav=' '.join(f'<a href="#{a}">{names[a]} <small>{nbooks[a]}</small></a>' for a,_,_ in BOOKS if nbooks[a])
CSS="""
:root{--bg:#f7f5ef;--fg:#201f1c;--mut:#6f6c64;--mk:#ffe27a;--mkfg:#1a1400;--card:#fff;--line:#e6e2d6;--acc:#8a4b12;--chip:#f3efe3}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141417;--fg:#e9e6df;--mut:#9b9aa3;--mk:#8a6508;--mkfg:#fff;--card:#1c1c21;--line:#2f2f36;--acc:#e0a864;--chip:#26262d}}
:root[data-theme=dark]{--bg:#141417;--fg:#e9e6df;--mut:#9b9aa3;--mk:#8a6508;--mkfg:#fff;--card:#1c1c21;--line:#2f2f36;--acc:#e0a864;--chip:#26262d}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
.ar{flex:none;font:18px system-ui;line-height:1;width:34px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}.ar:disabled{opacity:.35;cursor:default}#cp{margin-right:-4px}#cn{margin-left:-4px}
main{zoom:var(--z,1)}
.v{position:relative}
.cb{position:absolute;top:8px;right:10px;display:flex;align-items:center;justify-content:center;width:30px;height:28px;padding:0;border-radius:6px;border:1px solid var(--line);background:var(--chip);color:var(--mut);cursor:pointer;opacity:.75}
.cb:hover{opacity:1;color:var(--acc);border-color:var(--acc)}
select{font:14px system-ui;height:36px;padding:0 10px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--fg);max-width:160px;cursor:pointer}select:focus{outline:2px solid var(--acc);outline-offset:1px}.bar{flex-wrap:wrap}
#ca[hidden]{display:none}h2 #ca{order:2;margin:0;font-weight:400;align-self:center}#fd{margin-left:auto}
#th{flex:none;font:15px system-ui;width:36px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:110px}
body{margin:0;background:var(--bg);color:var(--fg);font:18px/1.65 Georgia,'Iowan Old Style',serif;-webkit-font-smoothing:antialiased}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:12px 20px}
.hin{max-width:820px;margin:0 auto}
h1{font-size:20px;margin:0;letter-spacing:-.01em}.brand{display:flex;align-items:center;gap:12px;margin-bottom:8px}.brand img{border-radius:12px;flex:none}.brand .sub{margin:2px 0 0}
.sub{font:13px system-ui;color:var(--mut);margin:2px 0 8px}
.bar{display:flex;align-items:center;gap:10px;margin-top:4px}
#n{font:12px system-ui;color:var(--mut)}
main{max-width:820px;margin:0 auto;padding:0 20px 80px}
h2{margin:44px 0 12px;font-size:26px;letter-spacing:-.01em;display:flex;align-items:baseline;gap:10px}
h2::after{content:"";flex:1;height:1px;background:var(--line)}
.v{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px 12px;margin:10px 0;box-shadow:0 1px 2px rgba(0,0,0,.04);transition:box-shadow .15s,border-color .15s}
.v:hover{box-shadow:0 4px 14px rgba(0,0,0,.08);border-color:color-mix(in srgb,var(--acc) 40%,var(--line))}
.v p{margin:4px 0 8px}
.r{display:inline-block;font:700 11px system-ui;letter-spacing:.06em;color:var(--acc);background:var(--chip);border-radius:6px;padding:2px 8px}
mark{background:var(--mk);color:var(--mkfg);padding:0 3px;border-radius:4px;font-weight:600}
.g{font:13px system-ui;color:var(--mut);display:flex;flex-wrap:wrap;gap:6px;border-top:1px dashed var(--line);padding-top:8px}
.g>span.i{background:var(--chip);border-radius:8px;padding:3px 9px}
.gk{font-family:"SBL Greek",Palatino,'Palatino Linotype',serif;font-size:16px;color:var(--fg);font-weight:600}
.ln i{opacity:.75;font-style:normal;font-size:11.5px;margin-left:4px;color:var(--acc)}
#top{position:fixed;right:18px;bottom:18px;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--fg);font-size:18px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.15)}
@media(max-width:600px){body{font-size:17px}h2{font-size:22px}header{padding:10px 14px}main{padding:0 14px 80px}}
"""
page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Imperatives in the New Testament (NASB)</title><link rel="icon" href="logo.svg" type="image/svg+xml">
<style>{CSS}</style>
<header><div class="hin"><div class="brand"><img src="logo.svg" alt="" width="52" height="52"><div><h1>Imperatives in the New Testament — NASB</h1><div class="sub">{len(out)} verses · {sum(len(o["marks"]) for o in out)} imperative verbs</div></div></div><div class="bar"><select id="sb" aria-label="Book"></select><button id="cp" class="ar" aria-label="Previous chapter">‹</button><select id="sc" aria-label="Chapter"></select><button id="cn" class="ar" aria-label="Next chapter">›</button><span id="n"></span><button id="fd" class="ar" aria-label="Decrease font size" title="Smaller text" style="font-size:13px">A</button><button id="fu" class="ar" aria-label="Increase font size" title="Larger text" style="font-size:18px">A</button><button id="th" title="Toggle light/dark" aria-label="Toggle theme"></button></div></div></header>
<main><button id="ca" class="ar" style="width:auto;padding:0 12px;font:13px system-ui" hidden>Copy all</button>{''.join(body)}</main><button id="top" title="Back to top" onclick="scrollTo(0,0)">↑</button>
<script>const R=document.documentElement,dm=matchMedia('(prefers-color-scheme:dark)');let T=null;try{{T=localStorage.theme}}catch(e){{}}if(T)R.dataset.theme=T;const dk=()=>R.dataset.theme?R.dataset.theme=='dark':dm.matches,sync=()=>th.textContent=dk()?'☀️':'🌙';sync();th.onclick=()=>{{const t=dk()?'light':'dark';R.dataset.theme=t;try{{localStorage.theme=t}}catch(e){{}}sync()}};dm.onchange=sync;const CP='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>',CK='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7"/></svg>';
const esc=x=>x.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function fmt(v){{const p=v.querySelector('p'),
gi=[...v.querySelectorAll('.g .i')].map(i=>({{w:i.dataset.w||'',g:i.textContent.replace(/\\s+/g,' ').trim()}})),
ph=[...p.childNodes].map(n=>n.nodeName=='MARK'?'<b>'+esc(n.textContent)+'</b>':esc(n.textContent)).join(''),
pt=[...p.childNodes].map(n=>n.nodeName=='MARK'?'**'+n.textContent+'**':n.textContent).join(''),
head=v.dataset.ref+' (NASB)';
return {{html:'<p><b>'+esc(head)+'</b><br>'+ph+'</p>'+gi.map(x=>'<p>'+(x.w?'<b>'+esc(x.w)+'</b><br>':'')+esc(x.g)+'</p>').join(''),
text:head+'\\n'+pt+'\\n\\n'+gi.map(x=>(x.w?'**'+x.w+'**\\n':'')+x.g).join('\\n\\n')}}}}
function copyOut(html,text,b,label){{const done=()=>{{b.innerHTML=CK;setTimeout(()=>b.innerHTML=label,1200)}};
const fb=()=>{{const d=document.createElement('div');d.innerHTML=html;d.style.cssText='position:fixed;left:-9999px;white-space:pre-wrap';document.body.appendChild(d);const r=document.createRange();r.selectNodeContents(d);const s=getSelection();s.removeAllRanges();s.addRange(r);try{{document.execCommand('copy')}}catch(x){{}}s.removeAllRanges();d.remove();done()}};
if(navigator.clipboard&&window.ClipboardItem)navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([html],{{type:'text/html'}}),'text/plain':new Blob([text],{{type:'text/plain'}})}})]).then(done,fb);else fb()}}
document.addEventListener('click',e=>{{const b=e.target.closest('.cb');if(!b)return;const o=fmt(b.closest('.v'));copyOut(o.html,o.text,b,CP)}});
ca.onclick=()=>{{const o=vs.filter(d=>d.style.display!=='none').map(fmt);copyOut(o.map(x=>x.html).join('<hr>'),o.map(x=>x.text).join('\\n\\n---\\n\\n'),ca,'Copy all')}};
let Z=1;try{{Z=+localStorage.zoom||1}}catch(e){{}}const setZ=z=>{{Z=Math.min(1.6,Math.max(.8,Math.round(z*10)/10));R.style.setProperty('--z',Z);fd.disabled=Z<=.8;fu.disabled=Z>=1.6;try{{localStorage.zoom=Z}}catch(e){{}}}};fd.onclick=()=>setZ(Z-.1);fu.onclick=()=>setZ(Z+.1);setZ(Z);const vs=[...document.querySelectorAll('.v')],ss=[...document.querySelectorAll('section')],B={{}};vs.forEach(d=>{{const b=d.dataset.b,c=+d.dataset.c;(B[b]=B[b]||new Set()).add(c)}});
sb.innerHTML='<option value="">All books</option>'+ss.map(e=>`<option value="${{e.id}}">${{e.querySelector('h2').textContent}}</option>`).join('');
function fillCh(b){{sc.disabled=!b;sc.innerHTML='<option value="">All chapters</option>'+(b?[...B[b]].sort((x,y)=>x-y).map(c=>`<option value="${{c}}">Chapter ${{c}}</option>`).join(''):'')}}
function apply(){{const b=sb.value,k=sc.value;let lo=0,hi=999;if(k)lo=hi=+k;let c=0;
vs.forEach(d=>{{const n=+d.dataset.c,h=(!b||d.dataset.b==b)&&n>=lo&&n<=hi;d.style.display=h?'':'none';c+=h}});
ss.forEach(e=>e.style.display=[...e.querySelectorAll('.v')].some(d=>d.style.display!=='none')?'':'none');n.textContent=c+' verses';ca.hidden=!k;ss.forEach(e=>{{const h=e.querySelector('h2'),t=h.firstChild;if(!t.o)t.o=t.textContent;t.textContent=k&&e.style.display!=='none'?t.o+' '+k:t.o}});{{const h=k&&ss.find(e=>e.style.display!=='none');if(h)h.querySelector('h2').appendChild(ca)}}arrows();setHash(b?'#'+b+(k?'.'+k:''):'#');scrollTo({{top:0,behavior:"instant"}})}}
const L=[];vs.forEach(d=>{{const k=d.dataset.b+' '+d.dataset.c;if(L[L.length-1]!=k)L.push(k)}});
function arrows(){{const i=L.indexOf(sb.value+' '+sc.value),on=sb.value&&sc.value;cp.disabled=!on||i<1;cn.disabled=!on||i<0||i>=L.length-1}}
function step(d){{const[b,c]=L[L.indexOf(sb.value+' '+sc.value)+d].split(' ');sb.value=b;fillCh(b);sc.value=c;apply()}}
cp.onclick=()=>step(-1);cn.onclick=()=>step(1);
sb.onchange=()=>{{fillCh(sb.value);apply()}};sc.onchange=apply;
function go(h){{const m=/^#?([A-Za-z0-9]+)(?:[.]([0-9]+)(?:[.]([0-9]+))?)?$/.exec(h||'');if(!m||!B[m[1]]||(m[2]&&!B[m[1]].has(+m[2])))return false;sb.value=m[1];fillCh(m[1]);sc.value=m[2]||'';apply();const t=m[3]&&document.getElementById(`${{m[1]}}.${{m[2]}}.${{m[3]}}`);if(t&&t.style.display!=='none')t.scrollIntoView({{behavior:"instant"}});return true}}
if(!go(location.hash)){{sb.value='Mat';fillCh('Mat');sc.value='5';apply()}}
let tk=0,last='';const hh=()=>document.querySelector('header').offsetHeight;
function setHash(h){{if(location.hash===h)return;try{{history.replaceState(null,'',h)}}catch(e){{}}if(location.hash!==h){{try{{location.replace(h)}}catch(e){{}}}}}}
function track(){{tk=0;const y=hh()+2;for(const d of vs){{if(d.style.display==='none')continue;if(d.getBoundingClientRect().bottom>y){{setHash('#'+d.id);return}}}}}}
addEventListener('scroll',()=>{{if(!tk)tk=setTimeout(track,120)}},{{passive:true}});let sy=-1;setInterval(()=>{{if(scrollY!==sy){{sy=scrollY;track()}}}},250);track();
onhashchange=()=>go(location.hash);</script></html>'''
open('index.html','w',encoding='utf8').write(page)
