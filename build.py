#!/usr/bin/env python3
"""Génère le catalogue statique de l'Institut de l'Excellence depuis livres.json.
Usage: python build.py --site-url https://votre-domaine.fr
Dépendances optionnelles : pymupdf + Pillow pour extraire les nouvelles couvertures.
"""
from __future__ import annotations
import argparse, html, json, os, re, textwrap
from pathlib import Path
from urllib.parse import quote, urljoin
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--site-url',default='',help='URL absolue du site pour les métadonnées sociales (facultatif avant déploiement).')
args=parser.parse_args()
SITE_URL=(args.site_url or os.environ.get('SITE_URL','')).rstrip('/')
books=json.loads((ROOT/'livres.json').read_text(encoding='utf-8'))
h=lambda value:html.escape(str(value),quote=True)

# Génération des miniatures : première page du véritable PDF, sauf si déjà présente.
for b in books:
    cover=ROOT/'assets/img/couvertures'/f"{b['slug']}.webp"
    b['cover']=f"assets/img/couvertures/{b['slug']}.webp"
    if cover.exists():continue
    pdf=ROOT/b['pdf']
    if not pdf.is_file():raise SystemExit(f"PDF introuvable pour {b['slug']}: {pdf}")
    try:
        import fitz
        from PIL import Image
    except ImportError as e:raise SystemExit('Installer pymupdf et pillow pour générer les couvertures : pip install pymupdf pillow') from e
    with fitz.open(pdf) as doc:
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(1.75,1.75),alpha=False)
    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    im.save(cover,format='WEBP',quality=88,method=6)

