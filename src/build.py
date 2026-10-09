#!/usr/bin/env python3
"""Static site generator for sitesthatbook.com.
Usage: python3 build.py deploy|preview
deploy  -> ./dist     clean URLs (/pricing), absolute assets, real form posts
preview -> ./preview  flat .html files for the Artifact preview
"""
import json, os, sys, shutil, html
from datetime import date
from trades import TRADES, ICONS
from posts import POSTS

MODE = sys.argv[1] if len(sys.argv) > 1 else "deploy"
OUT = "dist" if MODE == "deploy" else "preview"
SITE = "https://www.sitesthatbook.com"
PHONE = "+1 307-218-7725"
TEL = "+13072187725"
EMAIL = "info@sitesthatbook.com"
LOGO = "https://vibe.filesafe.space/1783379195664317566/attachments/042b063c-12b0-406e-9093-c2495e3145f3.png"
LOGO_WHITE = "https://vibe.filesafe.space/1783379195664317566/attachments/2287cd0e-9e28-45f6-834a-76c017c1ceaf.png"
FB = "https://web.facebook.com/profile.php?id=61591392166533"
IG = "https://www.instagram.com/sitesthatbook"
TODAY = date.today().isoformat()
SETUP, MONTHLY = "$349", "$99"
GA4_ID = "G-B4F43GR07E"
META_PIXEL_ID = "1031461002806380"
# Form delivery. Fill these 3 values, rebuild, redeploy.
GHL_WEBHOOK = "https://services.leadconnectorhq.com/hooks/20s74Ma9bI9VvC7iqVW3/webhook-trigger/50e0a686-1484-46b6-8f98-1bdac1dab51f"
CLOUDINARY_CLOUD = "lfktoefi"
CLOUDINARY_PRESET = "fekgn3gt"

PAGES = []  # (path, priority) for sitemap

def L(path):
    """Internal link."""
    if MODE == "deploy":
        return "/" + path
    return ("index" if path == "" else path.replace("/", "__")) + ".html"

def outfile(path):
    if MODE == "deploy":
        return os.path.join(OUT, "index.html" if path == "" else path + ".html")
    return os.path.join(OUT, ("index" if path == "" else path.replace("/", "__")) + ".html")

def esc(s): return html.escape(s, quote=True)

TICK = '<span class="tick" aria-hidden="true"><svg viewBox="0 0 12 12"><path d="M2.5 6.2l2.3 2.3 4.7-4.9" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></span>'
SEARCH_ICO = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2" fill="none"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
MARK = '<span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="3" stroke="#fff" stroke-width="2" fill="none"/><path d="M3 10h18M8 3v4M16 3v4M8.5 15l2.3 2.3 4.7-4.6" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></span>'

def ico(name):
    return f'<span class="trade-icon" aria-hidden="true"><svg viewBox="0 0 24 24">{ICONS[name]}</svg></span>'

def checks(items, cols=False):
    return f'<ul class="checks{" cols" if cols else ""}">' + "".join(f"<li>{TICK}<span>{i}</span></li>" for i in items) + "</ul>"

def brand(light=False):
    mark = open("assets/logo-mark.svg").read().replace("<svg ", '<svg class="brand-svg" aria-hidden="true" focusable="false" ')
    cls = "brand light" if light else "brand"
    return f'<a class="{cls}" href="{L("")}" aria-label="SitesThatBook home">{mark}<span class="wordmark">sitesthat<b>book</b><i>.</i></span></a>'

# ---------------------------------------------------------------- schema
ORG = {
 "@type":"ProfessionalService","@id":SITE+"/#org","name":"SitesThatBook","url":SITE+"/",
 "logo":SITE+"/assets/logo.png","image":SITE+"/assets/logo.png","telephone":PHONE,"email":EMAIL,
 "description":"Done-for-you websites for US home service businesses. $349 setup, $99 per month, live in 48 hours, with hosting, SEO, updates and blog posts included.",
 "address":{"@type":"PostalAddress","streetAddress":"30 N Gould St","addressLocality":"Sheridan","addressRegion":"WY","postalCode":"82801","addressCountry":"US"},
 "areaServed":{"@type":"Country","name":"United States"},
 "priceRange":"$349 setup, from $99/month",
 "sameAs":[FB,IG],
 "knowsAbout":["Website design for contractors","Home service websites","Local SEO","Google Business Profile","Google Ads for contractors"],
}
WEBSITE = {"@type":"WebSite","@id":SITE+"/#website","url":SITE+"/","name":"SitesThatBook","publisher":{"@id":SITE+"/#org"}}

def crumbs_schema(trail):
    return {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":n,"item":SITE+("/"+p if p else "/")} for i,(n,p) in enumerate(trail)]}

def faq_schema(faqs):
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]}

def service_schema(name, desc, path):
    return {"@type":"Service","name":name,"description":desc,"provider":{"@id":SITE+"/#org"},
            "areaServed":{"@type":"Country","name":"United States"},"url":SITE+"/"+path,
            "offers":{"@type":"Offer","price":"349","priceCurrency":"USD","description":"$349 setup plus $99 per month"}}

# ---------------------------------------------------------------- chrome
NAV = [("Industries","industries"),("Pricing","pricing"),("How it works","how-it-works"),("Our work","our-work"),("About","about"),("Blog","blog")]

def header(active):
    dd = "".join(f'<a href="{L(t["slug"])}">{t["name"]} websites</a>' for t in TRADES)
    items = []
    for name, path in NAV:
        cur = ' aria-current="page"' if path == active else ""
        if path == "industries":
            items.append(f'<li class="dd"><a href="{L(path)}"{cur}>Industries</a><div class="dd-panel">{dd}</div></li>')
        else:
            items.append(f'<li><a href="{L(path)}"{cur}>{name}</a></li>')
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap nav">
{brand()}
<nav aria-label="Main"><ul class="nav-links" id="navlinks">{"".join(items)}<li class="mobile-only"><a href="{L("get-started")}">Get started</a></li></ul></nav>
<div class="nav-cta"><a class="nav-phone" href="tel:{TEL}">{PHONE}</a><a class="btn btn-primary btn-sm" href="{L("get-started")}">Get my site</a><button class="menu-btn" type="button" aria-controls="navlinks" aria-expanded="false" id="menubtn">Menu</button></div>
</div></header>'''

def footer():
    trades = "".join(f'<li><a href="{L(t["slug"])}">{t["name"]} websites</a></li>' for t in TRADES)
    return f'''<footer class="site-footer"><div class="wrap">
<div class="foot-grid">
 <div class="stack">{brand(light=True)}<p>Done-for-you websites for home service businesses across the United States. Built to rank, built to book.</p>
 <p>30 N Gould St, Sheridan, WY 82801<br><a href="tel:{TEL}">{PHONE}</a><br><a href="mailto:{EMAIL}">{EMAIL}</a></p>
 <p><a href="{FB}" rel="noopener">Facebook</a> &nbsp;.&nbsp; <a href="{IG}" rel="noopener">Instagram</a></p></div>
 <div><h3>Industries</h3><ul>{trades}</ul></div>
 <div><h3>Services</h3><ul>
  <li><a href="{L("home-service-website-design")}">Home service website design</a></li>
  <li><a href="{L("local-seo-for-contractors")}">Local SEO for contractors</a></li>
  <li><a href="{L("google-ads-for-contractors")}">Google Ads for contractors</a></li>
  <li><a href="{L("done-for-you-vs-website-builder")}">Done for you vs DIY builder</a></li>
  <li><a href="{L("pricing")}">Pricing</a></li></ul></div>
 <div><h3>Company</h3><ul>
  <li><a href="{L("about")}">About</a></li><li><a href="{L("how-it-works")}">How it works</a></li><li><a href="{L("our-work")}">Our work</a></li>
  <li><a href="{L("faq")}">FAQ</a></li><li><a href="{L("blog")}">Blog</a></li><li><a href="{L("contact")}">Contact</a></li>
  <li><a href="{L("privacy")}">Privacy Policy</a></li><li><a href="{L("terms")}">Terms of Service</a></li></ul></div>
</div>
<div class="foot-base"><span>&copy; {date.today().year} SitesThatBook. All rights reserved.</span><span>Websites for US home service businesses. {SETUP} setup, {MONTHLY}/month, live in 48 hours.</span></div>
</div></footer>
<div class="callbar"><a class="btn btn-ghost" href="tel:{TEL}">Call us</a><a class="btn btn-primary" href="{L("get-started")}">Get my site</a></div>'''

SCRIPT = '''<script>
(function(){var b=document.getElementById("menubtn"),n=document.getElementById("navlinks");if(b&&n){b.addEventListener("click",function(){var o=n.classList.toggle("open");b.setAttribute("aria-expanded",o?"true":"false");b.textContent=o?"Close":"Menu";});}
%s})();
</script>'''
UPLOAD_JS = '''document.querySelectorAll("[data-show-when]").forEach(function(box){var n=box.getAttribute("data-show-when"),v=box.getAttribute("data-show-value");document.querySelectorAll('input[name="'+n+'"]').forEach(function(r){r.addEventListener("change",function(){box.hidden=!(r.checked&&r.value===v);});});});
document.querySelectorAll(".drop input[type=file]").forEach(function(inp){inp.addEventListener("change",function(){var s=inp.parentNode.querySelector(".drop-file");s.textContent=inp.files.length?inp.files[0].name:"No file chosen";inp.parentNode.classList.toggle("has",!!inp.files.length);});});
function shrink(file){return new Promise(function(res){if(!/^image\\/(jpeg|png|webp|heic)/i.test(file.type)||file.size<600000){return res(file);}var img=new Image(),url=URL.createObjectURL(file);img.onload=function(){var m=1800,w=img.width,h=img.height,k=Math.min(1,m/Math.max(w,h));var c=document.createElement("canvas");c.width=Math.round(w*k);c.height=Math.round(h*k);c.getContext("2d").drawImage(img,0,0,c.width,c.height);c.toBlob(function(b){URL.revokeObjectURL(url);res(b?new File([b],file.name.replace(/\\.[^.]+$/,"")+".jpg",{type:"image/jpeg"}):file);},"image/jpeg",0.82);};img.onerror=function(){res(file);};img.src=url;});}
'''
DEPLOY_FORM_JS = '''document.querySelectorAll("form[enctype]").forEach(function(f){f.addEventListener("submit",function(e){e.preventDefault();var btn=f.querySelector("button[type=submit]");btn.disabled=true;btn.textContent="Uploading, please wait...";var fd=new FormData(f),jobs=[];f.querySelectorAll("input[type=file]").forEach(function(inp){if(inp.files.length){jobs.push(shrink(inp.files[0]).then(function(x){fd.set(inp.name,x,x.name);}));}else{fd.delete(inp.name);}});Promise.all(jobs).then(function(){return fetch("/",{method:"POST",body:fd});}).then(function(r){if(!r.ok)throw new Error(r.status);window.location.href="/thanks";}).catch(function(){btn.disabled=false;btn.textContent="Try again";alert("Upload failed. Try fewer photos, or text them to us instead.");});});});'''
PREVIEW_FORM_JS = '''document.querySelectorAll("form[data-netlify]").forEach(function(f){f.addEventListener("submit",function(e){e.preventDefault();var m=f.querySelector(".form-ok");if(m){m.hidden=false;m.focus();}});});'''

def ga_tag():
    if MODE != "deploy" or not GA4_ID:
        return ""
    return f'''<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');
