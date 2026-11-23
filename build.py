# -*- coding: utf-8 -*-
import json, os, re, shutil, html
from urllib.parse import quote, unquote

HAND = r"C:\Users\user\Desktop\Claude WEB\DR MOOEN\extracted\DR-MOEEN-Claude-Handoff"
OUT  = r"C:\Users\user\Desktop\Claude WEB\DR MOOEN\drmoeen-site"

def J(p):
    with open(os.path.join(HAND, p), encoding="utf-8") as f: return json.load(f)

cfg   = J("content/site-config.json")
pages = J("content/pages.json")
testi = J("content/testimonials.json")
man   = J("assets/manifest.json")

by_id  = {p["id"]: p for p in pages}
url2id = {}
for p in pages:
    url2id[p["url"].rstrip("/")] = p["id"]
    url2id[p["final_url"].rstrip("/")] = p["id"]

LOGO = cfg["logo"]["file"]                       # assets/xxx.webp
VIDEO = cfg["clinic_video"]["file"]
POSTER = cfg["video_original_poster"]["file"]
PORTRAIT = cfg["doctor_portrait"]["file"]
CATIMG = {k: v["file"] for k, v in cfg["original_category_images"].items()}

# ---- page -> best content image (largest, excl. logo/tiny) ----
page_imgs = {}
for a in man:
    f = a.get("file")
    if not f or not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")): continue
    if f == LOGO: continue
    full = os.path.join(HAND, f)
    sz = os.path.getsize(full) if os.path.exists(full) else 0
    if sz < 9000: continue
    for r in a.get("references", []):
        pid = url2id.get((r.get("page") or "").rstrip("/"))
        if pid:
            page_imgs.setdefault(pid, [])
            if f not in [x[0] for x in page_imgs[pid]]:
                page_imgs[pid].append((f, sz))
def best_img(pid):
    lst = page_imgs.get(pid, [])
    if not lst: return None
    return sorted(lst, key=lambda x: -x[1])[0][0]

# ---- slug helpers ----
def slug_of(p):
    u = p["final_url"] or p["url"]
    s = u.split("drmatanis.com", 1)[1] if "drmatanis.com" in u else u
    s = s.strip("/")
    return unquote(s)  # raw hebrew, "" for home

for p in pages: p["slug"] = slug_of(p)
slug2id = {p["slug"]: p["id"] for p in pages}
HOME_ID = slug2id.get("", pages[0]["id"])

ABOUT, CONTACT, REVIEWS, ARTICLES = "על-הרופא", "צור-קשר", "חוות-דעת", "articles"
CATS = {"טיפולי-פנים": "face", "טיפולי-גוף": "body", "dental-care": "dental"}
CAT_LABEL = {"טיפולי-פנים": "טיפולי פנים", "טיפולי-גוף": "טיפולי גוף", "dental-care": "רפואת שיניים"}

GROUPS = {
 "טיפולי-פנים": [("salmon-injection-trout","הזרקת זרע סלמון / פורל"),("lip-filling","עיבוי ועיצוב השפתיים"),
   ("botox-injection","הזרקות בוטוקס"),("face-sculpting","פיסול פנים"),
   ("sculpture-nose-without-surgery","פיסול אף ללא ניתוח"),("under-eye-hollowness-filling","מילוי שקעים מתחת העיניים"),
   ("wrinkles-filling-hyaluronic-acid","מילוי קמטים"),("הזרקת-חומצה-היאלורונית","הזרקת חומצה היאלורונית"),
   ("טיפולי-prp-לשיער","טיפולי PRP לשיער")],
 "טיפולי-גוף": [("firming-body-skin","מיצוק עור הגוף"),("body-shaping","הצרת היקפים"),
   ("הסרת-שיער-בלייזר","הסרת שיער בלייזר"),("cellulite-removal","הסרת צלוליט"),
   ("scars-removal","הסרת צלקות"),("stretch-marks-removal","הסרת סימני מתיחה"),
   ("wrinkle-elimination","העלמת קמטים")],
 "dental-care": [("teeth-porcelain-coating","ציפויי חרסינה לשיניים"),("teeth-whitening","הלבנת שיניים"),
   ("zirkonia-aesthetic-crowns","כתרי זירקוניה"),("חריקת-שיניים-ברוקסיזם","חריקת שיניים (ברוקסיזם)"),
   ("סריקת-שיניים-באמצעות-ai","סריקת שיניים באמצעות AI")],
}
MAGAZINE = [("articles","מגזין מאמרים"),("answers-to-questions-about-botox","תשובות בנושא בוטוקס"),
   ("answers-about-lip-thickening","תשובות בנושא עיבוי שפתיים"),("fillmed","מוצרי FILLMED פילמד"),
   ("רופא-בוטוקס-מומלץ-בחיפה","רופא בוטוקס מומלץ בחיפה"),("מכשור-רפואי-טיפולי-מיצוק","מכשור רפואי - טיפולי מיצוק")]
