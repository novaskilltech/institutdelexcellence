#!/usr/bin/env python3
"""Génère le catalogue statique de l'Institut de l'Excellence depuis livres.json.
Usage: python build.py --site-url https://votre-domaine.fr
Dépendances optionnelles : pymupdf + Pillow pour extraire les nouvelles couvertures.
"""
from __future__ import annotations
import argparse, html, json, re, textwrap
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--site-url',default='',help='URL absolue du site pour les métadonnées sociales (facultatif avant déploiement).')
args=parser.parse_args()
SITE_URL=args.site_url.rstrip('/')
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
    font_serif='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
    font_sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    def F(path,size):
        try:return ImageFont.truetype(path,size)
        except OSError:return ImageFont.load_default()
    def og_image(book=None):
        W,H=1200,630;im=Image.new('RGB',(W,H),(19,56,47));d=ImageDraw.Draw(im)
        # Art direction: luminous green circles and small brass ornaments
        d.ellipse((650,-340,1390,390),fill=(25,68,56))
        d.ellipse((790,330,1230,770),outline=(128,115,78),width=2)
        d.line((65,104,180,104),fill=(184,144,83),width=3)
        d.text((65,57),'INSTITUT DE L’EXCELLENCE',font=F(font_sans,25),fill=(230,209,164))
        title=book['titre'] if book else 'Des savoirs à transmettre.\nDes livres à partager.'
        max_chars=26 if book else 29
        # Split by character length without cutting words.
        lines=[]
        for segment in title.split('\n'):
            lines+=textwrap.wrap(segment,width=max_chars,break_long_words=False,break_on_hyphens=False)
        top=161
        for line in lines[:4]:
            d.text((65,top),line,font=F(font_serif,51 if book else 52),fill=(249,248,239))
            top+=80
        subtitle=(book['accroche'] if book else 'Livres et livrets gratuits · Lecture libre')
        sublines=textwrap.wrap(subtitle,width=52)
        y=max(420,top+8)
        for line in sublines[:2]:
            d.text((66,y),line,font=F(font_sans,21),fill=(205,215,202));y+=32
        d.rounded_rectangle((65,550,268,591),radius=18,fill=(239,230,210))
        d.text((89,558),'ACCÈS GRATUIT',font=F(font_sans,18),fill=(23,61,51))
        if book:
            cover=Image.open(ROOT/book['cover']).convert('RGB')
            cover.thumbnail((310,515),Image.Resampling.LANCZOS)
            shadow=Image.new('RGBA',(cover.width+20,cover.height+20),(0,0,0,0))
            shadow.paste((0,0,0,35),(8,9,cover.width+17,cover.height+18))
            x=1001-cover.width//2;y=(H-cover.height)//2
            im.paste(shadow,(x-10,y-10),shadow)
            im.paste(cover,(x,y))
        return im
    for b in books:og_image(b).save(ROOT/'assets/img/partage'/f"{b['slug']}.jpg",quality=88,optimize=True)
    og_image().save(ROOT/'assets/img/partage/institut-excellence.jpg',quality=89,optimize=True)
except ImportError:
    print('Pillow absent : prévisualisations OpenGraph non régénérées')

ICON='''<svg width="29" height="29" viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="3.7" stroke-linecap="round" stroke-linejoin="round"><path d="M32 18c-7-6-13-7-21-6v33c9-1 15 1 21 6 6-5 12-7 21-6V12c-8-1-14 0-21 6Z"/><path d="M32 18v33M16 22c5 0 8 1 11 4m10 0c3-3 6-4 11-4"/></g></svg>'''

def absolute(path):
    return SITE_URL+'/'+path.lstrip('/') if SITE_URL else path

def meta(title,description,url,og):
    canonical=f'<link rel="canonical" href="{h(absolute(url))}">' if SITE_URL else ''
    ogurl=f'<meta property="og:url" content="{h(absolute(url))}">' if SITE_URL else ''
    img=absolute(og)
    return f'''<meta name="description" content="{h(description)}">
<meta property="og:type" content="{'book' if url!='/' else 'website'}">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="Institut de l’Excellence">
<meta property="og:title" content="{h(title)}">
<meta property="og:description" content="{h(description)}">
<meta property="og:image" content="{h(img)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{h(title)}"><meta name="twitter:description" content="{h(description)}"><meta name="twitter:image" content="{h(img)}">
{canonical}{ogurl}'''

def header(prefix):
    return f'''<a class="skip" href="#main">Aller au contenu</a>
<header class="site-header"><div class="container nav"><a class="brand" href="{prefix}index.html" aria-label="Accueil — Institut de l’Excellence"><span class="brand-mark">{ICON}</span><span><span class="brand-name">Institut de l’Excellence</span><span class="brand-sub">Maison d’édition</span></span></a>
<nav class="nav-links" aria-label="Navigation principale"><a href="{prefix}index.html#catalogue">Les ouvrages</a><a class="nav-about" href="{prefix}index.html#mission">Notre mission</a><a class="nav-cta" href="{prefix}index.html#catalogue">Lire gratuitement</a></nav></div></header>'''