document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href^="tel:"]');if(a){{gtag('event','click_to_call',{{link_url:a.getAttribute('href'),page_path:location.pathname}});}}}});</script>'''

def meta_pixel():
    if MODE != "deploy" or not META_PIXEL_ID:
        return ""
    return f'''<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','{META_PIXEL_ID}');fbq('track','PageView');
document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href^="tel:"]');if(a){{fbq('track','Contact');}}}});</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={META_PIXEL_ID}&ev=PageView&noscript=1"></noscript>'''

def form_script(body):
    if "<form" not in body:
        return SCRIPT % ""
    if MODE != "deploy":
        return SCRIPT % (UPLOAD_JS + PREVIEW_FORM_JS)
    js = open("forms.js").read().replace("__HOOK__", GHL_WEBHOOK).replace("__CLOUD__", CLOUDINARY_CLOUD).replace("__PRESET__", CLOUDINARY_PRESET)
    return SCRIPT % "" + "\n<script>" + js + "</script>"

def page(path, title, desc, body, active="", schema=None, og_type="website", priority="0.7", noindex=False):
    canonical = SITE + ("/" + path if path else "/")
    graph = [ORG, WEBSITE] + (schema or [])
    ld = json.dumps({"@context":"https://schema.org","@graph":graph}, ensure_ascii=False)
    css_href = "/styles.css" if MODE == "deploy" else "styles.css"
    A = "/assets/" if MODE == "deploy" else "assets/"
    robots = '<meta name="robots" content="noindex">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
    doc = f'''<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{ga_tag()}
{meta_pixel()}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{robots}
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="SitesThatBook">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="https://www.sitesthatbook.com/assets/og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://www.sitesthatbook.com/assets/og-image.png"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="theme-color" content="#0A1F44">
<link rel="icon" href="{A}favicon.ico" sizes="any"><link rel="icon" type="image/svg+xml" href="{A}favicon.svg">
<link rel="apple-touch-icon" href="{A}apple-touch-icon.png"><link rel="manifest" href="{A}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700;800&display=swap">
<link rel="stylesheet" href="{css_href}">
<script type="application/ld+json">{ld}</script>
</head>
<body>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
{form_script(body)}
</body>
</html>'''
    f = outfile(path)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    with open(f, "w") as fh:
        fh.write(doc)
    if not noindex:
        PAGES.append((path, priority))

# ---------------------------------------------------------------- shared blocks
def hero(eyebrow, h1, lede, crumbs=None, ctas=True, extra=""):
    cr = ""
    if crumbs:
        parts = [f'<a href="{L(p)}">{n}</a>' for n,p in crumbs[:-1]] + [crumbs[-1][0]]
        cr = f'<nav class="crumbs" aria-label="Breadcrumb">{" &rsaquo; ".join(parts)}</nav>'
    btns = f'<div class="btn-row"><a class="btn btn-primary" href="{L("get-started")}">Get my site in 48 hours</a><a class="btn btn-outline-light" href="tel:{TEL}">Call {PHONE}</a></div>' if ctas else ""
    return f'''<section class="hero"><div class="wrap page-hero"><div class="hero-copy">{cr}<span class="eyebrow">{eyebrow}</span><h1>{h1}</h1><p class="lede">{lede}</p>{btns}{extra}</div></div></section>'''

def proof_row():
    items = ["Live in 48 hours","Money-back guarantee","No contracts","Hosting and SEO included"]
    return '<ul class="proof-row">' + "".join(f"<li>{TICK}{i}</li>" for i in items) + "</ul>"

def devices_mock(trade="Plumbing", headline="Same day plumbing you can count on", alerts=None, domain="yourcompany.com"):
    alerts = alerts or [("New booking","Water heater leaking","9:15 PM . Tonight"),("New review","5 stars on Google","Just now"),("Missed call","Texted back automatically","2 sec ago")]
    tickets = "".join(f'''<div class="dv-ticket t{i}"><span class="t-label">{a}</span><span class="t-main">{b}</span><span class="t-meta">{c}</span></div>''' for i,(a,b,c) in enumerate(alerts[:3]))
    head = f'<div class="ms-bar"><span class="ms-logo"></span><span class="ms-nav"><i></i><i></i><i></i></span><span class="ms-call">Call now</span></div>'
    hero = f'<div class="ms-hero"><span class="ms-kicker">{trade}</span><b>{headline}</b><span class="ms-btns"><span class="b1">Call now</span><span class="b2">Book online</span></span></div>'
    cards = '<div class="ms-cards"><span><i></i>Licensed and insured</span><span><i class="st"></i>4.9 on Google</span><span><i></i>Free estimates</span></div>'
    form = '<div class="ms-form"><span class="f-title">Request service</span><span class="f-field"><i></i></span><span class="f-field"><i></i></span><span class="f-field"><i></i></span><span class="f-btn"><em>Send request</em><em>Booked</em></span></div>'
    return f'''<div class="devices" aria-hidden="true">
 <div class="dv-laptop"><div class="dv-screen"><div class="dv-url"><i></i><i></i><i></i><span>{domain}</span></div>
  <div class="ms ms-desk">{head}<div class="ms-split">{hero}{form}</div>{cards}</div></div><div class="dv-base"></div></div>
 <div class="dv-tablet"><div class="dv-screen"><div class="ms ms-tab">{head}{hero}{cards}</div></div></div>
 <div class="dv-phone"><div class="dv-screen"><div class="ms ms-mob"><div class="ms-bar"><span class="ms-logo"></span><span class="ms-burger"></span></div>{hero}{cards}<div class="ms-sticky"><span>Call</span><span>Book</span></div></div></div></div>
 {tickets}
</div>'''

def phone_mock(trade="Plumbing", headline="Same day plumbing you can count on", t1=("New booking","Water heater leaking","9:15 PM . Tonight"), t2=("New review","5 stars from Dana R.","Just now")):
    return f'''<div class="mock" aria-hidden="true">
 <div class="phone"><div class="screen">
  <div class="screen-top"><div class="screen-bar"><span>yourcompany.com</span><span>{trade}</span></div><strong>{headline}</strong>
   <div class="call"><span class="c1">Call now</span><span class="c2">Book online</span></div></div>
  <div class="screen-body">
   <div class="mini"><i></i><b>Licensed and insured</b></div>
   <div class="mini"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><b>4.9 on Google</b></div>
   <div class="mini"><i></i><b>Serving your city and suburbs</b></div>
   <div class="mini"><i></i><b>Free estimates</b></div>
  </div></div></div>
 <div class="ticket a"><span class="t-label">{t1[0]}</span><span class="t-main">{t1[1]}</span><span class="t-meta">{t1[2]}</span></div>
 <div class="ticket b"><span class="t-label">{t2[0]}</span><span class="t-main">{t2[1]}</span><span class="t-meta">{t2[2]}</span></div>
</div>'''

def trades_grid():
    cards = "".join(f'''<a class="card" href="{L(t["slug"])}">{ico(t["icon"])}<h3>{t["name"]} websites</h3><p>{t["lede"].split(".")[0]}.</p><span class="more">See {t["name"].lower()} websites &rarr;</span></a>''' for t in TRADES)
    return f'<div class="grid g3 trades">{cards}</div>'

INCLUDED = ["5 custom pages written for your trade","Mobile first design with sticky call bar","Click to call and click to text","Lead and booking request form","Fast cloud hosting and SSL","Your domain connected","2 content updates every month","2 SEO blog posts every month","Monthly traffic report","Schema markup and sitemap for Google"]

def steps_block():
    return f'''<div class="steps">
 <div class="step"><span class="when">10 minutes</span><h3>Fill the onboarding form</h3><p>Tell us your trade, services, service area and what makes you different. Add your logo and job photos if you have them.</p></div>
 <div class="step"><span class="when">Hours 1 to 47</span><h3>We build your site</h3><p>We write the copy, design the pages, set up your forms, add SEO and connect everything. You keep running jobs.</p></div>
 <div class="step"><span class="when">Hour 48</span><h3>Your site goes live</h3><p>We walk you through it on a launch call, connect your domain and you are ready to take calls and bookings.</p></div>
</div>'''

def plans(full=False):
    extra_launch = ["Mobile first design","Click to call and booking form","Fast hosting and SSL","Monthly traffic report"] if full else []
    return f'''<div class="plans">
 <div class="plan"><h3>Launch</h3><p class="sub">Your complete 5-page website.</p>
  <div class="price">{SETUP} <small>setup</small></div><div class="sub">then <b>{MONTHLY}/month</b>. No contract.</div>
  {checks(["Live in 48 hours","5 custom pages for your trade","Hosting, SSL and domain connection","2 updates and 2 SEO blog posts a month"]+extra_launch)}
  <a class="btn btn-ghost" href="{L("get-started")}?plan=launch">Start with Launch</a></div>
 <div class="plan featured"><span class="badge">Most popular</span><h3>Get Found</h3><p class="sub">Show up in the Google map pack.</p>
  <div class="price">+$149 <small>/month</small></div><div class="sub">Added to Launch.</div>
  {checks(["Everything in Launch","Google Business Profile setup","5 Google Business posts a month","Automated review requests","Local directory citations"]+(["Quarterly strategy call"] if full else []))}
  <a class="btn btn-primary" href="{L("get-started")}?plan=get-found">Start with Get Found</a></div>
 <div class="plan"><h3>Get Booked</h3><p class="sub">Ads, CRM and follow up, done for you.</p>
  <div class="price">+$499 <small>/month</small></div><div class="sub">Added to Launch.</div>
  {checks(["Everything in Get Found","Managed Google Ads campaign","CRM with instant lead follow up","Missed call text back"]+(["Monthly strategy call"] if full else []))}
  <a class="btn btn-ghost" href="{L("get-started")}?plan=get-booked">Start with Get Booked</a></div>
</div>'''