QUICK = [("","עמוד הבית"),(ABOUT,"ד\"ר מטאנס"),(CONTACT,"קליניקות"),(REVIEWS,"חוות דעת"),
   (CONTACT,"צור קשר"),("jobs","דרושים"),("accessibility-declaration","הצהרת נגישות"),
   ("terms-of-use","תנאי שימוש ומדיניות פרטיות")]

slug2cat = {}
for cslug, items in GROUPS.items():
    for s, _ in items: slug2cat[s] = cslug

# ---- URL builders (relative, base-agnostic) ----
def depth_of(slug): return 0 if slug == "" else 1
def link(target_slug, cur_depth):
    base = "../" * cur_depth
    if target_slug == "": return base if base else "./"
    return base + quote(target_slug) + "/"
def asset(path, cur_depth): return ("../" * cur_depth) + path

def esc(s): return html.escape(s, quote=True)

# ---- content parsing ----
HEADER_DROP = {"top of page","072-394-5160","072-397-0549","דרושים","תפריט","DR.MOEEN","AESTHETICS","MENU"}
FOOTER_MARKS = {"פניה מהירה בווטסאפ","מפת אתר"}
FORM_NOISE_EXACT = {"תיאום פגישה","תיאום פגישת ייעוץ","שלח/י","* פניה בנושא","פניה בנושא","פניה בנושא *"}
ZW = "\u200b\u200e\u200f\ufeff"

def norm(s): return re.sub(r"\s+"," ",s).strip(ZW+" ").strip()

def read_body(pid):
    """Return (breadcrumb_cat_label or None, list of ('h2'|'h3'|'qa'|'p'|'ul', data))."""
    p = by_id[pid]
    raw = ""
    cf = p.get("text_file")
    # content txt lives under content/<id>.txt
    path = os.path.join(HAND, "content", pid + ".txt")
    if os.path.exists(path):
        raw = open(path, encoding="utf-8").read()
    else:
        raw = p.get("text","")
    lines = [l.rstrip() for l in raw.split("\n")]
    # drop SOURCE/TITLE preamble
    if lines and lines[0].startswith("SOURCE:"): lines = lines[3:]
    title = p["title"]
    # cut footer
    cut = len(lines)
    for i, l in enumerate(lines):
        if norm(l) in FOOTER_MARKS: cut = i; break
    lines = lines[:cut]
    # extract breadcrumb category
    cat_label = None
    out = []
    h1 = ""
    for h in p["headings"]:
        if h["level"] == "h1": h1 = norm(h["text"]); break
    H2 = {norm(h["text"]) for h in p["headings"] if h["level"]=="h2"}
    H3 = {norm(h["text"]) for h in p["headings"] if h["level"] in ("h3",)}
    # footer blurb h4 is already cut; ignore h4
    pending_list = []
    def flush_list():
        if pending_list:
            out.append(("ul", pending_list.copy())); pending_list.clear()
    for l in lines:
        t = norm(l)
        if not t: continue
        if t == title: continue
        if t in HEADER_DROP: continue
        if t in FORM_NOISE_EXACT: continue
        if t.startswith("חייגו כעת"): continue
        if "מלאו את הפרטים" in t: continue
        if "תנאי השימוש ומדיניות הפרטיות" in t: continue
        if "מסכים/ה" in t or "מאשר/ת" in t: continue
        if ">>" in t:
            parts = [x.strip() for x in t.split(">>")]
            if len(parts) >= 2:
                mid = parts[1]
                for cs, lab in CAT_LABEL.items():
                    if lab == mid or mid in ("טיפולי שיניים",) and cs=="dental-care":
                        cat_label = cs
            continue
        if t == h1: continue
        if t in H2:
            flush_list(); out.append(("h2", t)); continue
        if t in H3:
            flush_list(); out.append(("h3", t)); continue
        if t.endswith("?") and len(t) < 120:
            flush_list(); out.append(("qa", t)); continue
        # list heuristic
        if len(t) <= 34 and not t.endswith(":") and not t.endswith("."):
            pass
        if len(t) <= 34 and (t.endswith(".") or (" " not in t) or len(t.split()) <= 3) and not t.endswith(":"):
            pending_list.append(t.rstrip(".")); continue
        flush_list(); out.append(("p", t))
    flush_list()
    # collapse single-item lists to paragraph
    final = []
    for kind, data in out:
        if kind == "ul" and len(data) < 2:
            for d in data: final.append(("p", d))
        else: final.append((kind, data))
    return cat_label, final

def render_prose(blocks):
    h = []
    for kind, data in blocks:
        if kind == "h2": h.append(f"<h2>{esc(data)}</h2>")
        elif kind == "h3": h.append(f"<h3>{esc(data)}</h3>")
        elif kind == "qa": h.append(f'<h3 class="qa">{esc(data)}</h3>')
        elif kind == "ul":
            items = "".join(f"<li>{esc(x)}</li>" for x in data)
            h.append(f"<ul>{items}</ul>")
        else: h.append(f"<p>{esc(data)}</p>")
    return "\n".join(h)