def footer(prefix):
    return f'''<footer class="footer"><div class="container"><div class="footer-top"><div><a class="brand" href="{prefix}index.html"><span class="brand-mark">{ICON}</span><span><span class="brand-name">Institut de l’Excellence</span><span class="brand-sub">Maison d’édition</span></span></a><p class="footer-text">Des ouvrages de transmission et de réflexion, proposés en lecture et en téléchargement gratuits.</p></div><nav class="footer-nav" aria-label="Liens de pied de page"><a href="{prefix}index.html#catalogue">Catalogue</a><a href="{prefix}index.html#mission">Notre mission</a><a href="{prefix}index.html#accueil">Accueil</a></nav></div><div class="footer-bottom"><span>© 2026 Institut de l’Excellence · Tous droits réservés sur les ouvrages.</span><span>Consultation et téléchargement gratuits · Les droits d’auteur demeurent réservés.</span></div></div></footer><div class="toast" id="toast" role="status" aria-live="polite"></div>'''

def shell(title,description,url,og,content,prefix=''):
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#163b33"><title>{h(title)}</title>
{meta(title,description,url,og)}
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml"><link rel="manifest" href="{prefix}manifest.webmanifest"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{prefix}assets/css/style.css"></head><body>{header(prefix)}{content}{footer(prefix)}<script defer src="{prefix}assets/js/main.js"></script></body></html>'''

def card(b):
    return f'''<article class="book-card" data-book data-category="{h(b['categorie_id'])}" data-search="{h(' '.join([b['titre'],b['accroche'],b['description'],b['collection'],b['categorie']]))}"><a href="livres/{h(b['slug'])}/" class="book-media" aria-label="Découvrir {h(b['titre'])}"><img class="book-cover" src="{h(b['cover'])}" alt="Couverture du livre {h(b['titre'])}" loading="lazy"><span class="free-pill">Gratuit</span></a><div class="book-body"><span class="book-collection">{h(b['collection'])}</span><h3 class="book-title"><a href="livres/{h(b['slug'])}/">{h(b['titre'])}</a></h3><p class="book-excerpt">{h(b['accroche'])}.</p><div class="book-bottom"><span>{b['pages']} pages · PDF</span><a class="link-arrow" href="livres/{h(b['slug'])}/">Découvrir <span class="arrow" aria-hidden="true">→</span></a></div></div></article>'''

categories=[('tout','Tous les livres'),('histoires','Biographies'),('priere','Prière'),('education','Éducation'),('coran','Coran'),('fiqh','Fiqh')]
filters=''.join(f'<button type="button" class="filter-btn" data-filter="{h(key)}" aria-pressed="{str(i==0).lower()}">{h(label)}</button>' for i,(key,label) in enumerate(categories))
hero_books=[books[2],books[1],books[3]]
hero_imgs=''.join(f'<img class="hero-book {cls}" src="{b["cover"]}" alt="" aria-hidden="true" loading="eager">' for cls,b in zip(['one','two','three'],hero_books))
home_content=f'''<main id="main"><section class="hero" id="accueil"><div class="container hero-grid"><div><span class="eyebrow">Maison d’édition · Accès libre</span><h1 class="serif">Le savoir se <em>transmet.</em><br>Il se partage.</h1><p class="hero-copy">Des livres conçus pour comprendre, apprendre et progresser. Découvrez les ouvrages de l’Institut de l’Excellence, disponibles gratuitement au format PDF.</p><div class="hero-actions"><a class="btn btn-primary" href="#catalogue">Explorer les ouvrages <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="#mission">Découvrir l’Institut</a></div><div class="hero-notes"><span><span class="mini-check" aria-hidden="true">✦</span> Lecture libre</span><span><span class="mini-check" aria-hidden="true">✦</span> PDF gratuits</span><span><span class="mini-check" aria-hidden="true">✦</span> Sans inscription</span></div></div><div class="hero-art" aria-label="Sélection de couvertures de nos livres">{hero_imgs}<div class="hero-seal"><span aria-hidden="true">✦</span> {len(books)} ouvrages à découvrir</div></div></div></section>
<section class="section catalogue" id="catalogue"><div class="container"><div class="section-header"><div><span class="eyebrow">Notre bibliothèque</span><h2 class="serif">Les ouvrages de l’Institut</h2></div><p class="section-intro">Des textes de transmission, de pédagogie et de réflexion, à consulter ou à conserver gratuitement.</p></div><div class="toolbar"><div class="filters" role="group" aria-label="Filtrer les livres par catégorie">{filters}</div><label class="search" for="book-search"><span aria-hidden="true">⌕</span><span class="sr-only">Rechercher un ouvrage</span><input id="book-search" type="search" placeholder="Rechercher un livre…" autocomplete="off"></label></div><p class="results-count" id="results-count" role="status" aria-live="polite">{len(books)} ouvrages affichés</p><div class="book-grid" id="books">{''.join(card(b) for b in books)}</div><div class="empty-state" id="empty-results"><p>Aucun livre ne correspond à cette recherche.</p><p>Essayez un autre mot ou sélectionnez « Tous les livres ».</p></div></div></section>
<section class="section mission" id="mission"><div class="container"><div class="mission-grid"><div><span class="eyebrow">La vocation de l’Institut</span><blockquote>Éditer des livres qui rendent les savoirs <em>plus clairs, plus proches et plus utiles.</em></blockquote></div><div class="mission-copy"><p><strong>Notre ligne éditoriale :</strong> une lecture accessible sans renoncer à la rigueur, une présentation soignée et des références permettant d’aller plus loin.</p><p>Les publications sont offertes en lecture et au téléchargement. La gratuité ne supprime pas les droits d’auteur : chaque ouvrage conserve ses mentions et ses conditions d’utilisation.</p></div></div><div class="steps"><div class="step"><span class="step-symbol" aria-hidden="true">✧</span> Pédagogie accessible</div><div class="step"><span class="step-symbol" aria-hidden="true">◈</span> Sources & références</div><div class="step"><span class="step-symbol" aria-hidden="true">⌁</span> Transmission libre</div></div></div></section>
<section class="promise"><div class="container promise-grid"><div><span class="eyebrow">Une bibliothèque ouverte</span><h2>Un livre peut faire la différence.</h2><p>Choisissez un titre, lisez-le en ligne ou téléchargez son PDF.</p></div><a class="btn" href="#catalogue">Consulter le catalogue <span aria-hidden="true">↗</span></a></div></section></main>'''
(ROOT/'index.html').write_text(shell('Institut de l’Excellence — Maison d’édition | Livres gratuits','Bibliothèque de l’Institut de l’Excellence : livres de spiritualité, sciences du Coran, fiqh, éducation et biographies, en lecture et téléchargement PDF gratuits.','/','assets/img/partage/institut-excellence.jpg',home_content),encoding='utf-8')

for b in books:
    slug=b['slug'];prefix='../../'
    others=[x for x in books if x['slug']!=slug][:3]
    other_html=''.join(f'<a class="other-mini" href="../{h(x["slug"])}/"><img src="{prefix}{h(x["cover"])}" alt="" loading="lazy"><span><strong>{h(x["titre"])}</strong><span>{h(x["collection"])}</span></span></a>' for x in others)
    details=f'''<main id="main"><section class="detail"><div class="container"><a class="back-link" href="../../index.html#catalogue"><span aria-hidden="true">←</span> Retour au catalogue</a><div class="detail-grid"><div class="detail-image"><img src="{prefix}{h(b['cover'])}" alt="Couverture de {h(b['titre'])}"></div><div class="detail-info"><span class="eyebrow">{h(b['collection'])}</span><h1 class="detail-title">{h(b['titre'])}</h1><p class="detail-lead">{h(b['accroche'])}</p><p class="detail-description">{h(b['description'])}</p><div class="detail-meta"><span><strong>Gratuit</strong> · Accès libre</span><span>{b['pages']} pages</span><span>{h(b['date'])}</span><span>PDF</span></div><div class="detail-actions"><a class="btn btn-primary" href="{prefix}{h(b['pdf'])}" target="_blank" rel="noopener">Lire en ligne <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="{prefix}{h(b['pdf'])}" download="{h(slug)}.pdf">↓ Télécharger le PDF</a><button type="button" class="btn btn-outline" data-share data-title="{h(b['titre'])}">Partager</button></div><p class="detail-note">Aucune inscription et aucun paiement requis. Œuvre protégée par le droit d’auteur.</p></div></div></div></section><section class="other-books"><div class="container"><span class="eyebrow">Poursuivre la découverte</span><h2>D’autres ouvrages à lire</h2><div class="other-grid">{other_html}</div></div></section></main>'''
    # Schema.org JSON-LD helps search engines describe book pages.
    schema={'@context':'https://schema.org','@type':'Book','name':b['titre'],'description':b['description'],'inLanguage':'fr','numberOfPages':b['pages'],'bookFormat':'https://schema.org/EBook','isAccessibleForFree':True,'publisher':{'@type':'Organization','name':'Institut de l’Excellence'},'image':absolute('/'+b['cover'])}
    schema_tag='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('</','<\\/')+'</script>'
    p=ROOT/'livres'/slug;p.mkdir(parents=True,exist_ok=True)
    page=shell(f"{b['titre']} | Institut de l’Excellence",b['description'],f'/livres/{slug}/',f'assets/img/partage/{slug}.jpg',details,prefix).replace('</head>',schema_tag+'</head>')
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