SHIELD = '<svg class="shield" viewBox="0 0 76 88" aria-hidden="true"><path d="M38 2L72 14v28c0 22-15 37-34 44C19 79 4 64 4 42V14L38 2z" fill="#1D6FF2"/><path d="M24 44l10 10 19-20" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
def guarantee():
    return f'''<div class="guarantee">{SHIELD}<div class="stack"><h2>The launch call guarantee</h2><p class="lede" style="color:var(--ink)">We show you your finished site on a live launch call. If you do not love it and we cannot fix it right there on the call, we refund your {SETUP} setup fee. No hard feelings, no runaround.</p></div></div>'''

def cta_band(h="Ready to get booked?", p=f"Fill the onboarding form today. Your new website is live 48 hours later."):
    return f'''<section class="section tight"><div class="wrap"><div class="cta-band"><div><h2>{h}</h2><p>{p}</p></div><div class="btn-row"><a class="btn btn-light" href="{L("get-started")}">Get my site in 48 hours</a><a class="btn btn-outline-light" href="tel:{TEL}">{PHONE}</a></div></div></div></section>'''

def faq_block(faqs):
    return '<div class="faq">' + "".join(f"<details><summary>{esc(q)}</summary><div><p>{esc(a)}</p></div></details>" for q,a in faqs) + "</div>"

def bw(url, label, title, sub, tone="dark"):
    return f'''<div class="bw" aria-hidden="true"><div class="bw-bar"><i></i><i></i><i></i><span>{url}</span></div>
<div class="bw-hero {tone}"><small>{label}</small><b>{title}</b><small>{sub}</small><div class="bw-btns"><span>Call now</span><span>Free estimate</span></div></div>
<div class="bw-rows"><i></i><i></i><i></i></div></div>'''

WORK = [
 {"key":"oro","name":"ORO Landscaping","url":"https://google.orolandscape.com/","where":"Denver and Boulder, Colorado","trade":"Landscape design and build",
  "short":"Backyard design and build with a 3 step consultation form and a full project gallery.",
  "text":"ORO designs and builds outdoor living spaces across Colorado, from paver patios and fire features to outdoor kitchens and turf. The site opens with a 3 step consultation form right under the headline, backs it with a 4.9 rating and BBB badge, then lets the work sell itself with a gallery of real completed projects.",
  "points":["3 step consultation form above the fold","Click to call and free consultation buttons","Real project gallery by category","Trust strip: rating, reviews, BBB, years of experience"],
  "tags":["Landscaping","Hardscape","Outdoor kitchens","Design and build"]},
 {"key":"gnr","name":"Great Northern Refrigeration","url":"https://www.gnrpdx.com/","where":"Portland, Oregon","trade":"HVAC and refrigeration",
  "short":"Same day HVAC and refrigeration with a 24/7 emergency strip and a free quote form up top.",
  "text":"Great Northern Refrigeration handles commercial, supermarket, residential and industrial HVAC and refrigeration across the Portland metro. The site leads with same day and 24/7 emergency service, puts a free quote form in the first screen, splits services by customer type and lists every city they cover for local search.",
  "points":["Call and free quote buttons pinned to the top","Free quote form in the first screen","24/7 emergency banner","Service area list: Portland, Salem, Eugene, Vancouver and more"],
  "tags":["HVAC","Refrigeration","24/7 emergency","Commercial and residential"]},
 {"key":"ai","name":"A & I Contracting LLC","url":"https://google.aandicontracting.com/","where":"Denver, Colorado","trade":"Home remodeling",
  "short":"Family owned Denver remodeler with a free estimate offer and every trade on one page.",
  "text":"A & I Contracting is a family owned remodeling contractor serving the Denver metro since 2004. The site uses a bold black and white look that matches their brand, puts licensed, insured and BBB accredited in the first screen, runs a limited time offer and walks through every service from full remodels to plumbing.",
  "points":["Free estimate and call buttons in the hero","Licensed, insured and family owned since 2004 up top","Limited time offer banner","Every service with its own card and photo"],
  "tags":["Remodeling","Kitchens and baths","Basements","Free estimates"]},
]

def asset(name):
    return ("/assets/" if MODE == "deploy" else "assets/") + name

def phone_shot(w, full=True):
    img = f'{w["key"]}-full.webp' if full else f'{w["key"]}-top.webp'
    return f'''<a class="shot{" scroll" if full else ""}" href="{w["url"]}" rel="noopener" target="_blank" aria-label="Open the live {w["name"]} website"><span class="shot-frame"><img src="{asset(img)}" alt="Mobile screenshot of the {w["name"]} website built by SitesThatBook" width="420"{"" if not full else " loading=\"lazy\""}></span></a>'''

def work_block(w):
    return f'''<article class="work"><div class="browser">{phone_shot(w)}</div>
<div class="body"><span class="eyebrow">{w["trade"]} . {w["where"]}</span><h3 style="font-size:1.5rem">{w["name"]}</h3><p class="muted">{w["text"]}</p>
{checks(w["points"])}<ul class="tags">{"".join(f"<li>{t}</li>" for t in w["tags"])}</ul>
<p><a class="btn btn-ghost btn-sm" href="{w["url"]}" rel="noopener" target="_blank">Visit the live site</a></p></div></article>'''

def work_cards():
    return '<div class="grid g3">' + "".join(f'''<div class="card work-card">{phone_shot(w, full=False)}<span class="eyebrow">{w["trade"]} . {w["where"]}</span><h3>{w["name"]}</h3><p>{w["short"]}</p><a class="more" href="{w["url"]}" rel="noopener" target="_blank">Visit the live site &rarr;</a></div>''' for w in WORK) + "</div>"

COMPARE_ROWS = [
 ("Who builds it","We do, start to finish","You do, nights and weekends","Their team, on their timeline"),
 ("Time to live","48 hours","Weeks, if it gets finished","4 to 12 weeks"),
 ("Upfront cost",f"{SETUP}","$0 plus your time","$3,000 to $15,000 is common"),
 ("Monthly cost",f"{MONTHLY}, everything included","$20 to $50 plus apps","Often $150 to $500 for hosting and care"),
 ("Written for your trade","Yes","Templates only","Usually"),
 ("SEO setup and schema","Included","Up to you","Often an extra"),
 ("Blog posts every month","2 included","No","Extra"),
 ("Updates","2 a month included","You do them","Billed hourly"),
 ("Contract","None","None","Often 12 months"),
]
def compare_table():
    rows = "".join(f"<tr><th scope=\"row\">{a}</th><td class=\"yes\">{b}</td><td>{c}</td><td>{d}</td></tr>" for a,b,c,d in COMPARE_ROWS)
    return f'<div class="table-wrap"><table><thead><tr><th scope="col"></th><th scope="col">SitesThatBook</th><th scope="col">DIY website builder</th><th scope="col">Typical agency</th></tr></thead><tbody>{rows}</tbody></table></div><p class="form-note" style="margin-top:10px">DIY and agency figures are common market ranges, not quotes from any specific company.</p>'

GLOBAL_FAQ = [
 ("How is my website live in 48 hours?","We only build for home service businesses, so our page structure, copy approach and SEO setup are already proven. You give us your details in a 10 minute onboarding form and our team builds from there. 48 hours later we show you the finished site on a launch call."),
 ("What do you need from me?","Your business name, trade, services, service area, phone number, logo if you have one and a few job photos. No photos? We start with clean stock images and swap yours in later as one of your monthly updates."),
 ("How much does it cost?",f"{SETUP} one-time setup and {MONTHLY} a month. The monthly plan covers hosting, SSL, 2 content updates, 2 SEO blog posts and a monthly traffic report. Get Found adds $149 a month and Get Booked adds $499 a month."),
 ("Is there a contract?","No. Pay month to month and cancel anytime."),
 ("Do I own my domain?","Yes. Your domain stays in your name. If you do not have one yet, we help you pick and register it."),
 ("What if I do not like the design?",f"We fix it on the launch call. If you still do not love it and we cannot fix it there, we refund your {SETUP} setup fee."),
 ("Will my website rank on Google?","Every site is built on a strong SEO base: fast pages, clean headings, service and city content, schema markup and a sitemap sent to Google. Rankings also depend on your competition, reviews and Google Business Profile. That is why we include 2 SEO blog posts a month and offer the Get Found plan for map pack visibility."),
 ("Which trades do you build for?","HVAC, plumbing, roofing, electrical, garage door, landscaping, cleaning, pest control, painting and pressure washing. If you run another home service business, ask us. We probably build for you too."),
]