# ---- shared chrome ----
def meta_desc(pid):
    for m in by_id[pid].get("metadata", []):
        if m.get("name")=="description": return m.get("content","")
    # fallback from first paragraph
    return ""

def header_html(cur_slug, d):
    nav = ""
    for n in cfg["navigation"]:
        tslug = n["path"].strip("/")
        cur = ' aria-current="page"' if tslug == cur_slug else ""
        nav += f'<a href="{link(tslug,d)}"{cur}>{esc(n["label"])}</a>'
    return f'''<header class="site-header">
  <div class="header-inner">
    <a class="logo" href="{link('',d)}" aria-label="DR.MOEEN AESTHETICS — עמוד הבית">
      <img src="{asset(LOGO,d)}" alt="DR.MOEEN AESTHETICS" width="150" height="58">
    </a>
    <nav class="nav" id="primary-nav" aria-label="תפריט ראשי">{nav}</nav>
    <a class="btn-book" href="{link(CONTACT,d)}">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
      לתיאום פגישת ייעוץ</a>
    <button class="menu-toggle" aria-label="פתיחת תפריט" aria-expanded="false" aria-controls="primary-nav">☰</button>
  </div>
</header>'''

SOCIAL = cfg["links"]
def footer_html(d):
    def col(cslug):
        items = "".join(f'<a href="{link(s,d)}">{esc(lab)}</a>' for s,lab in GROUPS[cslug])
        return f'<div class="footer-col"><h4><a href="{link(cslug,d)}">{esc(CAT_LABEL[cslug])}</a></h4>{items}</div>'
    mag = "".join(f'<a href="{link(s,d)}">{esc(lab)}</a>' for s,lab in MAGAZINE)
    quick = "".join(f'<a href="{link(s,d)}">{esc(lab)}</a>' for s,lab in QUICK)
    wa = SOCIAL["whatsapp"]; ig = SOCIAL["instagram"]; fb = SOCIAL["facebook"]
    c = cfg["clinics"]
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-col footer-brand">
        <img src="{asset(LOGO,d)}" alt="DR.MOEEN AESTHETICS">
        <p>מרפאת DMC בניצוחו של ד"ר מטאנס מועין — רפואת שיניים ורפואה אסתטית. מענה מקיף ללקוחות בקריות, בחיפה ובצפון.</p>
        <div class="footer-social">
          <a href="{esc(ig)}" target="_blank" rel="noopener" aria-label="Instagram"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg></a>
          <a href="{esc(fb)}" target="_blank" rel="noopener" aria-label="Facebook"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M14 9h3V6h-3c-1.7 0-3 1.3-3 3v2H9v3h2v6h3v-6h2.5l.5-3H14V9z"/></svg></a>
          <a href="{esc(wa)}" target="_blank" rel="noopener" aria-label="WhatsApp"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 00-8.6 15l-1 4 4.1-1A10 10 0 1012 2zm0 2a8 8 0 11-4.2 14.8l-.3-.2-2.4.6.6-2.3-.2-.3A8 8 0 0112 4zm4.4 10.3c-.2.5-1.2 1-1.7 1-.4 0-.9.2-3-1s-3.3-3.3-3.5-3.5-1-1.3-1-2.4.6-1.6.8-1.8.4-.2.6-.2h.4c.2 0 .4 0 .6.5l.8 1.9c0 .2.1.3 0 .5l-.4.6-.3.3c-.1.1-.3.3-.1.6s.6 1 1.3 1.6c.9.8 1.6 1 1.9 1.2s.4.1.6-.1l.7-.8c.2-.2.3-.2.6-.1l1.7.8c.3.1.4.2.5.3s.1.6-.1 1z"/></svg></a>
        </div>
      </div>
      {col("טיפולי-פנים")}
      {col("טיפולי-גוף")}
      {col("dental-care")}
    </div>
    <div class="footer-top" style="grid-template-columns:1fr 1fr;border-top:1px solid var(--line);padding-top:30px">
      <div class="footer-col"><h4>מגזין ומידע</h4>{mag}</div>
      <div class="footer-col"><h4>ניווט מהיר</h4>{quick}</div>
    </div>
    <div class="disclaimers">
      <p>התמונות באתר הן להמחשה בלבד. אין לראות בפרסום זה המלצה לביצוע הליך כזה או אחר. כל טיפול מותנה בפגישת ייעוץ מקדימה.</p>
      <p>הבהרה: כל תחום ההזרקות מתבצע ע"י ד"ר מטאנס, רופא שיניים בהסמכתו: "אני מתחייב לעבוד על פי הנהלים והתקנים של משרד הבריאות הישראלי לטובת מטופליי". החומרים בהם ד"ר מטאנס עושה שימוש הם חומרים המאושרים לשימוש ע"י משרד הבריאות ורשות התרופות האמריקאית ה-FDA.</p>
      <p>סניף קריות: {esc(c[0]["address"])}. טלפון: <span class="tel">{esc(c[0]["phone"])}</span>.<br>
         סניף צפון: מעיליא. טלפון: <span class="tel">{esc(c[1]["phone"])}</span>.</p>
    </div>
    <div class="copyright">© 2017–<span id="year">2026</span> ד"ר מטאנס מועין · www.drmatanis.com · כל הזכויות שמורות.</div>
  </div>