# Métadonnées de partage : chaque livre dispose de sa miniature sociale.
try:
    from PIL import Image,ImageDraw,ImageFont
    SERIF_FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','C:/Windows/Fonts/georgiab.ttf','C:/Windows/Fonts/georgia.ttf']
    SANS_FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/segoeui.ttf']
    ARABIC_BOLD_FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/tahomabd.ttf','C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/segoeuib.ttf']
    ARABIC_FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/tahoma.ttf','C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/segoeui.ttf']
    def is_arabic_book(b):
        return b is not None and (b.get('langue')=='العربية' or any('\u0600'<=c<='\u06ff' for c in str(b.get('titre',''))))
    def F(paths,size):
        for p in paths:
            if Path(p).is_file():
                try:return ImageFont.truetype(p,size)
                except OSError:continue
        return ImageFont.load_default()
    def og_image(book=None):
        W,H=1200,630;im=Image.new('RGB',(W,H),(19,56,47));d=ImageDraw.Draw(im)
        ar=is_arabic_book(book)
        # Art direction: luminous green circles and small brass ornaments
        d.ellipse((650,-340,1390,390),fill=(25,68,56))
        d.ellipse((790,330,1230,770),outline=(128,115,78),width=2)
        if ar:
            d.line((645,104,760,104),fill=(184,144,83),width=3)
            d.text((760,57),'معهد التميّز للنشر',font=F(ARABIC_BOLD_FONTS,25),fill=(230,209,164),anchor='ra',direction='rtl',language='ar')
        else:
            d.line((65,104,180,104),fill=(184,144,83),width=3)
            d.text((65,57),'INSTITUT DE L’EXCELLENCE',font=F(SANS_FONTS,25),fill=(230,209,164))
        title=book['titre'] if book else 'Des savoirs à transmettre.\nDes livres à partager.'
        max_chars=28 if ar else (26 if book else 29)
        # Split by character length without cutting words.
        lines=[]
        for segment in title.split('\n'):
            lines+=textwrap.wrap(segment,width=max_chars,break_long_words=False,break_on_hyphens=False)
        top=161
        for line in lines[:4]:
            if ar:
                d.text((760,top),line,font=F(ARABIC_BOLD_FONTS,46),fill=(249,248,239),anchor='ra',direction='rtl',language='ar')
                top+=74
            else:
                d.text((65,top),line,font=F(SERIF_FONTS,51 if book else 52),fill=(249,248,239))
                top+=80
        subtitle=(book['accroche'] if book else 'Maison d’édition · Spiritualité, Coran, fiqh, histoire & éducation')
        sublines=textwrap.wrap(subtitle,width=52)
        y=max(420,top+8)
        for line in sublines[:2]:
            if ar:
                d.text((760,y),line,font=F(ARABIC_FONTS,22),fill=(205,215,202),anchor='ra',direction='rtl',language='ar')
            else:
                d.text((66,y),line,font=F(SANS_FONTS,21),fill=(205,215,202))
            y+=34
        pill_font=F(ARABIC_BOLD_FONTS if ar else SANS_FONTS,18)
        if ar:
            pill_txt=(book.get('prix') or 'إصدار مدفوع') if (book.get('categorie_id')=='payants' or book.get('payant') or book.get('prix')) else 'مجاني · متاح للجميع'
            tb=d.textbbox((0,0),pill_txt,font=pill_font)
            pw=(tb[2]-tb[0])+48
            d.rounded_rectangle((760-pw,550,760,591),radius=18,fill=(239,230,210))
            d.text((736,558),pill_txt,font=pill_font,fill=(23,61,51),anchor='ra',direction='rtl',language='ar')
        else:
            pill_txt=(book.get('prix') or 'ÉDITION PAYANTE').upper() if (book and (book.get('categorie_id')=='payants' or book.get('payant') or book.get('prix'))) else ('MAISON D’ÉDITION · ACCÈS LIBRE' if not book else 'ACCÈS GRATUIT')
            tb=d.textbbox((0,0),pill_txt,font=pill_font)
            d.rounded_rectangle((65,550,65+(tb[2]-tb[0])+48,591),radius=18,fill=(239,230,210))
            d.text((89,558),pill_txt,font=pill_font,fill=(23,61,51))
        if book:
            cover=Image.open(ROOT/book['cover']).convert('RGB')
            cover.thumbnail((310,515),Image.Resampling.LANCZOS)
            shadow=Image.new('RGBA',(cover.width+20,cover.height+20),(0,0,0,0))
            shadow.paste((0,0,0,35),(8,9,cover.width+17,cover.height+18))
            x=1001-cover.width//2;y=(H-cover.height)//2
            im.paste(shadow,(x-10,y-10),shadow)
            im.paste(cover,(x,y))
        else:
            showcase=[books[i] for i in (0,len(books)//2,len(books)-1) if i<len(books)]
            positions=[(835,145,210,330),(1015,105,220,350),(925,215,225,360)]
            for b_item,(px,py,mw,mh) in zip(showcase,positions):
                c=Image.open(ROOT/b_item['cover']).convert('RGB')
                c.thumbnail((mw,mh),Image.Resampling.LANCZOS)
                sh=Image.new('RGBA',(c.width+16,c.height+16),(0,0,0,0))
                sh.paste((0,0,0,50),(6,8,c.width+13,c.height+15))
                im.paste(sh,(px-8,py-8),sh)
                im.paste(c,(px,py))
        return im
    for b in books:og_image(b).save(ROOT/'assets/img/partage'/f"{b['slug']}.jpg",quality=88,optimize=True)
    home_og=og_image()
    home_og.save(ROOT/'assets/img/partage/institut-excellence.jpg',quality=89,optimize=True)
    home_og.save(ROOT/'assets/img/partage/institut-excellence.png',optimize=True)
except ImportError:
    print('Pillow absent : prévisualisations OpenGraph non régénérées')

ICON='''<svg width="29" height="29" viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="3.7" stroke-linecap="round" stroke-linejoin="round"><path d="M32 18c-7-6-13-7-21-6v33c9-1 15 1 21 6 6-5 12-7 21-6V12c-8-1-14 0-21 6Z"/><path d="M32 18v33M16 22c5 0 8 1 11 4m10 0c3-3 6-4 11-4"/></g></svg>'''

def absolute(path):
    return SITE_URL+'/'+path.lstrip('/') if SITE_URL else path

def meta(title,description,url,og,lang='fr'):
    canonical=f'<link rel="canonical" href="{h(absolute(url))}">' if SITE_URL else ''
    ogurl=f'<meta property="og:url" content="{h(absolute(url))}">' if SITE_URL else ''
    img=absolute(og)
    secure=f'<meta property="og:image:secure_url" content="{h(img)}">' if img.startswith('https://') else ''
    locale='ar_AR' if lang=='ar' else 'fr_FR'
    site_name='معهد التميّز للنشر' if lang=='ar' else 'Institut de l’Excellence'
    return f'''<meta name="description" content="{h(description)}">
<meta property="og:type" content="{'book' if url!='/' else 'website'}">
<meta property="og:locale" content="{locale}">
<meta property="og:site_name" content="{h(site_name)}">
<meta property="og:title" content="{h(title)}">
<meta property="og:description" content="{h(description)}">
<meta property="og:image" content="{h(img)}">
{secure}<meta property="og:image:type" content="image/jpeg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{h(title)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{h(title)}"><meta name="twitter:description" content="{h(description)}"><meta name="twitter:image" content="{h(img)}"><meta name="twitter:image:alt" content="{h(title)}">
{canonical}{ogurl}'''

def header(prefix,lang='fr'):
    if lang=='ar':
        return f'''<a class="skip" href="#main">الانتقال إلى المحتوى</a>
<header class="site-header"><div class="container nav"><a class="brand" href="{prefix}index.html" aria-label="الرئيسية — معهد التميّز للنشر"><span class="brand-mark">{ICON}</span><span><span class="brand-name">معهد التميّز للنشر</span><span class="brand-sub">دار نشر</span></span></a>
<nav class="nav-links" aria-label="التنقل الرئيسي"><a href="{prefix}index.html#catalogue">الإصدارات</a><a class="nav-about" href="{prefix}index.html#mission">رسالتنا</a><a class="nav-cta" href="{prefix}index.html#catalogue">اقرأ مجانًا</a></nav></div></header>'''
    return f'''<a class="skip" href="#main">Aller au contenu</a>
<header class="site-header"><div class="container nav"><a class="brand" href="{prefix}index.html" aria-label="Accueil — Institut de l’Excellence"><span class="brand-mark">{ICON}</span><span><span class="brand-name">Institut de l’Excellence</span><span class="brand-sub">Maison d’édition</span></span></a>
<nav class="nav-links" aria-label="Navigation principale"><a href="{prefix}index.html#catalogue">Les ouvrages</a><a class="nav-about" href="{prefix}index.html#mission">Notre mission</a><a class="nav-cta" href="{prefix}index.html#catalogue">Lire gratuitement</a></nav></div></header>'''

def footer(prefix,lang='fr'):
    if lang=='ar':
        return f'''<footer class="footer"><div class="container"><div class="footer-top"><div><a class="brand" href="{prefix}index.html"><span class="brand-mark">{ICON}</span><span><span class="brand-name">معهد التميّز للنشر</span><span class="brand-sub">دار نشر</span></span></a><p class="footer-text">مؤلفات في النقل والتفكر، متاحة للقراءة والتحميل مجانًا.</p></div><nav class="footer-nav" aria-label="روابط التذييل"><a href="{prefix}index.html#catalogue">الفهرس</a><a href="{prefix}index.html#mission">رسالتنا</a><a href="{prefix}index.html#accueil">الرئيسية</a></nav></div><div class="footer-bottom"><span>© 2026 معهد التميّز للنشر · جميع الحقوق محفوظة على المؤلفات.</span><span class="site-visits" data-visit-counter="institut-excellence-v1" data-visit-key="site-visits">زيارات الموقع : <strong data-visit-count>—</strong></span></div></div></footer><div class="toast" id="toast" role="status" aria-live="polite"></div>'''
    return f'''<footer class="footer"><div class="container"><div class="footer-top"><div><a class="brand" href="{prefix}index.html"><span class="brand-mark">{ICON}</span><span><span class="brand-name">Institut de l’Excellence</span><span class="brand-sub">Maison d’édition</span></span></a><p class="footer-text">Des ouvrages de transmission et de réflexion, proposés en lecture et en téléchargement gratuits.</p></div><nav class="footer-nav" aria-label="Liens de pied de page"><a href="{prefix}index.html#catalogue">Catalogue</a><a href="{prefix}index.html#mission">Notre mission</a><a href="{prefix}index.html#accueil">Accueil</a></nav></div><div class="footer-bottom"><span>© 2026 Institut de l’Excellence · Tous droits réservés sur les ouvrages.</span><span class="site-visits" data-visit-counter="institut-excellence-v1" data-visit-key="site-visits">Visites du site : <strong data-visit-count>—</strong></span></div></div></footer><div class="toast" id="toast" role="status" aria-live="polite"></div>'''

def shell(title,description,url,og,content,prefix='',lang='fr'):
    html_attr='lang="ar" dir="rtl"' if lang=='ar' else 'lang="fr"'
    return f'''<!DOCTYPE html><html {html_attr}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#163b33"><title>{h(title)}</title>
{meta(title,description,url,og,lang)}
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml"><link rel="manifest" href="{prefix}manifest.webmanifest"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{prefix}assets/css/style.css"></head><body>{header(prefix,lang)}{content}{footer(prefix,lang)}<script defer src="{prefix}assets/js/main.js"></script></body></html>'''

def format_excerpt(text):
    t=str(text).strip()
    return t if t.endswith(('.','!','?','…')) else t+'.'

def is_paid(b):
    return b.get('categorie_id')=='payants' or bool(b.get('payant')) or bool(b.get('prix'))

def card(b):
    ar=is_arabic_book(b)
    if ar:
        badge=b.get('prix') or 'مدفوع' if is_paid(b) else 'مجاني'
        dir_attr=' dir="rtl" lang="ar"'
        aria_lbl=f"استعراض {b['titre']}"
        alt_txt=f"غلاف كتاب {b['titre']}"
        pages_txt=f"{b['pages']} صفحة · PDF"
        more_txt='استعراض <span class="arrow" aria-hidden="true">←</span>'
    else:
        badge=b.get('prix') or 'Payant' if is_paid(b) else 'Gratuit'
        dir_attr=''
        aria_lbl=f"Découvrir {b['titre']}"
        alt_txt=f"Couverture du livre {b['titre']}"
        pages_txt=f"{b['pages']} pages · PDF"
        more_txt='Découvrir <span class="arrow" aria-hidden="true">→</span>'
    return f'''<article class="book-card" data-book data-category="{h(b['categorie_id'])}" data-search="{h(' '.join([b['titre'],b['accroche'],b['description'],b['collection'],b['categorie'],b.get('auteur','')]))}"><a href="livres/{h(b['slug'])}/" class="book-media" aria-label="{h(aria_lbl)}"><img class="book-cover" src="{h(b['cover'])}" alt="{h(alt_txt)}" loading="lazy"><span class="free-pill">{h(badge)}</span></a><div class="book-body"{dir_attr}><span class="book-collection">{h(b['collection'])}</span><h3 class="book-title"><a href="livres/{h(b['slug'])}/">{h(b['titre'])}</a></h3><p class="book-excerpt">{h(format_excerpt(b['accroche']))}</p><div class="book-bottom"><span>{pages_txt}</span><a class="link-arrow" href="livres/{h(b['slug'])}/">{more_txt}</a></div></div></article>'''

categories=[('tout','Tous les livres'),('histoires','Histoire & biographies'),('priere','Prière & spiritualité'),('education','Éducation'),('coran','Sciences du Coran'),('fiqh','Jurisprudence'),('payants','Livres payants')]
filters=''.join(f'<button type="button" class="filter-btn" data-filter="{h(key)}" aria-pressed="{str(i==0).lower()}">{h(label)}</button>' for i,(key,label) in enumerate(categories))
grouped_books=[]
seen_cats={k for k,_ in categories[1:]}
for key,label in categories[1:]:
    cat_books=[b for b in books if b.get('categorie_id')==key]
    if cat_books:
        grouped_books.append((key,label,cat_books))
other_cat_books=[b for b in books if b.get('categorie_id') not in seen_cats]
if other_cat_books:
    grouped_books.append(('autres','Autres ouvrages',other_cat_books))
books_html=''.join(
    f'<section class="category-group" data-category-group="{h(key)}">'
    f'<div class="category-header"><h3 class="category-title serif">{h(label)}</h3>'
    f'<span class="category-count" data-category-count>{len(cat_books)} ouvrage{"s" if len(cat_books)>1 else ""}</span></div>'
    f'<div class="book-grid">{"".join(card(b) for b in cat_books)}</div></section>'
    for key,label,cat_books in grouped_books
)
hero_books=[books[i] for i in (2,1,3) if i<len(books)] or books[:3]
hero_imgs=''.join(f'<img class="hero-book {cls}" src="{b["cover"]}" alt="" aria-hidden="true" loading="eager">' for cls,b in zip(['one','two','three'],hero_books))
home_wa_text=quote(f"Institut de l’Excellence — Maison d’édition : ouvrages de spiritualité, sciences du Coran, fiqh, histoire et éducation en accès libre {absolute('/')}" if SITE_URL else "Institut de l’Excellence — Maison d’édition")
home_content=f'''<main id="main"><section class="hero" id="accueil"><div class="container hero-grid"><div><span class="eyebrow">Maison d’édition · Accès libre</span><h1 class="serif">Le savoir se <em>transmet.</em><br>Il se partage.</h1><p class="hero-copy">Maison d’édition de l’Institut de l’Excellence : des livres de spiritualité, sciences du Coran, fiqh, histoire et éducation conçus pour comprendre, apprendre et progresser.</p><div class="hero-actions"><a class="btn btn-primary" href="#catalogue">Explorer les ouvrages <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="#mission">Découvrir l’Institut</a></div><div class="hero-notes"><span><span class="mini-check" aria-hidden="true">✦</span> Lecture libre</span><span><span class="mini-check" aria-hidden="true">✦</span> PDF gratuits</span><span><span class="mini-check" aria-hidden="true">✦</span> Sans inscription</span></div></div><div class="hero-art" aria-label="Sélection de couvertures de nos livres">{hero_imgs}<div class="hero-seal"><span aria-hidden="true">✦</span> {len(books)} ouvrages à découvrir</div></div></div></section>
<section class="section catalogue" id="catalogue"><div class="container"><div class="section-header"><div><span class="eyebrow">Notre bibliothèque</span><h2 class="serif">Les ouvrages de l’Institut</h2></div><p class="section-intro">Des textes de transmission, de pédagogie et de réflexion, à consulter ou à conserver gratuitement.</p></div><div class="toolbar"><div class="filters" role="group" aria-label="Filtrer les livres par catégorie">{filters}</div><label class="search" for="book-search"><span aria-hidden="true">⌕</span><span class="sr-only">Rechercher un ouvrage</span><input id="book-search" type="search" placeholder="Rechercher un livre…" autocomplete="off"></label></div><p class="results-count" id="results-count" role="status" aria-live="polite">{len(books)} ouvrages affichés</p><div class="category-groups" id="books">{books_html}</div><div class="empty-state" id="empty-results"><p>Aucun livre ne correspond à cette recherche.</p><p>Essayez un autre mot ou sélectionnez « Tous les livres ».</p></div></div></section>
<section class="section mission" id="mission"><div class="container"><div class="mission-grid"><div><span class="eyebrow">La vocation de l’Institut</span><blockquote>Éditer des livres qui rendent les savoirs <em>plus clairs, plus proches et plus utiles.</em></blockquote></div><div class="mission-copy"><p><strong>Notre ligne éditoriale :</strong> une lecture accessible sans renoncer à la rigueur, une présentation soignée et des références permettant d’aller plus loin.</p><p>Les publications sont offertes en lecture et au téléchargement. La gratuité ne supprime pas les droits d’auteur : chaque ouvrage conserve ses mentions et ses conditions d’utilisation.</p></div></div><div class="steps"><div class="step"><span class="step-symbol" aria-hidden="true">✧</span> Pédagogie accessible</div><div class="step"><span class="step-symbol" aria-hidden="true">◈</span> Sources & références</div><div class="step"><span class="step-symbol" aria-hidden="true">⌁</span> Transmission libre</div></div></div></section>
<section class="promise"><div class="container promise-grid"><div><span class="eyebrow">Une bibliothèque ouverte</span><h2>Un livre peut faire la différence.</h2><p>Choisissez un titre, lisez-le en ligne, téléchargez son PDF ou partagez l’Institut.</p></div><div class="hero-actions"><a class="btn" href="#catalogue">Consulter le catalogue <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="https://wa.me/?text={home_wa_text}" target="_blank" rel="noopener">Partager sur WhatsApp</a></div></div></section></main>'''
(ROOT/'index.html').write_text(shell('Institut de l’Excellence — Maison d’édition | Savoirs, spiritualité & histoire','Maison d’édition de l’Institut de l’Excellence : ouvrages de spiritualité, sciences du Coran, fiqh, histoire, biographies, éducation et calligraphie en lecture libre et éditions PDF.','/','assets/img/partage/institut-excellence.jpg',home_content),encoding='utf-8')

for b in books:
    slug=b['slug'];prefix='../../'
    others=[x for x in books if x['slug']!=slug][:3]
    other_html=''.join(f'<a class="other-mini" href="../{h(x["slug"])}/"><img src="{prefix}{h(x["cover"])}" alt="" loading="lazy"><span><strong>{h(x["titre"])}</strong><span>{h(x["collection"])}</span></span></a>' for x in others)
    author_meta=f'<span>{h(b["auteur"])}</span>' if b.get('auteur') else ''
    share_url=absolute(f'/livres/{slug}/')
    wa_text=quote(f"{b['titre']} — {share_url}" if share_url.startswith('http') else b['titre'])
    ar=is_arabic_book(b)
    lang='ar' if ar else 'fr'
    paid=is_paid(b)
    if ar:
        price_meta=f"<span><strong>{h(b.get('prix') or 'مدفوع')}</strong> · إصدار مدفوع</span>" if paid else '<span><strong>مجاني</strong> · وصول مفتوح</span>'
        if paid:
            buy_btn=f'<a class="btn btn-primary" href="{h(b["lien_achat"])}" target="_blank" rel="noopener">اطلب / اشترِ <span aria-hidden="true">↗</span></a>' if b.get('lien_achat') else '<span class="btn btn-primary" aria-disabled="true">إصدار مدفوع</span>'
            sample_btn=f'<a class="btn btn-outline" href="{prefix}{h(b["extrait_pdf"])}" target="_blank" rel="noopener">اقرأ مقتطفًا</a>' if b.get('extrait_pdf') else ''
            action_btns=f'{buy_btn}{sample_btn}'
            note_txt='إصدار مدفوع محمي بحقوق النشر.'
            dl_meta=''
        else:
            amazon_url=b.get('lien_amazon') or b.get('lien_achat') or ''
            amazon_btn=f'<a class="btn btn-outline" href="{h(amazon_url)}" target="_blank" rel="noopener">طلب النسخة الورقية (أمازون) <span aria-hidden="true">↗</span></a>' if amazon_url else ''
            action_btns=f'<a class="btn btn-primary" href="{prefix}{h(b["pdf"])}" target="_blank" rel="noopener" data-dl-trigger="{h(slug)}">اقرأ مجانًا <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="{prefix}{h(b["pdf"])}" download="{h(slug)}.pdf" data-dl-trigger="{h(slug)}">↓ تحميل PDF</a>{amazon_btn}'
            note_txt='لا يتطلب تسجيلًا ولا دفعًا. العمل محمي بحقوق النشر.'
            dl_meta=f'<span data-dl-counter="{h(slug)}" data-dl-ns="institut-excellence-v1"><strong data-dl-count>—</strong> تحميل</span>'
        details=f'''<main id="main"><section class="detail"><div class="container"><a class="back-link" href="../../index.html#catalogue"><span aria-hidden="true">→</span> العودة إلى الفهرس</a><div class="detail-grid"><div class="detail-image"><img src="{prefix}{h(b['cover'])}" alt="غلاف كتاب {h(b['titre'])}"></div><div class="detail-info"><span class="eyebrow">{h(b['collection'])}</span><h1 class="detail-title">{h(b['titre'])}</h1><p class="detail-lead">{h(b['accroche'])}</p><p class="detail-description">{h(b['description'])}</p><div class="detail-meta">{price_meta}{author_meta}<span>{b['pages']} صفحة</span><span>{h(b['date'])}</span><span>PDF</span>{dl_meta}</div><div class="detail-actions">{action_btns}<a class="btn btn-outline" href="https://wa.me/?text={wa_text}" target="_blank" rel="noopener">واتساب</a><button type="button" class="btn btn-outline" data-share data-title="{h(b['titre'])}">مشاركة</button></div><p class="detail-note">{note_txt}</p></div></div></div></section><section class="other-books"><div class="container"><span class="eyebrow">تصفّح المزيد</span><h2>إصدارات أخرى للقراءة</h2><div class="other-grid">{other_html}</div></div></section></main>'''
        publisher_name='معهد التميّز للنشر'
        page_title=f"{b['titre']} | معهد التميّز للنشر"
    else:
        price_meta=f"<span><strong>{h(b.get('prix') or 'Payant')}</strong> · Édition payante</span>" if paid else '<span><strong>Gratuit</strong> · Accès libre</span>'
        if paid:
            buy_btn=f'<a class="btn btn-primary" href="{h(b["lien_achat"])}" target="_blank" rel="noopener">Commander / Acheter <span aria-hidden="true">↗</span></a>' if b.get('lien_achat') else '<span class="btn btn-primary" aria-disabled="true">Édition payante</span>'
            sample_btn=f'<a class="btn btn-outline" href="{prefix}{h(b["extrait_pdf"])}" target="_blank" rel="noopener">Lire un extrait</a>' if b.get('extrait_pdf') else ''
            action_btns=f'{buy_btn}{sample_btn}'
            note_txt='Ouvrage payant protégé par le droit d’auteur.'
            dl_meta=''
        else:
            amazon_url=b.get('lien_amazon') or b.get('lien_achat') or ''
            amazon_label=f'Commander en broché ({h(b["prix_broche"])})' if b.get('prix_broche') else 'Commander en broché (Amazon)'
            amazon_btn=f'<a class="btn btn-outline" href="{h(amazon_url)}" target="_blank" rel="noopener">{amazon_label} <span aria-hidden="true">↗</span></a>' if amazon_url else ''
            action_btns=f'<a class="btn btn-primary" href="{prefix}{h(b["pdf"])}" target="_blank" rel="noopener" data-dl-trigger="{h(slug)}">Lire gratuitement <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="{prefix}{h(b["pdf"])}" download="{h(slug)}.pdf" data-dl-trigger="{h(slug)}">↓ Télécharger le PDF</a>{amazon_btn}'
            note_txt='Aucune inscription et aucun paiement requis. Œuvre protégée par le droit d’auteur.'
            dl_meta=f'<span data-dl-counter="{h(slug)}" data-dl-ns="institut-excellence-v1"><strong data-dl-count>—</strong> téléchargements</span>'
        details=f'''<main id="main"><section class="detail"><div class="container"><a class="back-link" href="../../index.html#catalogue"><span aria-hidden="true">←</span> Retour au catalogue</a><div class="detail-grid"><div class="detail-image"><img src="{prefix}{h(b['cover'])}" alt="Couverture de {h(b['titre'])}"></div><div class="detail-info"><span class="eyebrow">{h(b['collection'])}</span><h1 class="detail-title">{h(b['titre'])}</h1><p class="detail-lead">{h(b['accroche'])}</p><p class="detail-description">{h(b['description'])}</p><div class="detail-meta">{price_meta}{author_meta}<span>{b['pages']} pages</span><span>{h(b['date'])}</span><span>PDF</span>{dl_meta}</div><div class="detail-actions">{action_btns}<a class="btn btn-outline" href="https://wa.me/?text={wa_text}" target="_blank" rel="noopener">WhatsApp</a><button type="button" class="btn btn-outline" data-share data-title="{h(b['titre'])}">Partager</button></div><p class="detail-note">{note_txt}</p></div></div></div></section><section class="other-books"><div class="container"><span class="eyebrow">Poursuivre la découverte</span><h2>D’autres ouvrages à lire</h2><div class="other-grid">{other_html}</div></div></section></main>'''
        publisher_name='Institut de l’Excellence'
        page_title=f"{b['titre']} | Institut de l’Excellence"
    # Schema.org JSON-LD helps search engines describe book pages.
    schema={'@context':'https://schema.org','@type':'Book','name':b['titre'],'description':b['description'],'inLanguage':'ar' if ar else b.get('langue','fr'),'numberOfPages':b['pages'],'bookFormat':'https://schema.org/EBook','isAccessibleForFree':not paid,'publisher':{'@type':'Organization','name':publisher_name},'image':absolute('/'+b['cover'])}
    if b.get('auteur'):schema['author']={'@type':'Person','name':b['auteur']}
    schema_tag='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('</','<\\/')+'</script>'
    p=ROOT/'livres'/slug;p.mkdir(parents=True,exist_ok=True)
    page=shell(page_title,b['description'],f'/livres/{slug}/',f'assets/img/partage/{slug}.jpg',details,prefix,lang).replace('</head>',schema_tag+'</head>')
    (p/'index.html').write_text(page,encoding='utf-8')

(ROOT/'manifest.webmanifest').write_text(json.dumps({'name':'Institut de l’Excellence — Maison d’édition','short_name':'Institut Excellence','description':'Bibliothèque gratuite des ouvrages de l’Institut de l’Excellence','start_url':'/','display':'standalone','background_color':'#faf8f2','theme_color':'#163b33','icons':[{'src':'assets/img/favicon.svg','sizes':'any','type':'image/svg+xml'}]},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n'+(f'Sitemap: {SITE_URL}/sitemap.xml\n' if SITE_URL else ''),encoding='utf-8')
if SITE_URL:
    urls=[SITE_URL+'/']+[SITE_URL+f'/livres/{b["slug"]}/' for b in books]
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{h(x)}</loc></url>' for x in urls)+'</urlset>',encoding='utf-8')
else:
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<!-- Relancer python build.py --site-url https://votre-domaine pour générer le sitemap. -->\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',encoding='utf-8')
print(f"Site généré : {len(books)} ouvrages, {len(books)+1} pages HTML.")
if not SITE_URL:print('Avant mise en ligne : ajouter --site-url https://domaine-publie pour les balises de partage absolues.')