# ---------------------------------------------------------------- pages
def home():
    t = TRADES[1]
    body = f'''<section class="hero"><div class="wrap hero-grid">
 <div class="hero-copy"><span class="eyebrow">Websites for home service businesses</span>
  <h1>Your website. Live in 48 hours. Built to <em>get you booked.</em></h1>
  <p class="lede">Done-for-you websites for plumbers, HVAC companies, roofers, electricians and every home service pro. {SETUP} to start, {MONTHLY} a month, no contracts. You run the jobs. We make the phone ring.</p>
  <div class="btn-row"><a class="btn btn-primary" href="{L("get-started")}">Get my site in 48 hours</a><a class="btn btn-outline-light" href="{L("our-work")}">See our work</a></div>
  {proof_row()}
 </div>
 {devices_mock()}
</div></section>

<section class="section tight"><div class="wrap"><div class="facts">
 <div class="fact"><b>{SETUP}</b><span>One-time setup</span></div>
 <div class="fact"><b>{MONTHLY}/mo</b><span>Hosting, SEO, updates, blogs</span></div>
 <div class="fact"><b>48 hrs</b><span>From form to live site</span></div>
 <div class="fact"><b>0</b><span>Contracts. Cancel anytime.</span></div>
</div></div></section>

<section class="section mist"><div class="wrap split">
 <div class="stack"><span class="eyebrow">Why your website matters</span><h2>Right now, someone in your area is searching for exactly what you do</h2>
  <p class="lede">They pick from the first few results that look trustworthy and load fast on a phone. If your site is slow, outdated or missing, that job goes to a competitor who is not half as good as you.</p>
  <p class="muted">A SitesThatBook website is built for one outcome: turning those searches into calls, texts and booking requests. Every page is written for your trade, every button leads to your phone and every site ships with the SEO groundwork Google expects.</p></div>
 <div class="searches" aria-label="Example searches homeowners type">
  {"".join(f'<div class="search">{SEARCH_ICO}<span>{s}</span></div>' for s in ["plumber near me","ac repair open now","roof leak repair","garage door spring broken","electrician for panel upgrade"])}
 </div>
</div></section>

<section class="section"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Industries</span><h2>Websites for every home service trade</h2><p class="lede">Each trade gets copy, pages and features that match how its customers search and buy. No generic templates with your logo slapped on.</p></div>
 {trades_grid()}
</div></section>

<section class="section mist"><div class="wrap">
 <div class="section-head"><span class="eyebrow">How it works</span><h2>Form today. Live website in 48 hours.</h2><p class="lede">Three steps. Your part takes about 10 minutes.</p></div>
 {steps_block()}
 <p style="margin-top:28px"><a href="{L("how-it-works")}">See the full process &rarr;</a></p>
</div></section>

<section class="section"><div class="wrap split">
 <div class="stack"><span class="eyebrow">What you get</span><h2>Everything you need. Nothing you don't.</h2><p class="lede">Your {MONTHLY} a month keeps the site fast, secure, updated and growing in search. No surprise invoices.</p>{checks(INCLUDED, cols=True)}</div>
 {phone_mock("HVAC","No heat? We answer 24/7",("New booking","No heat, gas furnace","7:42 AM . Today"),("New lead","AC tune up request","Booked for Thu"))}
</div></section>

<section class="section mist"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Built to rank</span><h2>SEO built into every site, not bolted on later</h2><p class="lede">Google and AI search tools like ChatGPT need to read your site to recommend you. We build every site so they can.</p></div>
 <div class="grid g3">
  <div class="card"><h3>Fast, crawlable pages</h3><p>Lightweight pages that load fast on phones, with all content in plain HTML that Google can read on the first visit.</p></div>
  <div class="card"><h3>Service and city content</h3><p>Every service you offer and every city you cover is written into the site so you match local searches.</p></div>
  <div class="card"><h3>Schema markup</h3><p>Structured data tells Google your business type, services, phone, hours and service area.</p></div>
  <div class="card"><h3>2 blog posts a month</h3><p>Fresh, useful articles around the questions your customers ask, published for you every month.</p></div>
  <div class="card"><h3>Google Business ready</h3><p>Name, address and phone match your Google Business Profile so your website and map listing support each other.</p></div>
  <div class="card"><h3>Traffic report</h3><p>A simple monthly report showing visits, top pages and where your traffic comes from.</p></div>
 </div>
 <p style="margin-top:28px"><a href="{L("local-seo-for-contractors")}">Learn about local SEO for contractors &rarr;</a></p>
</div></section>

<section class="section"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Our work</span><h2>Live sites we have built for home service pros</h2><p class="lede">Real businesses, real sites, live right now. Tap any one to open it.</p></div>
 {work_cards()}
 <p style="margin-top:28px"><a href="{L("our-work")}">See the full breakdown of each site &rarr;</a></p>
</div></section>

<section class="section mist" id="pricing"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Pricing</span><h2>Simple pricing. No contracts.</h2><p class="lede">Every plan starts with Launch. Add local SEO or ads whenever you are ready.</p></div>
 {plans()}
 <p style="margin-top:24px"><a href="{L("pricing")}">Compare every feature &rarr;</a></p>
</div></section>

<section class="section"><div class="wrap">{guarantee()}</div></section>

<section class="section mist"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Compare</span><h2>SitesThatBook vs doing it yourself vs a typical agency</h2></div>
 {compare_table()}
</div></section>

<section class="section"><div class="wrap">
 <div class="section-head"><span class="eyebrow">FAQ</span><h2>Questions home service owners ask us</h2></div>
 {faq_block(GLOBAL_FAQ)}
 <p style="margin-top:24px"><a href="{L("faq")}">See all questions &rarr;</a></p>
</div></section>
{cta_band()}'''
    page("", "Home Service Websites, Live in 48 Hours | SitesThatBook",
         f"Done-for-you websites for plumbers, HVAC, roofers, electricians and home service pros. {SETUP} setup, {MONTHLY}/month, live in 48 hours. Hosting, SEO and blogs included.",
         body, schema=[faq_schema(GLOBAL_FAQ)], priority="1.0")

def trade_page(t):
    others = [x for x in TRADES if x["slug"] != t["slug"]][:4]
    body = f'''<section class="hero"><div class="wrap hero-grid">
 <div class="hero-copy"><nav class="crumbs" aria-label="Breadcrumb"><a href="{L("")}">Home</a> &rsaquo; <a href="{L("industries")}">Industries</a> &rsaquo; {t["name"]} websites</nav>
  <span class="eyebrow">{t["kw"]}</span><h1>{t["h1"]}</h1><p class="lede">{t["lede"]}</p>
  <div class="btn-row"><a class="btn btn-primary" href="{L("get-started")}?trade={t["slug"]}">Get my {t["name"].lower()} site</a><a class="btn btn-outline-light" href="#pricing">See pricing</a></div>{proof_row()}</div>
 {devices_mock(t["name"], f"Trusted {t['name'].lower()} pros in your area", [t["example"], ("New review","5 stars on Google","Just now"), ("Missed call","Texted back automatically","2 sec ago")])}
</div></section>

<section class="section mist"><div class="wrap split">
 <div class="stack"><span class="eyebrow">What your customers search</span><h2>Homeowners are searching for {t["who"]} right now</h2><p class="lede">These are the kinds of searches your website needs to answer. We build pages and sections around them so Google can match you to the job.</p></div>
 <div class="searches">{"".join(f'<div class="search">{SEARCH_ICO}<span>{s}</span></div>' for s in t["searches"])}</div>
</div></section>

<section class="section"><div class="wrap">
 <div class="section-head"><span class="eyebrow">The problem</span><h2>Why most {t["name"].lower()} websites lose jobs</h2></div>
 <div class="grid g2">{"".join(f'<div class="card"><h3>{a}</h3><p>{b}</p></div>' for a,b in t["pains"])}</div>
</div></section>

<section class="section mist"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Built for {t["name"].lower()}</span><h2>What goes into every {t["name"].lower()} website we build</h2><p class="lede">Features picked for how {t["who"]} actually win work.</p></div>
 <div class="grid g3">{"".join(f'<div class="card"><h3>{a}</h3><p>{b}</p></div>' for a,b in t["features"])}</div>
</div></section>

<section class="section"><div class="wrap split">
 <div class="stack"><span class="eyebrow">Your 5 pages</span><h2>The pages we build for your {t["name"].lower()} business</h2><p class="lede">Every page is written for your company, your services and your service area. You review it all on the launch call.</p>
  <ol class="checks" style="list-style:none">{"".join(f"<li>{TICK}<span>{p}</span></li>" for p in t["pages"])}</ol></div>
 <div class="stack"><h3>Also included every month</h3>{checks(["Hosting, SSL and domain connection","2 content updates","2 SEO blog posts written for "+t["who"],"Monthly traffic report","Schema markup and sitemap"])}</div>
</div></section>

<section class="section mist"><div class="wrap">
 <div class="section-head"><span class="eyebrow">How it works</span><h2>Your {t["name"].lower()} website, live in 48 hours</h2></div>
 {steps_block()}
</div></section>

<section class="section" id="pricing"><div class="wrap">
 <div class="section-head"><span class="eyebrow">Pricing</span><h2>{t["name"]} website pricing</h2><p class="lede">{SETUP} setup and {MONTHLY} a month. Add map pack SEO or Google Ads when you are ready.</p></div>
 {plans()}
</div></section>

<section class="section mist"><div class="wrap">{guarantee()}</div></section>

<section class="section"><div class="wrap">
 <div class="section-head"><span class="eyebrow">FAQ</span><h2>{t["name"]} website questions</h2></div>
 {faq_block(t["faqs"])}
</div></section>

<section class="section mist tight"><div class="wrap">
 <div class="section-head"><h2>Other trades we build for</h2></div>
 <div class="grid g4">{"".join(f'<a class="card" href="{L(o["slug"])}">{ico(o["icon"])}<h3>{o["name"]} websites</h3><span class="more">View &rarr;</span></a>' for o in others)}</div>
</div></section>
{cta_band(f"Ready for a {t['name'].lower()} website that books jobs?")}'''
    page(t["slug"], t["title"], t["meta"], body, active="industries", priority="0.9",
         schema=[service_schema(f"{t['name']} website design", t["meta"], t["slug"]), faq_schema(t["faqs"]),
                 crumbs_schema([("Home",""),("Industries","industries"),(f"{t['name']} websites",t["slug"])])])

def industries():
    body = hero("Industries","Websites built for <em>home service</em> businesses","We only build for home service pros. That focus is why we can go live in 48 hours and why every site speaks your customers' language.",crumbs=[("Home",""),("Industries","")]) + f'''
<section class="section"><div class="wrap">{trades_grid()}</div></section>
<section class="section mist"><div class="wrap split"><div class="stack"><h2>Don't see your trade?</h2><p class="lede">Handyman, flooring, fencing, pool service, appliance repair, junk removal, window cleaning, solar and more. If you serve homeowners, we can build for you.</p></div><div><a class="btn btn-primary" href="{L("contact")}">Ask about your trade</a></div></div></section>
{cta_band()}'''
    page("industries","Website Design for Home Service Industries | SitesThatBook",
         "Websites for HVAC, plumbing, roofing, electrical, garage door, landscaping, cleaning, pest control, painting and pressure washing companies. Live in 48 hours.",
         body, active="industries", priority="0.8", schema=[crumbs_schema([("Home",""),("Industries","industries")])])