</footer>'''

DEMO_BANNER = '<div style="background:#1a1613;border-bottom:1px solid var(--line);color:var(--muted);text-align:center;font-size:12.5px;padding:7px 12px">גרסת דמו לצורכי בדיקה בלבד — התוכן נאסף מהאתר הציבורי · אינה מחליפה את האתר הפעיל</div>'

def page_shell(title, desc, body, d, cur_slug, extra_head="", noindex=False):
    robots = '<meta name="robots" content="noindex, nofollow">' if noindex else ''
    desc_tag = f'<meta name="description" content="{esc(desc)}">' if desc else ''
    canon = "https://www.drmatanis.com/" + (quote(cur_slug)+"/" if cur_slug else "")
    return f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{desc_tag}
{robots}
<link rel="canonical" href="{esc(canon)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#121110">
<link rel="icon" href="{asset(LOGO,d)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500;700&family=Heebo:wght@300;400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset('assets/site.css',d)}">
{extra_head}
</head>
<body>
{DEMO_BANNER}
{header_html(cur_slug,d)}
<main id="main">
{body}
</main>
{footer_html(d)}
<script src="{asset('assets/site.js',d)}" defer></script>
</body>
</html>'''

def breadcrumb_html(trail, d):
    parts = []
    for i,(slug,label) in enumerate(trail):
        if i < len(trail)-1:
            parts.append(f'<a href="{link(slug,d)}">{esc(label)}</a>')
        else:
            parts.append(f'<span style="color:var(--text2)">{esc(label)}</span>')
    return '<nav class="breadcrumb" aria-label="מיקום">' + '<span>›</span>'.join(parts) + '</nav>'

# ---- contact form component ----
def contact_form_html():
    co = cfg["contact_form"]
    clinics = "".join(f'<option value="{esc(o)}">{esc(o)}</option>' for o in co["clinic_options"])
    subs = "".join(f'<option value="{esc(o)}">{esc(o)}</option>' for o in co["subject_options"])
    return f'''<form id="contact-form" class="form-card" novalidate>
  <div class="form-note">זוהי בקשת תיאום בלבד ואינה אישור תור. ליעד שליחה פעיל יש להגדיר חיבור שרת (ראו README). עד אז ניתן לחייג 072-394-5160 או לפנות בוואטסאפ.</div>
  <div class="row2">
    <div class="field"><label for="fn">שם פרטי <span class="req">*</span></label><input id="fn" name="first_name" required><div class="err">נא למלא שם פרטי</div></div>
    <div class="field"><label for="ln">שם משפחה <span class="req">*</span></label><input id="ln" name="last_name" required><div class="err">נא למלא שם משפחה</div></div>
  </div>
  <div class="row2">
    <div class="field"><label for="ph">טלפון <span class="req">*</span></label><input id="ph" name="phone" type="tel" inputmode="tel" class="ltr" required><div class="err">נא למלא מספר טלפון תקין</div></div>
    <div class="field"><label for="em">דוא״ל</label><input id="em" name="email" type="email" class="ltr"><div class="err">כתובת דוא״ל אינה תקינה</div></div>
  </div>
  <div class="row2">
    <div class="field"><label for="cl">בחר/י קליניקה <span class="req">*</span></label><select id="cl" name="clinic" required><option value="">— בחר/י —</option>{clinics}</select><div class="err">נא לבחור קליניקה</div></div>
    <div class="field"><label for="su">נושא הפנייה <span class="req">*</span></label><select id="su" name="subject" required><option value="">— בחר/י —</option>{subs}</select><div class="err">נא לבחור נושא</div></div>
  </div>
  <div class="field"><label for="dt">תאריך מבוקש (בקשה בלבד)</label><input id="dt" name="preferred_date" type="date" class="ltr"></div>
  <div class="field"><label for="msg">הודעה</label><textarea id="msg" name="message"></textarea></div>
  <label class="consent"><input type="checkbox" name="consent" required>אני מסכים/ה ל<a href="../terms-of-use/" style="color:var(--gold-lt)">תנאי השימוש ומדיניות הפרטיות</a> <span class="req">*</span></label>
  <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">שלח/י בקשת תיאום</button>
  <div class="form-status" role="status" aria-live="polite"></div>
</form>'''

