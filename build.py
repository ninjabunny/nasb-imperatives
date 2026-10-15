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
        segs.append(html.escape(t[pos:s])); segs.append(f'<mark title="{html.escape(it["greek"])} ({html.escape(it["lg"])})">{html.escape(t[s:e])}</mark>'); pos=e
    segs.append(html.escape(t[pos:])); return ''.join(segs)
body=[];cur=None
nbooks=collections.Counter()
for o in out:
    a,c,v=o['ref']
    if a!=cur:
        if cur: body.append('</section>')
        cur=a; body.append(f'<section id="{a}"><h2>{names[a]}</h2>')
    nbooks[a]+=1
    g=' · '.join(f'<span class="gk" lang="grc">{html.escape(it["greek"])}</span> <span class="ln">{html.escape(it["tr"])} — {html.escape(it["lg"])} <i>{it["parse"]}</i></span>' for _,_,it in o['marks'])
    body.append(f'<div class="v" data-b="{a}"><span class="r">{c}:{v}</span><p>{render(o)}</p><div class="g">{g}</div></div>')
body.append('</section>')
nav=' '.join(f'<a href="#{a}">{names[a]} <small>{nbooks[a]}</small></a>' for a,_,_ in BOOKS if nbooks[a])
page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Imperatives in the New Testament (NASB)</title>
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1f;--mut:#6b6b70;--mk:#ffe066;--mkfg:#000;--card:#fff;--line:#e4e1d8}}
@media(prefers-color-scheme:dark){{:root{{--bg:#16161a;--fg:#e8e6e1;--mut:#9a9aa2;--mk:#b8860b;--mkfg:#fff;--card:#1e1e24;--line:#33333a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:17px/1.55 Georgia,serif}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}}
h1{{font-size:18px;margin:0 0 6px}}nav{{font:13px system-ui;display:flex;flex-wrap:wrap;gap:4px 10px}}nav a{{color:var(--mut);text-decoration:none}}nav small{{opacity:.7}}
input{{font:14px system-ui;padding:5px 8px;width:min(320px,100%);margin-top:6px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}}
main{{max-width:820px;margin:0 auto;padding:0 16px 60px}}h2{{margin:32px 0 8px;border-bottom:2px solid var(--line)}}
.v{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:8px 0}}
.v p{{margin:2px 0}}.r{{font:600 12px system-ui;color:var(--mut)}}
mark{{background:var(--mk);color:var(--mkfg);padding:0 2px;border-radius:3px}}
.g{{font:13px system-ui;color:var(--mut)}}.gk{{font-family:"SBL Greek",Palatino,serif;font-size:15px;color:var(--fg)}}.ln i{{opacity:.7}}
</style>
<header><h1>Imperatives in the New Testament — NASB <small style="font-weight:400;color:var(--mut)">({len(out)} verses · {sum(len(o["marks"]) for o in out)} imperative verbs)</small></h1><nav>{nav}</nav><input id="q" placeholder="Filter verses or Greek…"></header>
<main>{''.join(body)}</main>
<script>q.oninput=()=>{{const s=q.value.toLowerCase();document.querySelectorAll('.v').forEach(d=>d.style.display=d.textContent.toLowerCase().includes(s)?'':'none')}}</script></html>'''
open('index.html','w',encoding='utf8').write(page)