def pricing():
    rows = [("5 custom pages","Yes","Yes","Yes"),("Live in 48 hours","Yes","Yes","Yes"),("Hosting, SSL, domain connection","Yes","Yes","Yes"),
            ("2 content updates a month","Yes","Yes","Yes"),("2 SEO blog posts a month","Yes","Yes","Yes"),("Monthly traffic report","Yes","Yes","Yes"),
            ("Google Business Profile setup","No","Yes","Yes"),("5 Google Business posts a month","No","Yes","Yes"),("Automated review requests","No","Yes","Yes"),
            ("Local directory citations","No","Yes","Yes"),("Managed Google Ads campaign","No","No","Yes"),("CRM with instant lead follow up","No","No","Yes"),
            ("Missed call text back","No","No","Yes"),("Strategy calls","No","Quarterly","Monthly")]
    def cell(v): return f'<td class="{"yes" if v!="No" else "no"}">{v}</td>'
    table = '<div class="table-wrap"><table><thead><tr><th scope="col">Feature</th><th scope="col">Launch</th><th scope="col">Get Found</th><th scope="col">Get Booked</th></tr></thead><tbody>' + "".join(f'<tr><th scope="row">{a}</th>{cell(b)}{cell(c)}{cell(d)}</tr>' for a,b,c,d in rows) + "</tbody></table></div>"
    pf = [("Why is there a setup fee?",f"The {SETUP} covers writing your copy, designing your pages, setting up forms, SEO and connecting your domain. It is the only upfront cost."),
          ("What does the $99 a month cover?","Hosting, SSL security, 2 content updates, 2 SEO blog posts and a monthly traffic report. Your site stays fast, secure and growing."),
          ("Are Google Ads costs included in Get Booked?","The $499 a month covers managing your campaign, the CRM and follow up tools. Your ad spend is paid directly to Google, so you control the budget."),
          ("Can I upgrade or downgrade?","Yes. Add Get Found or Get Booked anytime, or drop back to Launch at the end of any month."),
          ("Can I cancel?","Yes. No contracts. Cancel anytime.")]
    body = hero("Pricing",f"Simple pricing. <em>{SETUP}</em> setup, <em>{MONTHLY}</em> a month.","No contracts, no hidden fees. Every plan starts with Launch. Add local SEO or ads when you want more calls.",crumbs=[("Home",""),("Pricing","")]) + f'''
<section class="section"><div class="wrap">{plans(full=True)}</div></section>
<section class="section mist"><div class="wrap"><div class="section-head"><h2>Compare plans</h2></div>{table}</div></section>
<section class="section"><div class="wrap">{guarantee()}</div></section>
<section class="section mist"><div class="wrap"><div class="section-head"><h2>Compared to the alternatives</h2></div>{compare_table()}</div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>Pricing questions</h2></div>{faq_block(pf)}</div></section>
{cta_band()}'''
    offer = {"@type":"OfferCatalog","name":"SitesThatBook plans","itemListElement":[
        {"@type":"Offer","name":"Launch","price":"349","priceCurrency":"USD","description":"$349 setup plus $99 per month. 5-page website live in 48 hours."},
        {"@type":"Offer","name":"Get Found","price":"149","priceCurrency":"USD","description":"Adds $149 per month to Launch. Google Business Profile, posts, reviews, citations."},
        {"@type":"Offer","name":"Get Booked","price":"499","priceCurrency":"USD","description":"Adds $499 per month to Launch. Google Ads management, CRM, missed call text back."}]}
    page("pricing",f"Pricing: {SETUP} Setup, {MONTHLY}/Month, No Contracts | SitesThatBook",
         f"Home service website pricing: {SETUP} setup and {MONTHLY}/month with hosting, updates and SEO blog posts. Add local SEO for $149/month or Google Ads for $499/month.",
         body, active="pricing", priority="0.9", schema=[offer, faq_schema(pf), crumbs_schema([("Home",""),("Pricing","pricing")])])

def how_it_works():
    need = ["Business name, phone and email","Your trade and the services you offer","Cities and areas you serve","License number and insurance details, if you have them","Logo, if you have one","5 to 15 job photos, if you have them","Your domain name, or the one you want","Anything that makes you different: years in business, guarantees, financing"]
    hf = [("What if I don't have a logo?","We create a clean text logo so you can launch on time. You can swap in a designed logo later."),
          ("What if I don't have photos?","We use professional stock images that fit your trade. Send real job photos anytime and we swap them in."),
          ("What happens on the launch call?","We share our screen, walk you through every page, make quick changes on the spot, connect your domain and go live."),
          ("What happens after launch?","Each month we publish 2 SEO blog posts, make up to 2 updates you request and send your traffic report.")]
    body = hero("How it works","From onboarding form to <em>live website</em> in 48 hours","Your part takes about 10 minutes. We handle the writing, design, SEO, hosting and setup.",crumbs=[("Home",""),("How it works","")]) + f'''
<section class="section"><div class="wrap">{steps_block()}</div></section>
<section class="section mist"><div class="wrap split">
 <div class="stack"><span class="eyebrow">Step 1</span><h2>What we ask for in the onboarding form</h2><p class="lede">Short and simple. If you do not have something yet, skip it. We fill the gaps so you still launch on time.</p></div>
 <div>{checks(need)}</div></div></section>
<section class="section"><div class="wrap split">
 <div class="stack"><span class="eyebrow">Step 2</span><h2>What we do while you work</h2><p class="lede">Our team writes your copy for your trade and city, designs your 5 pages, sets up click to call and your request form, adds schema markup and builds your sitemap.</p></div>
 <div>{checks(["Copy written for your trade and service area","Mobile first design with sticky call bar","Lead form connected to your phone and email","Page titles, descriptions and headings set for search","Schema markup and sitemap","Speed and mobile checks before launch"])}</div></div></section>
<section class="section mist"><div class="wrap split">
 <div class="stack"><span class="eyebrow">Step 3</span><h2>Launch call and go live</h2><p class="lede">48 hours after your form, we walk you through the finished site on a call, make changes on the spot and connect your domain. If you do not love it and we cannot fix it right there, you get your {SETUP} back.</p></div>
 <div>{checks(["Live walkthrough of every page","Quick edits made on the call","Domain connected","Site submitted to Google"])}</div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>Process questions</h2></div>{faq_block(hf)}</div></section>
{cta_band()}'''
    howto = {"@type":"HowTo","name":"How to get a SitesThatBook website live in 48 hours","totalTime":"PT48H","step":[
        {"@type":"HowToStep","position":1,"name":"Fill the onboarding form","text":"Share your trade, services, service area, logo and photos. Takes about 10 minutes."},
        {"@type":"HowToStep","position":2,"name":"We build your site","text":"We write the copy, design the pages, set up forms and add SEO."},
        {"@type":"HowToStep","position":3,"name":"Go live","text":"48 hours later we walk you through the site on a launch call and connect your domain."}]}
    page("how-it-works","How It Works: Website Live in 48 Hours | SitesThatBook",
         "Fill a 10 minute onboarding form. We write, design and set up your home service website. It goes live 48 hours later on a launch call.",
         body, active="how-it-works", priority="0.8", schema=[howto, faq_schema(hf), crumbs_schema([("Home",""),("How it works","how-it-works")])])

def our_work():
    body = hero("Our work","Live websites for <em>real home service</em> businesses","A look at sites we have built and launched. Visit them live and judge the work yourself.",crumbs=[("Home",""),("Our work","")]) + f'''
<section class="section"><div class="wrap">{"".join(work_block(w) for w in WORK)}</div></section>
<section class="section mist"><div class="wrap split"><div class="stack"><h2>What every site we build has in common</h2><p class="lede">Different trades, same standard.</p></div><div>{checks(["A clear headline that says what you do and where","Call and estimate buttons on every screen","Trust signals up top: license, insurance, reviews","One section per service so Google can match each search","Service area written out city by city","Fast on phones"])}</div></div></section>
{cta_band("Want yours next?")}'''
    page("our-work","Our Work: Home Service Websites We Built | SitesThatBook",
         "Live websites we built for home service businesses: ORO Landscaping in Colorado, Great Northern Refrigeration in Portland and A & I Contracting in Denver.",
         body, active="our-work", priority="0.7", schema=[crumbs_schema([("Home",""),("Our work","our-work")])])

def about():
    body = hero("About","We build websites for the people who <em>keep homes running</em>","SitesThatBook exists for one reason: home service pros deserve a website that brings in work, without paying agency prices or losing weekends to a website builder.",crumbs=[("Home",""),("About","")]) + f'''
<section class="section"><div class="wrap split">
 <div class="prose"><h2>Why we started</h2>
 <p>Most plumbers, HVAC techs and roofers we talked to had the same story. Either they had no website, a site a relative built years ago, or they paid an agency thousands and waited months for something that still did not bring in calls.</p>
 <p>We knew the problem was not the trade. It was the website. So we built a simple offer: a professional site written for your trade, live in 48 hours, for {SETUP} to start and {MONTHLY} a month, with hosting, updates and SEO handled for you.</p>
 <h2>Who is behind SitesThatBook</h2>
 <p>SitesThatBook is built by the team behind Leads Magnets, a Google Partner performance marketing agency. Our founder, Mostafa Dabour, has spent more than 14 years running paid media and lead generation on Google, Meta and TikTok for businesses in the US, UK and Australia.</p>
 <p>That background shapes every site we build. We know what makes someone pick up the phone, because we have spent years tracking which pages, headlines and buttons turn clicks into booked jobs.</p></div>
 <div class="stack">
  <div class="card"><h3>Home service only</h3><p>We do not build sites for restaurants or online stores. Focus is why we are fast.</p></div>
  <div class="card"><h3>Built to book, not to win design awards</h3><p>Every design choice is judged by one test: does it get the call?</p></div>
  <div class="card"><h3>Honest pricing</h3><p>{SETUP} setup, {MONTHLY} a month, no contracts and a money-back guarantee on the setup fee.</p></div>
 </div>
</div></section>
{cta_band()}'''
    person = {"@type":"Person","name":"Mostafa Dabour","jobTitle":"Founder","worksFor":{"@id":SITE+"/#org"}}
    page("about","About SitesThatBook | Websites for Home Service Pros",
         "SitesThatBook builds done-for-you websites for US home service businesses. Built by the team behind Leads Magnets, a Google Partner agency.",
         body, active="about", priority="0.6", schema=[person, crumbs_schema([("Home",""),("About","about")])])

def faq_page():
    more = [("Can customers book from my website?","Yes. Every site has click to call, click to text and a booking request form. Requests arrive on your phone and email right away."),
            ("Can I make changes after launch?","Yes. 2 content updates a month are included. Text or email what you want changed."),
            ("Do you write the content?","Yes. We write all the copy from your onboarding form. You review it on the launch call."),
            ("Will my site work on phones?","Every site is designed mobile first with a sticky call bar, because most of your customers will find you on a phone."),
            ("What is the Get Found plan?","It adds Google Business Profile setup and management, 5 Google Business posts a month, automated review requests and local directory citations for $149 a month."),
            ("What is the Get Booked plan?","It adds a managed Google Ads campaign, a CRM with instant lead follow up and missed call text back for $499 a month. Ad spend is paid to Google separately."),
            ("Do you serve businesses outside the US?","We focus on US home service businesses."),
            ("Can you move my existing website?","Yes. We rebuild it on our platform and connect your existing domain, so you keep your web address.")]
    allf = GLOBAL_FAQ + more
    body = hero("FAQ","Questions, <em>answered</em>","Everything home service owners ask before getting a site with us. Still curious? Call or text "+PHONE+".",crumbs=[("Home",""),("FAQ","")],ctas=False) + f'''
<section class="section"><div class="wrap">{faq_block(allf)}</div></section>{cta_band()}'''
    page("faq","FAQ: Websites for Home Service Businesses | SitesThatBook",
         "Answers about SitesThatBook websites: pricing, the 48 hour timeline, what we need from you, SEO, domains, updates, contracts and our money-back guarantee.",
         body, active="", priority="0.7", schema=[faq_schema(allf), crumbs_schema([("Home",""),("FAQ","faq")])])

def trade_options(selected=""):
    return "".join(f'<option value="{t["name"]}">{t["name"]}</option>' for t in TRADES) + '<option value="Other">Other home service</option>'