def clinics_html(d):
    cards = ""
    for c in cfg["clinics"]:
        cards += f'''<div class="clinic">
      <h3>{esc(c["name"])}</h3>
      <div class="addr">{esc(c["address"])}</div>
      <div class="acts">
        <a class="chip" href="{esc(c["tel"])}" dir="ltr">☎ {esc(c["phone"])}</a>
        <a class="chip" href="{esc(c["waze"])}" target="_blank" rel="noopener">📍 ניווט ב-Waze</a>
      </div>
    </div>'''
    return f'<div class="clinics">{cards}</div>'

# =========================================================
#  BUILD
# =========================================================
if os.path.isdir(OUT):
    for name in os.listdir(OUT):
        if name in (".git",): continue
        p = os.path.join(OUT, name)
        if name == "assets": continue  # keep css/js we authored; media copied below
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
# copy media assets (skip our css/js)
for name in os.listdir(os.path.join(HAND, "assets")):
    if name in ("site.css","site.js"): continue
    src = os.path.join(HAND, "assets", name)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(OUT, "assets", name))

def write_page(slug, html_str):
    d = depth_of(slug)
    folder = OUT if slug == "" else os.path.join(OUT, slug)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_str)

# ---------- HOME ----------
def build_home():
    d = 0
    hp = by_id[HOME_ID]
    cat_cards = ""
    order = [("טיפולי-פנים","face"),("טיפולי-גוף","body"),("dental-care","dental")]
    for cslug, key in order:
        img = asset(CATIMG[key], d)
        cat_cards += f'''<a class="cat-card" href="{link(cslug,d)}" aria-label="{esc(CAT_LABEL[cslug])}">
      <img src="{img}" alt="" loading="lazy"><div class="veil"></div>
      <div class="label"><h3>{esc(CAT_LABEL[cslug])}</h3>
        <span class="arrow"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 6l-6 6 6 6"/></svg></span>
      </div></a>'''
    tcards = ""
    for t in testi:
        stars = "★" * int(t.get("displayed_stars",5))
        tcards += f'''<figure class="testi"><div class="stars" aria-label="5 כוכבים">{stars}</div>
      <p>{esc(t["text"])}</p><figcaption class="who">{esc(t["author"])}</figcaption></figure>'''
    bio = ('ד"ר מטאנס מועין, עוסק בתחומי רפואת השיניים והרפואה האסתטית. את ניסיונו המקצועי '
           'רכש ד"ר מטאנס במהלך לימודיו האקדמיים ובמסגרת השתלמויות מקצועיות שעבר בארץ ובעולם.')
    teas = {
     "face": "הקליניקה של ד\"ר מטאנס עוסקת ברפואה אסתטית ומעניקה מגוון רחב של טיפולי אסתטיקה חדשניים באזור הפנים. מטרת הטיפולים השונים היא להשיג ללקוח מראה רענן יותר וליצור הרמוניה בין מראה הפנים למראה השיניים.",
     "dental": "רפואת השיניים היא תחום עיסוק מרכזי בקליניקת DMC של ד\"ר מטאנס מועין. המרפאה מבצעת מגוון רחב של טיפולי שיניים מתקדמים למבוגרים ולילדים, בסביבה סטרילית והיגיינית ובשימוש בציוד חדיש ומתקדם.",
     "body": "מרפאת DMC של ד\"ר מטאנס מועין מציעה מגוון טיפולי גוף אסתטיים בטכנולוגיות מתקדמות. מגוון הטיפולים הרחב, בשילוב הידע המקצועי, מאפשר לנו להציע ללקוחותינו את פתרונות היופי והאסתטיקה המובילים.",
    }
    body = f'''
<section class="hero" aria-label="ראשי">
  <div class="wrap">
    <div class="hero-grid">
      <div class="player" aria-label="סרטון היכרות עם המרפאה">
        <video poster="{asset(POSTER,d)}" preload="metadata" playsinline>
          <source src="{asset(VIDEO,d)}" type="video/mp4">
          הדפדפן שלך אינו תומך בנגן הווידאו.
        </video>
        <div class="poster-ui" role="button" tabindex="0" aria-label="הפעלת סרטון המרפאה">
          <span class="play-ring"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>
          <span class="caption">הכירו את המרפאה</span>
        </div>
      </div>
      <div class="hero-text">
        <div class="eyebrow"><b>DR.MOEEN</b> <span class="green">AESTHETICS</span></div>
        <h1>העתיד של היופי<br>מתחיל בך</h1>
        <div class="subline">אסתטיקה <span class="dot">•</span> רפואת שיניים <span class="dot">•</span> טכנולוגיה</div>
        <div class="hero-cta">
          <a class="btn btn-primary" href="{link(CONTACT,d)}">לתיאום פגישת ייעוץ</a>
          <a class="btn btn-ghost" href="#categories">גלו את הטיפולים
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 6l-6 6 6 6"/></svg></a>
        </div>
      </div>
    </div>
    <div class="wave" aria-hidden="true"><svg viewBox="0 0 1200 60" preserveAspectRatio="none"><path d="M0 40 Q 300 5 600 32 T 1200 24" fill="none" stroke="currentColor" stroke-width="1.4"/></svg></div>
    <div class="locations">קריות <span style="color:var(--gold)">•</span> מעיליא</div>
    <div id="categories" class="cats">{cat_cards}</div>
  </div>
</section>

<section aria-label="על הרופא">
  <div class="wrap">
    <div class="doctor">
      <div class="portrait"><img src="{asset(PORTRAIT,d)}" alt="ד&quot;ר מטאנס מועין" loading="lazy"></div>
      <div>
        <div class="section-eyebrow" style="text-align:right">על הרופא</div>
        <h2>ד"ר מטאנס מועין</h2>
        <div class="eng">Dr. Moeen Matanis</div>
        <p style="color:var(--text2)">{esc(bio)}</p>
        <p style="color:var(--text2)">{esc(teas["face"])}</p>
        <div class="hero-cta" style="margin-top:22px"><a class="btn btn-primary" href="{link(ABOUT,d)}">עוד על ד"ר מטאנס</a>
        <a class="btn btn-ghost" href="{link(CONTACT,d)}">למידע על הקליניקות</a></div>
      </div>
    </div>
  </div>
</section>

<section aria-label="תחומי טיפול" style="background:rgba(185,157,117,.04);border-block:1px solid var(--line)">
  <div class="wrap">
    <div class="section-eyebrow">תחומי הטיפול</div>
    <div class="section-title"><h2>שלושה עולמות של אסתטיקה</h2></div>
    <div class="tiles" style="grid-template-columns:repeat(3,1fr)">
      <div class="tile"><div class="ph"><img src="{asset(CATIMG["face"],d)}" alt="" loading="lazy"></div><div class="tt" style="flex-direction:column;align-items:stretch"><h3 style="margin-bottom:8px"><a href="{link("טיפולי-פנים",d)}">טיפולי פנים</a></h3><p style="color:var(--text2);font-size:14.5px;margin:0">{esc(teas["face"])}</p></div></div>
      <div class="tile"><div class="ph"><img src="{asset(CATIMG["body"],d)}" alt="" loading="lazy"></div><div class="tt" style="flex-direction:column;align-items:stretch"><h3 style="margin-bottom:8px"><a href="{link("טיפולי-גוף",d)}">טיפולי גוף</a></h3><p style="color:var(--text2);font-size:14.5px;margin:0">{esc(teas["body"])}</p></div></div>
      <div class="tile"><div class="ph"><img src="{asset(CATIMG["dental"],d)}" alt="" loading="lazy"></div><div class="tt" style="flex-direction:column;align-items:stretch"><h3 style="margin-bottom:8px"><a href="{link("dental-care",d)}">רפואת שיניים</a></h3><p style="color:var(--text2);font-size:14.5px;margin:0">{esc(teas["dental"])}</p></div></div>
    </div>
  </div>
</section>

<section aria-label="חוות דעת">
  <div class="wrap">
    <div class="section-eyebrow">לקוחות ממליצים</div>
    <div class="section-title"><h2>חוות דעת</h2></div>
    <p class="lead">{len(testi)} חוות דעת שנאספו מעמוד הבית של האתר.</p>
    <div class="testi-grid">{tcards}</div>
    <div style="text-align:center;margin-top:30px"><a class="btn btn-ghost" href="{link(REVIEWS,d)}">לכל חוות הדעת</a></div>
  </div>
</section>

<section id="booking" aria-label="תיאום פגישה" style="background:rgba(185,157,117,.04);border-block:1px solid var(--line)">
  <div class="wrap">
    <div class="section-eyebrow">נשמח לעמוד לרשותכם</div>
    <div class="section-title"><h2>תיאום פגישת ייעוץ</h2></div>
    <p class="lead">חייגו 072-394-5160 או השאירו פרטים ונחזור אליכם.</p>
    <div class="contact-grid" style="margin-top:30px">
      {contact_form_html()}
      <div>{clinics_html(d)}</div>
    </div>
  </div>
</section>'''
    title = hp["title"]
    write_page("", page_shell(title, meta_desc(HOME_ID) or bio, body, d, ""))