def form_html(name, fields_html, button, ok):
    return f'''<form class="form" name="{name}" method="POST" data-stb="1" data-netlify="true">
<p hidden><label>Leave empty <input name="company_website"></label></p>
{fields_html}
{"" if "data-step-next" in fields_html else f'<div class="full"><button class="btn btn-primary" type="submit">{button}</button></div>'}
<p class="form-note full">We reply within one business day. We never share your details.</p>
<div class="form-ok full" hidden tabindex="-1">{ok}</div>
<div class="form-err full" hidden>Something went wrong sending your form. Call or text {PHONE} and we will sort it out right away.</div>
</form>'''

def field(id_, label, type_="text", full=False, req=True, hint="", ph=""):
    r = " required" if req else ""
    cls = "field full" if full else "field"
    h = f'<span class="hint">{hint}</span>' if hint else ""
    if type_ == "textarea":
        inp = f'<textarea id="{id_}" name="{id_}" placeholder="{ph}"{r}></textarea>'
    else:
        inp = f'<input id="{id_}" name="{id_}" type="{type_}" placeholder="{ph}"{r}>'
    return f'<div class="{cls}"><label for="{id_}">{label}</label>{inp}{h}</div>'

def radios(name, legend, options, hint=""):
    opts = "".join(f'<label class="opt"><input type="radio" name="{name}" value="{v}"><span>{v}</span></label>' for i,v in enumerate(options))
    h = f'<span class="hint">{hint}</span>' if hint else ""
    return f'<fieldset class="field full choice"><legend>{legend}</legend><div class="opts">{opts}</div>{h}</fieldset>'

def file_input(id_, label, accept="image/*"):
    return f'<label class="drop" for="{id_}"><input id="{id_}" name="{id_}" type="file" accept="{accept}"><span class="drop-label">{label}</span><span class="drop-file" aria-live="polite">No file chosen</span></label>'

PHOTO_SLOTS = 6
def brand_section():
    logo_opts = ["Yes, I will upload it now","Yes, but I will send it later","No, make me a clean text logo for now","No, I want a designed logo (ask me about it)"]
    photo_opts = ["Yes, I will upload some now","Yes, I will share a Google Drive or Dropbox link","Yes, I will text them to you","No, use quality stock photos for now"]
    photos = "".join(file_input(f"photo{i}", f"Photo {i}") for i in range(1, PHOTO_SLOTS+1))
    return f'''<div class="form-group full"><h3>Your logo</h3><p class="form-note">A logo is not required to launch. We can start with a clean text logo and swap yours in anytime.</p></div>
{radios("has_logo","Do you have a logo?",logo_opts)}
<div class="full uploads" data-show-when="has_logo" data-show-value="{logo_opts[0]}" hidden>
 {file_input("logo","Upload your logo","image/*,.svg,.pdf")}
 <span class="hint">PNG, JPG, SVG or PDF. A version on a transparent or white background works best.</span>
</div>
<div class="form-group full"><h3>Photos of your work</h3><p class="form-note">Real job photos build more trust than any stock image. Trucks, crews, finished jobs, before and afters all work.</p></div>
{radios("has_photos","Do you have photos of your work or team?",photo_opts)}
<div class="full uploads" data-show-when="has_photos" data-show-value="{photo_opts[0]}" hidden>
 <div class="drops">{photos}</div>
 <span class="hint">Up to {PHOTO_SLOTS} photos. We shrink them automatically so the upload is quick. Got more? Send a link below or text them to {PHONE}.</span>
</div>
<div class="full" data-show-when="has_photos" data-show-value="{photo_opts[1]}" hidden>{field("photo_link","Photo folder link","url",req=False,ph="https://drive.google.com/...",hint="Make sure the folder is set to anyone with the link can view.")}</div>
{field("brand_colors","Brand colors or sites you like",full=True,req=False,ph="Navy and orange, like our trucks. We like the look of example.com",hint="Optional. Helps us match your style.")}
'''

def get_started():
    step1 = ('<div class="form-step-head full"><span class="step-pill">Step 1 of 2</span><h3>Start here. Takes 30 seconds.</h3><p class="form-note">We will reach out to you right after this step, even if you stop here.</p></div>' +
              field("name","Your name",ph="Mike Johnson") + field("business","Business name",ph="Johnson Plumbing LLC") +
              f'<div class="field"><label for="trade">Your trade</label><select id="trade" name="trade" required><option value="">Choose your trade</option>{trade_options()}</select></div>' +
              field("phone","Mobile phone","tel",ph="(555) 123 4567") + field("email","Email","email",full=True,ph="you@yourcompany.com") +
              '<div class="full step1-actions"><button class="btn btn-primary" type="button" data-step-next>Continue</button><span class="form-note">No payment needed to start.</span></div>')
    step2 = ('<div class="full step2" hidden>' +
              '<div class="form-grid">' +
              '<div class="form-step-head full"><span class="step-pill done">Step 1 done</span><h3>Step 2: Tell us about your business</h3><p class="form-note">Fill what you can now so we can start building right away. Anything you skip, we will cover on your launch call.</p></div>' +
              f'<div class="field full"><label for="plan">Plan</label><select id="plan" name="plan"><option>Launch ({SETUP} + {MONTHLY}/mo)</option><option>Get Found (+$149/mo)</option><option>Get Booked (+$499/mo)</option><option>Not sure yet</option></select></div>' +
              field("area","Cities or areas you serve",full=True,req=False,ph="Austin, Round Rock, Cedar Park, Georgetown") +
              field("services","Main services you offer","textarea",full=True,req=False,ph="Drain cleaning, water heaters, leak repair, repiping") +
              field("domain","Current website or domain",req=False,hint="Leave blank if you don't have one yet.",ph="johnsonplumbing.com") +
              field("license","License number",req=False,hint="Optional. Shown on your site to build trust.") +
              brand_section() +
              field("notes","Anything else we should know?","textarea",full=True,req=False,ph="Years in business, guarantees, financing, what makes you different") +
              '<div class="full step2-actions"><button class="btn btn-primary" type="submit">Send my details</button><a class="skip-link" href="/thanks" data-skip>Skip for now, we will cover it on the call</a></div>' +
              '</div></div>')
    fields = step1 + step2
    body = hero("Get started","Fill the form. <em>48 hours later</em> your website is live.","Start with your name and number. It takes 30 seconds. Add your business details now or on your launch call, whichever is easier.",crumbs=[("Home",""),("Get started","")],ctas=False) + f'''
<section class="section"><div class="wrap split" style="align-items:start">
 {form_html("onboarding", fields, "Send my onboarding form", "Got it. Your form and files are in. We will call or text you shortly to confirm your details and lock in your launch time.")}
 <div class="stack">
  <h2 style="font-size:1.6rem">What happens next</h2>
  <div class="steps" style="grid-template-columns:1fr">
   <div class="step"><span class="when">Today</span><h3>We review your form</h3><p>We reach out to confirm details, collect your logo and photos and take care of the {SETUP} setup.</p></div>
   <div class="step"><span class="when">Next 48 hours</span><h3>We build</h3><p>Copy, design, forms, SEO and hosting, all done for you.</p></div>
   <div class="step"><span class="when">Launch call</span><h3>You go live</h3><p>We walk you through it, make edits and connect your domain.</p></div>
  </div>
  <p class="muted">Rather talk first? Call or text <a href="tel:{TEL}">{PHONE}</a> or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
 </div>
</div></section>'''
    page("get-started","Get Started: Your Website Live in 48 Hours | SitesThatBook",
         f"Fill the SitesThatBook onboarding form and get a done-for-you home service website live in 48 hours. {SETUP} setup, {MONTHLY}/month, no contracts.",
         body, priority="0.8", schema=[crumbs_schema([("Home",""),("Get started","get-started")])])

def contact():
    fields = (field("name","Your name") + field("phone","Phone","tel") + field("email","Email","email",full=True) +
              field("notes","How can we help?","textarea",full=True))
    body = hero("Contact","Talk to a <em>real person</em>","Questions about your trade, pricing or the process? Call, text, email or send the form.",crumbs=[("Home",""),("Contact","")],ctas=False) + f'''
<section class="section"><div class="wrap split" style="align-items:start">
 <div class="stack">
  <div class="card"><h3>Call or text</h3><p><a href="tel:{TEL}">{PHONE}</a></p></div>
  <div class="card"><h3>Email</h3><p><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
  <div class="card"><h3>Mailing address</h3><p>30 N Gould St, Sheridan, WY 82801</p></div>
  <div class="card"><h3>Ready to start?</h3><p>Skip the back and forth and fill the onboarding form.</p><p><a class="btn btn-primary btn-sm" href="{L("get-started")}">Get my site</a></p></div>
 </div>
 {form_html("contact", fields, "Send message", "Thanks. We will get back to you within one business day.")}
</div></section>'''
    page("contact","Contact SitesThatBook | Call, Text or Email",
         f"Contact SitesThatBook about a website for your home service business. Call or text {PHONE} or email {EMAIL}.",
         body, priority="0.5", schema=[crumbs_schema([("Home",""),("Contact","contact")])])

def thanks():
    body = hero("Thank you","Got it. <em>We are on it.</em>",f"We will call or text you shortly to confirm your details. Questions in the meantime? Call {PHONE}.",ctas=False) + cta_band("While you wait","See the sites we have already launched for home service pros.")
    page("thanks","Thank You | SitesThatBook","Thanks for contacting SitesThatBook.", body, noindex=True)

def service_page(path, title, meta, eyebrow, h1, lede, sections, faqs, name):
    body = hero(eyebrow,h1,lede,crumbs=[("Home",""),(eyebrow,"")]) + sections + f'''
<section class="section mist"><div class="wrap"><div class="section-head"><h2>Questions</h2></div>{faq_block(faqs)}</div></section>{cta_band()}'''
    page(path, title, meta, body, priority="0.8", schema=[service_schema(name, meta, path), faq_schema(faqs), crumbs_schema([("Home",""),(eyebrow,path)])])

def services():
    service_page("home-service-website-design",
      "Home Service and Contractor Website Design | SitesThatBook",
      f"Website design for contractors and home service businesses. Written for your trade, built to rank and convert. {SETUP} setup, {MONTHLY}/month, live in 48 hours.",
      "Home service website design","Contractor website design that <em>turns visitors into jobs</em>",
      "Your website should work like your best salesperson: answer questions, build trust and get the homeowner to call. We design every page around that job.",
      f'''<section class="section"><div class="wrap split"><div class="prose"><h2>What makes a home service website convert</h2>
<p>Homeowners decide in seconds. They need to see what you do, where you work and how to reach you before they scroll. Then they look for proof: reviews, licenses, photos and a clear process.</p>
<p>Every SitesThatBook site follows a layout built around those moments. A headline that names your service and city. Call and estimate buttons that stay on screen. Trust signals near the top. One section for each service. A service area written out town by town. A short form that collects the details you need to quote.</p>
<h2>Designed for phones first</h2><p>Most of your customers will find you on a phone, often while something is broken. We design for that screen first, with a sticky call bar and big tap targets, then scale up to desktop.</p></div>
<div class="stack"><h3>Included in every site</h3>{checks(INCLUDED)}</div></div></section>
<section class="section mist"><div class="wrap"><div class="section-head"><h2>Website design by trade</h2></div>{trades_grid()}</div></section>''',
      [("How much does contractor website design cost?",f"With SitesThatBook it is {SETUP} setup and {MONTHLY} a month, including hosting, updates and SEO blog posts. Agencies commonly charge several thousand dollars upfront plus monthly care fees."),
       ("How long does it take?","48 hours from your onboarding form to a live site."),
       ("Do I need to provide the copy?","No. We write it for you from your onboarding form.")],
      "Home service website design")

    service_page("local-seo-for-contractors",
      "Local SEO for Contractors and Home Services | SitesThatBook",
      "Local SEO for home service businesses: Google Business Profile management, review requests, citations and monthly blog posts. Get Found plan from $149/month.",
      "Local SEO for contractors","Local SEO that gets you into the <em>Google map pack</em>",
      "The map pack is where most local calls start. Our Get Found plan keeps your Google Business Profile active, brings in reviews and builds the citations Google uses to trust your business.",
      f'''<section class="section"><div class="wrap"><div class="section-head"><h2>What local SEO includes</h2></div><div class="grid g3">
<div class="card"><h3>Google Business Profile setup</h3><p>Categories, services, service area, hours, photos and description set up the right way.</p></div>
<div class="card"><h3>5 posts a month</h3><p>Regular posts keep your profile active and show offers, projects and seasonal services.</p></div>
<div class="card"><h3>Automated review requests</h3><p>Customers get a text asking for a review after the job, so your review count grows every month.</p></div>
<div class="card"><h3>Local citations</h3><p>Your business listed with matching name, address and phone on trusted directories.</p></div>
<div class="card"><h3>2 blog posts a month</h3><p>Included with every site. Articles built around local questions your customers ask.</p></div>
<div class="card"><h3>Quarterly strategy call</h3><p>We review rankings, calls and reviews with you and plan the next quarter.</p></div>
</div></div></section>
<section class="section mist"><div class="wrap split"><div class="prose"><h2>Why your website and map listing need each other</h2><p>Google looks at your website to confirm what your Business Profile says. Matching services, service areas and contact details across both is one of the simplest ways to build trust with Google. That is why every SitesThatBook website is built to support your profile from day one.</p></div><div class="stack"><div class="card"><h3>Get Found plan</h3><div class="price" style="font-family:var(--display);font-weight:800;font-size:2rem;color:var(--navy)">+$149/mo</div><p>Added to your Launch plan.</p><a class="btn btn-primary" href="{L("get-started")}?plan=get-found">Start with Get Found</a></div></div></div></section>
<section class="section"><div class="wrap split" style="align-items:start"><div class="prose">
<h2>What decides who shows up in the map pack?</h2>
<p>Google ranks local results on three things: <b>relevance</b> (does your business match the search), <b>distance</b> (how close you are to the person searching) and <b>prominence</b> (how well known and trusted you are). You cannot move your shop closer to every customer, but you can control relevance and prominence.</p>
<ul><li><b>Relevance</b> comes from the right primary category, a full services list and a website that covers each service and city clearly.</li>
<li><b>Prominence</b> comes from reviews, consistent business listings across the web, links from local sites and an active profile.</li></ul>
<h2>How the Get Found plan works month by month</h2>
<ol><li><b>Month 1:</b> profile audit and cleanup, categories, services, service area, photos and description. Citations submitted to the main directories. Review request automation switched on.</li>
<li><b>Month 2:</b> weekly posts, photo uploads, answers to common questions on your profile and blog posts targeting your top services.</li>
<li><b>Month 3 and on:</b> keep the review flow steady, fill gaps in citations, track calls and direction requests and adjust what we post.</li></ol>
</div><div class="stack">
<div class="card"><h3>What we track for you</h3><p>Calls and website clicks from your profile, direction requests, review count and rating, and where you show up for your main searches.</p></div>
<div class="card"><h3>What we need from you</h3><p>Access to your Google Business Profile, job photos when you have them and a quick reply when a customer leaves a review that needs your voice.</p></div>
<div class="card"><h3>Works with your trade</h3><p>We do local SEO for HVAC, plumbing, roofing, electrical, garage door, landscaping, cleaning, pest control, painting and pressure washing companies.</p></div>
</div></div></section>''',
      [("How long does local SEO take to work?","Most businesses see movement in a few months. It depends on your competition, how many reviews you have and how complete your profile is."),
       ("What is the Google map pack?","It is the group of three local businesses Google shows with a map for searches like plumber near me. Most local calls from Google come from these results."),
       ("How do reviews help local SEO?","More recent reviews with a strong rating make your business look more established to Google and to customers. Our review requests go out by text right after the job, when customers are most likely to respond."),
       ("Do I need a website for local SEO?","A website makes your Google Business Profile far stronger. Google uses it to confirm your services and location."),
       ("Can you guarantee number one rankings?","No honest company can. We do the work that moves rankings and report on it every month.")],
      "Local SEO for contractors")

    service_page("google-ads-for-contractors",
      "Google Ads for Contractors and Home Services | SitesThatBook",
      "Managed Google Ads for home service businesses with CRM, instant lead follow up and missed call text back. Get Booked plan from $499/month plus ad spend.",
      "Google Ads for contractors","Google Ads, CRM and follow up that <em>book jobs on demand</em>",
      "SEO takes time. Google Ads puts you at the top of search today. Our Get Booked plan runs your campaign, follows up with every lead in seconds and texts back missed calls so no job slips away.",
      f'''<section class="section"><div class="wrap"><div class="section-head"><h2>What Get Booked includes</h2></div><div class="grid g2">
<div class="card"><h3>Managed Google Ads campaign</h3><p>Keyword research, ad copy, location targeting and ongoing optimization, run by a team with over 14 years in paid media.</p></div>
<div class="card"><h3>CRM with instant follow up</h3><p>Every form lead gets a text right away, so you reach them before your competitors do.</p></div>
<div class="card"><h3>Missed call text back</h3><p>Miss a call on a job? The caller gets an automatic text so the lead stays with you.</p></div>
<div class="card"><h3>Monthly strategy call</h3><p>We go over spend, calls, cost per lead and booked jobs, then adjust.</p></div>
</div></div></section>
<section class="section mist"><div class="wrap split" style="align-items:start"><div class="prose">
<h2>How we set up Google Ads for a home service business</h2>
<ol><li><b>Keywords with buying intent.</b> We target searches like "water heater repair near me" and "emergency ac repair", not broad terms that bring tire kickers.</li>
<li><b>Negative keywords from day one.</b> Jobs, DIY, free and how to searches are blocked so you do not pay for clicks that will never book.</li>
<li><b>Tight location targeting.</b> Ads only show in the cities and ZIP codes you actually serve, and can be scheduled around your hours.</li>
<li><b>Call tracking and form tracking.</b> We count calls and form leads, not just clicks, so we optimize for booked work.</li>
<li><b>Landing pages that convert.</b> Ads send people to your SitesThatBook site, built with click to call and a short request form.</li></ol>
<h2>Google Ads vs Local Services Ads</h2>
<p>Local Services Ads are the Google Guaranteed listings at the very top of some searches, and you pay per lead. Regular Google Ads give you more control over keywords, budget and where people land. Many home service companies run both. We help you decide what fits your trade and budget.</p>
</div><div class="stack">
<div class="card"><h3>Budget</h3><p>You set the ad budget and pay Google directly. We recommend a starting budget based on your trade, your area and how many jobs you can handle.</p></div>
<div class="card"><h3>Speed to lead</h3><p>Leads that get a reply within minutes book far more often than leads that wait hours. That is why every lead gets an instant text and missed calls get a text back.</p></div>
<div class="card"><h3>Run by paid media pros</h3><p>Campaigns are managed by the Leads Magnets team, a Google Partner agency.</p></div>
</div></div></section>''',
      [("Is ad spend included?","No. The $499 a month covers management and tools. Ad spend is paid directly to Google, so you set the budget."),
       ("Do I need the Launch plan first?","Yes. Get Booked is added to Launch so your ads send people to a site built to convert."),
       ("Can I pause ads in slow seasons?","Yes. We can lower or pause spend anytime."),
       ("How fast do Google Ads bring calls?","Ads can show the same day the campaign goes live. The first weeks are used to learn which keywords and hours bring booked jobs, then we cut waste and scale what works."),
       ("Which trades do you run Google Ads for?","HVAC, plumbing, roofing, electrical, garage door, landscaping, cleaning, pest control, painting and pressure washing companies.")],
      "Google Ads management for contractors")

def compare_page():
    body = hero("Compare","Done-for-you website vs a <em>DIY builder</em> vs an agency","Wix, Squarespace and GoDaddy builders are cheap until you count your hours. Agencies are thorough until you see the invoice. Here is how they stack up for a home service business.",crumbs=[("Home",""),("Compare","")]) + f'''
<section class="section"><div class="wrap">{compare_table()}</div></section>
<section class="section mist"><div class="wrap grid g3">
<div class="card"><h3>Choose DIY if</h3><p>You have spare evenings, enjoy design, and are fine handling SEO, updates and hosting yourself.</p></div>
<div class="card"><h3>Choose an agency if</h3><p>You need a large custom site with dozens of pages and have the budget and months to wait.</p></div>
<div class="card"><h3>Choose SitesThatBook if</h3><p>You want a professional site that brings in calls, live in 48 hours, with everything handled for {MONTHLY} a month.</p></div>
</div></section>{cta_band()}'''
    page("done-for-you-vs-website-builder","Done-for-You Website vs Wix or Squarespace | SitesThatBook",
         "Compare a done-for-you home service website with DIY builders like Wix and Squarespace and with a typical agency on cost, time, SEO and updates.",
         body, priority="0.6", schema=[crumbs_schema([("Home",""),("Compare","done-for-you-vs-website-builder")])])