# ---------- generic content/treatment page ----------
def build_content_page(pid):
    p = by_id[pid]; slug = p["slug"]; d = 1
    cat_label, blocks = read_body(pid)
    cslug = slug2cat.get(slug) or cat_label
    # breadcrumb trail
    trail = [("","בית")]
    leaf = p["title"].split("»")[0].split("|")[0].strip()
    h1 = next((h["text"] for h in p["headings"] if h["level"]=="h1"), leaf)
    if cslug and cslug in CAT_LABEL:
        trail.append((cslug, CAT_LABEL[cslug]))
    trail.append((slug, norm(h1)))
    img = best_img(pid)
    media = ""
    if img:
        media = f'<aside class="media-col"><img src="{asset(img,d)}" alt="{esc(norm(h1))}" loading="lazy"></aside>'
    # related links: siblings in same category
    related = ""
    if cslug and cslug in GROUPS:
        sibs = [(s,l) for s,l in GROUPS[cslug] if s != slug]
        if sibs:
            links_ = "".join(f'<a href="{link(s,d)}">{esc(l)}</a>' for s,l in sibs[:8])
            related = f'<div class="related"><h4>{esc(CAT_LABEL[cslug])} נוספים</h4>{links_}</div>'
    prose = render_prose(blocks)
    cta = f'''<div class="related" style="text-align:center;margin-top:30px">
      <h4>מעוניינים בטיפול?</h4>
      <p style="color:var(--text2)">חייגו <a href="{cfg["clinics"][0]["tel"]}" dir="ltr" style="color:var(--gold-lt)">072-394-5160</a> או קבעו פגישת ייעוץ.</p>
      <a class="btn btn-primary" href="{link(CONTACT,d)}" style="margin-top:8px">לתיאום פגישת ייעוץ</a>
    </div>'''
    body = f'''<div class="wrap narrow">
  <div class="page-head">{breadcrumb_html(trail,d)}<h1>{esc(norm(h1))}</h1></div>
  <div class="content with-media">
    <div class="prose">{prose}{cta}</div>
    <div>{media}{related}</div>
  </div>
</div>'''
    noindex = slug == "thank-you"
    write_page(slug, page_shell(p["title"], meta_desc(pid), body, d, slug, noindex=noindex))

# ---------- category page ----------
def build_category_page(cslug):
    pid = slug2id[cslug]; p = by_id[pid]; d = 1
    _, blocks = read_body(pid)
    # trim prose to the intro: stop once the per-treatment list begins
    tlabels = {norm(lab) for _, lab in GROUPS[cslug]}
    tlabels |= {norm(lab).replace(" / ", " ") for _, lab in GROUPS[cslug]}
    intro = []
    for kind, data in blocks:
        if kind in ("h2", "h3", "qa") and norm(data) in tlabels:
            break
        intro.append((kind, data))
    blocks = intro
    h1 = next((h["text"] for h in p["headings"] if h["level"]=="h1"), CAT_LABEL[cslug])
    tiles = ""
    for s, lab in GROUPS[cslug]:
        tid = slug2id.get(s); im = best_img(tid) if tid else None
        ph = f'<img src="{asset(im,d)}" alt="" loading="lazy">' if im else ''
        tiles += f'''<a class="tile" href="{link(s,d)}">
      <div class="ph">{ph}</div>
      <div class="tt"><h3>{esc(lab)}</h3><span class="arrow"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 6l-6 6 6 6"/></svg></span></div></a>'''
    trail = [("","בית"),(cslug, CAT_LABEL[cslug])]
    prose = render_prose(blocks)
    body = f'''<div class="wrap">
  <div class="page-head">{breadcrumb_html(trail,d)}<h1>{esc(norm(h1))}</h1></div>
  <div class="narrow"><div class="prose">{prose}</div></div>
  <div class="section-title" style="margin-top:36px"><h2>הטיפולים בתחום</h2></div>
  <div class="tiles">{tiles}</div>
  <div style="text-align:center;margin-top:40px"><a class="btn btn-primary" href="{link(CONTACT,d)}">לתיאום פגישת ייעוץ</a></div>
</div>'''
    write_page(cslug, page_shell(p["title"], meta_desc(pid), body, d, cslug))

# ---------- contact page ----------
def build_contact_page():
    cslug = CONTACT; pid = slug2id[cslug]; p = by_id[pid]; d = 1
    _, blocks = read_body(pid)
    h1 = next((h["text"] for h in p["headings"] if h["level"]=="h1"), "צור קשר")
    trail = [("","בית"),(cslug,"צור קשר")]
    body = f'''<div class="wrap">
  <div class="page-head">{breadcrumb_html(trail,d)}<h1>{esc(norm(h1))}</h1></div>
  <p class="lead" style="margin-bottom:30px">נשמח לעמוד לרשותכם. חייגו, נווטו אל אחת הקליניקות, או השאירו פרטים.</p>
  {clinics_html(d)}
  <div class="contact-grid" style="margin-top:36px">
    {contact_form_html()}
    <div>
      <div class="related"><h4>פנייה מהירה</h4>
        <p style="color:var(--text2)">ניתן לפנות גם בוואטסאפ או בטלפון בשעות הפעילות.</p>
        <a class="chip" style="margin:6px 6px 0 0" href="{esc(SOCIAL["whatsapp"])}" target="_blank" rel="noopener">פנייה בוואטסאפ</a>
      </div>
    </div>
  </div>
</div>'''
    write_page(cslug, page_shell(p["title"], meta_desc(pid), body, d, cslug))