def blog():
    cards = "".join(f'''<a class="card" href="{L("blog/"+p["slug"])}"><span class="num">{p["tag"]} . {p["read"]} min read</span><h3>{p["title"]}</h3><p>{p["desc"]}</p><span class="more">Read the article &rarr;</span></a>''' for p in POSTS)
    body = hero("Blog","Website and marketing advice for <em>home service pros</em>","Straight answers on websites, SEO and getting more booked jobs. No fluff.",crumbs=[("Home",""),("Blog","")],ctas=False) + f'''
<section class="section"><div class="wrap"><div class="grid g3">{cards}</div></div></section>{cta_band()}'''
    page("blog","Home Service Website and SEO Blog | SitesThatBook",
         "Practical advice for plumbers, HVAC companies, roofers and home service pros on websites, local SEO and getting more calls.",
         body, active="blog", priority="0.6", schema=[crumbs_schema([("Home",""),("Blog","blog")])])
    for p in POSTS:
        toc = "".join(f'<li><a href="#{a}">{h}</a></li>' for a,h in p["toc"])
        b = hero(p["tag"], p["h1"], p["desc"], crumbs=[("Home",""),("Blog","blog"),(p["tag"],"")], ctas=False,
                 extra=f'<p class="post-meta">By the SitesThatBook team . Updated {date.today().strftime("%B %Y")} . {p["read"]} min read</p>') + f'''
<section class="section"><div class="wrap"><article class="prose">
<div class="callout"><b>Short answer:</b> {p["answer"]}</div>
<nav class="toc" aria-label="In this article"><b>In this article</b><ol>{toc}</ol></nav>
{p["body"].replace("{GET}", L("get-started")).replace("{PRICING}", L("pricing")).replace("{PLUMB}", L("plumber-websites")).replace("{SEO}", L("local-seo-for-contractors")).replace("{HVAC}", L("hvac-websites"))}
</article></div></section>{cta_band()}'''
        art = {"@type":"BlogPosting","headline":p["title"],"description":p["desc"],"datePublished":TODAY,"dateModified":TODAY,
               "author":{"@type":"Organization","name":"SitesThatBook"},"publisher":{"@id":SITE+"/#org"},"mainEntityOfPage":SITE+"/blog/"+p["slug"]}
        page("blog/"+p["slug"], p["title"]+(" | SitesThatBook" if len(p["title"])<=48 else ""), p["desc"], b, active="blog", og_type="article", priority="0.6",
             schema=[art, faq_schema(p["faqs"]), crumbs_schema([("Home",""),("Blog","blog"),(p["title"],"blog/"+p["slug"])])])

def legal():
    priv = f'''<section class="section"><div class="wrap"><div class="prose">
<p>Last updated {date.today().strftime("%B %d, %Y")}.</p>
<p>This policy explains how SitesThatBook ("we", "us") collects and uses information when you visit sitesthatbook.com or use our services.</p>
<h2>Information we collect</h2><ul><li>Details you submit in our forms, such as your name, business name, phone, email, service area and notes.</li><li>Files you send us, such as logos and photos, to build your website.</li><li>Basic usage data, such as pages visited, device and browser type, collected through analytics tools.</li></ul>
<h2>How we use it</h2><ul><li>To build, host and maintain your website.</li><li>To contact you about your project by phone, text or email.</li><li>To improve our website and services.</li></ul>
<h2>Text messages</h2><p>If you give us your mobile number, we may text you about your project. Message and data rates may apply. Reply STOP to opt out at any time. We do not sell or share your mobile number with third parties for marketing.</p>
<h2>Sharing</h2><p>We do not sell your personal information. We share it only with service providers that help us run our business, such as hosting, form and CRM tools, and only as needed to deliver our services.</p>
<h2>Your choices</h2><p>You can ask us to access, correct or delete your information at any time by emailing {EMAIL}.</p>
<h2>Contact</h2><p>SitesThatBook, 30 N Gould St, Sheridan, WY 82801. {EMAIL}. {PHONE}.</p>
</div></div></section>'''
    page("privacy","Privacy Policy | SitesThatBook","How SitesThatBook collects, uses and protects your information.",
         hero("Legal","Privacy Policy","",crumbs=[("Home",""),("Privacy Policy","")],ctas=False)+priv, priority="0.2")
    terms = f'''<section class="section"><div class="wrap"><div class="prose">
<p>Last updated {date.today().strftime("%B %d, %Y")}.</p>
<h2>Services</h2><p>SitesThatBook builds, hosts and maintains websites for home service businesses under the plan you choose. Plan features are listed on our pricing page.</p>
<h2>Fees</h2><p>The Launch plan has a {SETUP} one-time setup fee and a {MONTHLY} monthly fee. Add-on plans are billed monthly. Advertising spend for Google Ads is paid directly to Google and is not included in our fees.</p>
<h2>Timeline</h2><p>We aim to launch your website 48 hours after we receive your completed onboarding form and any items we need from you. Delays in getting us required information may extend this.</p>
<h2>Guarantee</h2><p>If you do not love your website on the launch call and we cannot fix it during that call, we refund your setup fee.</p>
<h2>Cancellation</h2><p>There is no contract. You can cancel your monthly plan at any time. Your site stays live through the end of the paid month.</p>
<h2>Your domain and content</h2><p>You own your domain name and the content and photos you provide.</p>
<h2>Contact</h2><p>{EMAIL}. {PHONE}.</p>
</div></div></section>'''
    page("terms","Terms of Service | SitesThatBook","Terms for SitesThatBook website plans, fees, timelines and cancellation.",
         hero("Legal","Terms of Service","",crumbs=[("Home",""),("Terms of Service","")],ctas=False)+terms, priority="0.2")

def not_found():
    body = hero("404","This page <em>moved</em>","The page you are looking for does not exist. Try one of these instead.",ctas=False) + f'''
<section class="section"><div class="wrap">{trades_grid()}</div></section>'''
    page("404","Page Not Found | SitesThatBook","Page not found.", body, noindex=True)

def extras():
    if MODE != "deploy":
        return
    urls = "".join(f"<url><loc>{SITE}{'/' + p if p else '/'}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>" for p,pr in PAGES)
    open(os.path.join(OUT,"sitemap.xml"),"w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    ai_bots = ["GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","Claude-SearchBot","Claude-User","PerplexityBot","Perplexity-User","Google-Extended","Applebot-Extended","Bingbot","DuckAssistBot","Amazonbot","meta-externalagent","CCBot"]
    robots = "# SitesThatBook welcomes search engines and AI assistants.\n# Site summary for AI tools: " + SITE + "/llms.txt\n\n"
    robots += "User-agent: *\nAllow: /\nDisallow: /thanks\n\n"
    robots += "".join(f"User-agent: {b}\nAllow: /\nDisallow: /thanks\n\n" for b in ai_bots)
    robots += f"Sitemap: {SITE}/sitemap.xml\n"
    open(os.path.join(OUT,"robots.txt"),"w").write(robots)
    redirects = ["/detailing / 301","/hvac /hvac-websites 301","/roofing /roofing-websites 301","/cleaning /cleaning-business-websites 301",
                 "/landscaping /landscaping-websites 301","/work /our-work 301"]
    open(os.path.join(OUT,"_redirects"),"w").write("\n".join(redirects) + "\n")
    trades = "\n".join(f"- [{t['name']} websites]({SITE}/{t['slug']}): {t['meta']}" for t in TRADES)
    posts = "\n".join(f"- [{p['title']}]({SITE}/blog/{p['slug']}): {p['desc']}" for p in POSTS)
    open(os.path.join(OUT,"llms.txt"),"w").write(f"""# SitesThatBook

> SitesThatBook builds done-for-you websites for US home service businesses: HVAC, plumbing, roofing, electrical, garage door, landscaping, cleaning, pest control, painting and pressure washing. Websites go live 48 hours after the client fills an onboarding form. Pricing is $349 setup and $99 per month with hosting, SSL, 2 content updates, 2 SEO blog posts and a monthly traffic report included. No contracts. If the client does not love the site on the launch call and it cannot be fixed on the call, the setup fee is refunded.

Add-on plans: Get Found (+$149/month) adds Google Business Profile setup, 5 posts a month, automated review requests and local citations. Get Booked (+$499/month, ad spend separate) adds managed Google Ads, a CRM with instant lead follow up and missed call text back.

Live client sites: ORO Landscaping (Colorado landscape design and build, google.orolandscape.com), Great Northern Refrigeration (Portland HVAC and refrigeration, gnrpdx.com), A & I Contracting (Denver home remodeling, google.aandicontracting.com).

Built by the team behind Leads Magnets, a Google Partner performance marketing agency. Founder: Mostafa Dabour.

Contact: {PHONE}, {EMAIL}, 30 N Gould St, Sheridan, WY 82801.

## Key pages
- [Home]({SITE}/)
- [Pricing]({SITE}/pricing)
- [How it works]({SITE}/how-it-works)
- [Our work]({SITE}/our-work)
- [FAQ]({SITE}/faq)
- [Get started]({SITE}/get-started)

## Websites by trade
{trades}

## Services
- [Home service website design]({SITE}/home-service-website-design)
- [Local SEO for contractors]({SITE}/local-seo-for-contractors)
- [Google Ads for contractors]({SITE}/google-ads-for-contractors)

## Articles
{posts}
""")
    vercel = {"cleanUrls": True, "trailingSlash": False,
      "redirects": [{"source": a, "destination": b, "permanent": True} for a,b in [("/detailing","/"),("/hvac","/hvac-websites"),("/roofing","/roofing-websites"),("/cleaning","/cleaning-business-websites"),("/landscaping","/landscaping-websites"),("/work","/our-work")]],
      "headers": [{"source": "/(.*)", "headers": [{"key":"X-Content-Type-Options","value":"nosniff"},{"key":"Referrer-Policy","value":"strict-origin-when-cross-origin"}]},
                  {"source": "/assets/(.*)", "headers": [{"key":"Cache-Control","value":"public, max-age=2592000"}]}]}
    open(os.path.join(OUT,"vercel.json"),"w").write(json.dumps(vercel, indent=2))
    open(os.path.join(OUT,"netlify.toml"),"w").write('[build]\n  publish = "."\n\n[[headers]]\n  for = "/*"\n  [headers.values]\n    X-Content-Type-Options = "nosniff"\n    Referrer-Policy = "strict-origin-when-cross-origin"\n\n[[headers]]\n  for = "/styles.css"\n  [headers.values]\n    Cache-Control = "public, max-age=604800"\n')

if __name__ == "__main__":
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy("styles.css", os.path.join(OUT,"styles.css"))
    shutil.copytree("assets", os.path.join(OUT,"assets"))
    shutil.copy("assets/favicon.ico", os.path.join(OUT,"favicon.ico"))
    home(); industries(); pricing(); how_it_works(); our_work(); about(); faq_page(); get_started(); contact(); thanks()
    for t in TRADES: trade_page(t)
    services(); compare_page(); blog(); legal(); not_found(); extras()
    print(f"{MODE}: {len(PAGES)} indexable pages -> {OUT}/")