# ---------- reviews page ----------
def build_reviews_page():
    cslug = REVIEWS; pid = slug2id[cslug]; p = by_id[pid]; d = 1
    h1 = next((h["text"] for h in p["headings"] if h["level"]=="h1"), "חוות דעת")
    trail = [("","בית"),(cslug,"חוות דעת")]
    tcards = ""
    for t in testi:
        stars = "★" * int(t.get("displayed_stars",5))
        tcards += f'<figure class="testi"><div class="stars">{stars}</div><p>{esc(t["text"])}</p><figcaption class="who">{esc(t["author"])}</figcaption></figure>'
    body = f'''<div class="wrap">
  <div class="page-head">{breadcrumb_html(trail,d)}<h1>{esc(norm(h1))}</h1></div>
  <p class="lead" style="margin-bottom:30px">{len(testi)} חוות דעת שנאספו מעמוד הבית של האתר. מוצגות רק חוות דעת שנמצאו במקור.</p>
  <div class="testi-grid">{tcards}</div>
  <div style="text-align:center;margin-top:40px"><a class="btn btn-primary" href="{link(CONTACT,d)}">לתיאום פגישת ייעוץ</a></div>
</div>'''
    write_page(cslug, page_shell(p["title"], meta_desc(pid), body, d, cslug))

# ---------- articles index ----------
def build_articles_page():
    cslug = ARTICLES; pid = slug2id[cslug]; p = by_id[pid]; d = 1
    _, blocks = read_body(pid)
    h1 = next((h["text"] for h in p["headings"] if h["level"]=="h1"), "מגזין")
    trail = [("","בית"),(cslug,"מגזין")]
    arts = [("answers-to-questions-about-botox","תשובות לשאלות בנושא בוטוקס"),
            ("answers-about-lip-thickening","תשובות בנושא עיבוי שפתיים"),
            ("רופא-בוטוקס-מומלץ-בחיפה","רופא בוטוקס מומלץ בחיפה והצפון"),
            ("fillmed","מוצרי FILLMED פילמד"),
            ("מכשור-רפואי-טיפולי-מיצוק","מכשור רפואי — טיפולי מיצוק"),
            ("סריקת-שיניים-באמצעות-ai","סריקת שיניים באמצעות AI")]
    tiles = ""
    for s,lab in arts:
        tid = slug2id.get(s); im = best_img(tid) if tid else None
        ph = f'<img src="{asset(im,d)}" alt="" loading="lazy">' if im else ''
        tiles += f'<a class="tile" href="{link(s,d)}"><div class="ph">{ph}</div><div class="tt"><h3>{esc(lab)}</h3><span class="arrow">›</span></div></a>'
    prose = render_prose(blocks)
    body = f'''<div class="wrap">
  <div class="page-head">{breadcrumb_html(trail,d)}<h1>{esc(norm(h1))}</h1></div>
  <div class="narrow"><div class="prose">{prose}</div></div>
  <div class="tiles" style="margin-top:20px">{tiles}</div>
</div>'''
    write_page(cslug, page_shell(p["title"], meta_desc(pid), body, d, cslug))

# ---- dispatch ----
built = set()
build_home(); built.add(HOME_ID)
build_contact_page(); built.add(slug2id[CONTACT])
build_reviews_page(); built.add(slug2id[REVIEWS])
build_articles_page(); built.add(slug2id[ARTICLES])
for cslug in CATS:
    build_category_page(cslug); built.add(slug2id[cslug])
for p in pages:
    if p["id"] in built: continue
    build_content_page(p["id"]); built.add(p["id"])

# ---- sitemap, robots, 404, nojekyll ----
open(os.path.join(OUT, ".nojekyll"), "w").close()
urls = []
for p in pages:
    if p["slug"] == "thank-you": continue
    loc = "https://orgme24.github.io/drmoeen/" + (quote(p["slug"])+"/" if p["slug"] else "")
    urls.append(loc)
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls: sm += f"  <url><loc>{u}</loc></url>\n"
sm += "</urlset>\n"
open(os.path.join(OUT,"sitemap.xml"),"w",encoding="utf-8").write(sm)
# Demo: discourage indexing
open(os.path.join(OUT,"robots.txt"),"w",encoding="utf-8").write(
    "User-agent: *\nDisallow: /\n\nSitemap: https://orgme24.github.io/drmoeen/sitemap.xml\n")
# 404
nf = page_shell("הדף לא נמצא · DR.MOEEN", "",
    '<div class="wrap narrow" style="padding:80px 0;text-align:center">'
    '<h1>404</h1><p class="lead">הדף שחיפשת לא נמצא.</p>'
    '<a class="btn btn-primary" href="./">חזרה לעמוד הבית</a></div>', 0, "", noindex=True)
open(os.path.join(OUT,"404.html"),"w",encoding="utf-8").write(nf)

print("BUILT pages:", len(built), "of", len(pages))
print("Routes written:", sorted([p['slug'] or '(home)' for p in pages]))
