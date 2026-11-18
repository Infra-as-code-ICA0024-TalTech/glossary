"""Export the editable concept glossary using the standalone glossary build dependencies."""
import html
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from formatting import EMPHASIS, ascii_text, inline, to_html

# eXtreme Automation (XA) design tokens, see https://ui.extremeautomation.io/
XA = {'rose': '#d27079', 'navy': '#3d496e', 'slate': '#535c73', 'canvas': '#f5f5f7', 'line': '#e9e9ef',
      'muted': '#8991a8', 'ink': '#212121', 'rose_soft': '#f7e6e8', 'slate_soft': '#eceef3', 'link': '#0879ad'}
FONTS = {'PTSans': 'ptsans/PT_Sans-Web-Regular.ttf', 'PTSans-Bold': 'ptsans/PT_Sans-Web-Bold.ttf',
         'PTSans-Italic': 'ptsans/PT_Sans-Web-Italic.ttf', 'PTSans-BoldItalic': 'ptsans/PT_Sans-Web-BoldItalic.ttf',
         'JetBrainsMono': 'jetbrainsmono/JetBrainsMono[wght].ttf'}
XA_PDF_FONTS = {'PTSans-Regular', 'PTSans-Bold', 'PTSans-Italic', 'PTSans-BoldItalic', 'JetBrainsMono-Regular'}
HEADING = re.compile(r'^## (Lecture (\d+): .+)$', re.M)


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', ascii_text(value).casefold()).strip('-')


def load_glossary(root):
    source = (root/'source/Glossary.md').read_text(encoding='utf-8')
    preamble, *parts = HEADING.split(source)
    title, intro = preamble.strip().split('\n', 1)
    assert title.startswith('# ') and intro.strip(), 'Glossary needs a title and introduction'
    sections, concepts = [], {}
    for number, (heading, lecture, body) in enumerate(zip(parts[::3], parts[1::3], parts[2::3]), 1):
        assert int(lecture) == number, f'Lecture headings must be numbered 1, 2, 3, ...: found {heading}'
        assert heading.split(':', 1)[1].strip(), f'Lecture heading needs a title: {heading}'
        entries = []
        assert not body.split('### ', 1)[0].strip(), 'Put definitions under term headings'
        for term, definition in re.findall(r'^### ([^\n]+)\n(.*?)(?=^### |\Z)', body, re.M | re.S):
            term, definition = term.strip(), definition.strip()
            assert term and definition, 'Empty glossary term or definition'
            assert term.casefold() not in concepts, f'Duplicate glossary term: {term}'
            assert slug(term) not in {slug(t) for t in concepts.values()}, f'Ambiguous term anchor: {term}'
            assert not re.search(r'^#{1,6} ', definition, re.M), 'Unexpected heading in definition'
            concepts[term.casefold()] = term
            entries.append((term, definition))
        assert entries, f'No terms under {heading}'
        sections.append((heading, sorted(entries, key=lambda entry: entry[0].casefold())))
    assert sections, 'Glossary needs at least one "## Lecture 1: ..." heading'
    for _, entries in sections:
        for term, definition in entries:
            for reference in EMPHASIS.findall(definition):
                assert reference.casefold() in concepts, f'Italic cross-reference in "{term}" is not a term: {reference}'
                assert reference.casefold() != term.casefold(), f'Term refers to itself: {term}'
    return title[2:], intro.strip(), sections


def lecture_range(sections):
    return f'Lectures 1-{len(sections)}' if len(sections) > 1 else 'Lecture 1'


def course_code(title):
    code, _, rest = title.partition(' ')
    return (code, rest) if re.fullmatch(r'[A-Z]{2,}\d+', code) and rest else ('', title)


def split_heading(heading):
    label, name = heading.split(':', 1)
    return label.strip(), name.strip()


def logo_svg(root):
    svg = (root/'assets/xa-logo.svg').read_text(encoding='utf-8').strip()
    svg = re.sub(r'^<\?xml[^>]*>\s*', '', svg)
    return re.sub(r'^<svg\b[^>]*?\s(viewBox="[^"]+")[^>]*>',
                  r'<svg class="xa-logo" \1 xmlns="http://www.w3.org/2000/svg" role="img" aria-label="eXtreme Automation">',
                  svg, count=1)


def linked_definition(definition, anchors):
    def link(match):
        target = anchors.get(html.unescape(match.group(1)).casefold())
        return f'<a class="xref" href="#{target}"><em>{match.group(1)}</em></a>' if target else match.group(0)
    return re.sub(r'<em>([^<]+)</em>', link, to_html(definition))


HTML_CSS = '''
:root{--xa-color-rose:#d27079;--xa-color-navy:#3d496e;--xa-color-slate:#535c73;--xa-color-white:#fff;
--xa-color-canvas:#f5f5f7;--xa-color-line:#e9e9ef;--xa-color-muted:#8991a8;--xa-color-ink:#212121;
--xa-color-rose-soft:#f7e6e8;--xa-color-slate-soft:#eceef3;--xa-color-link:#0879ad;
--xa-font-sans:"PT Sans",system-ui,sans-serif;--xa-font-mono:"JetBrains Mono",ui-monospace,monospace;
--xa-radius-md:9px;--xa-radius-lg:14px;--xa-shadow-sm:0 1px 2px rgba(33,33,33,.06),0 1px 1px rgba(33,33,33,.04);
--xa-ring:0 0 0 3px rgba(210,112,121,.28);color-scheme:light}
*,*:before,*:after{box-sizing:border-box}
html{scroll-padding-top:84px;-webkit-text-size-adjust:100%}
body{margin:0;font-family:var(--xa-font-sans);color:var(--xa-color-ink);background:var(--xa-color-canvas);line-height:1.55;font-size:16px;-webkit-font-smoothing:antialiased}
h1,h2{line-height:1.2;color:var(--xa-color-navy);font-weight:700;margin:0}
a{color:var(--xa-color-link);text-decoration:none}a:hover{text-decoration:underline}
a:focus-visible,input:focus-visible{outline:none;box-shadow:var(--xa-ring);border-radius:6px}
code{font-family:var(--xa-font-mono);font-size:.82em;background:var(--xa-color-line);padding:2px 6px;border-radius:5px;color:var(--xa-color-navy)}
.wrap{max-width:1240px;margin:0 auto;padding:0 28px}
.xa-header{position:sticky;top:0;z-index:100;background:#ffffffe0;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid var(--xa-color-line)}
.xa-header-row{display:flex;align-items:center;gap:22px;height:64px}
.xa-logo{height:26px;width:auto;display:block;flex-shrink:0}
.xa-header-title{color:var(--xa-color-navy);font-weight:700;font-size:.94rem;padding-left:22px;border-left:1px solid var(--xa-color-line);white-space:nowrap}
.xa-header-spacer{flex:1}
.ver-badge{font-family:var(--xa-font-mono);font-size:.78rem;color:var(--xa-color-muted);border:1px solid var(--xa-color-line);border-radius:999px;padding:4px 11px;white-space:nowrap}
.c-hero{padding:44px 0 28px}
.eyebrow{color:var(--xa-color-rose);font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:.78rem}
.c-hero h1{font-size:2.6rem;margin:8px 0 12px;letter-spacing:-.02em}
.c-hero h1 .hl{background:linear-gradient(transparent 60%,var(--xa-color-rose-soft) 60%);padding:0 3px}
.c-hero .intro{font-size:1.1rem;color:var(--xa-color-slate);max-width:780px}
.c-hero .intro p{margin:0 0 .6rem}
.search{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin-top:22px}
.search[hidden]{display:none}
.search label{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.xa-input{font-family:var(--xa-font-sans);font-size:1rem;color:var(--xa-color-ink);background:var(--xa-color-white);border:1px solid #cdd2dd;border-radius:var(--xa-radius-md);padding:10px 14px;width:min(420px,100%);transition:border-color .15s,box-shadow .15s}
.xa-input:hover{border-color:var(--xa-color-navy)}
.xa-input:focus{outline:none;border-color:var(--xa-color-rose);box-shadow:var(--xa-ring)}
.search-status{font-size:.88rem;color:var(--xa-color-muted)}
.layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:32px;align-items:start;padding-bottom:40px}
.toc{position:sticky;top:80px;max-height:calc(100vh - 96px);overflow-y:auto;padding:4px 0}
.toc .label{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--xa-color-muted);font-weight:700;padding:4px 10px 8px}
.toc a{display:grid;grid-template-columns:1fr auto;column-gap:8px;padding:7px 10px;border-radius:var(--xa-radius-md);color:var(--xa-color-slate);font-weight:700;font-size:.88rem;line-height:1.3;transition:background .12s,color .12s}
.toc a:hover{background:var(--xa-color-slate-soft);color:var(--xa-color-navy);text-decoration:none}
.toc a[aria-current=true]{background:var(--xa-color-slate-soft);color:var(--xa-color-rose)}
.toc a.empty{opacity:.4}
.toc .tm{grid-column:1;font-family:var(--xa-font-mono);font-weight:400;font-size:.7rem;color:var(--xa-color-muted)}
.toc .t{grid-column:1}
.toc .n{grid-column:2;grid-row:1/3;align-self:center;font-family:var(--xa-font-mono);font-weight:400;font-size:.72rem;color:var(--xa-color-muted)}
.lectures{display:flex;flex-direction:column;gap:22px;min-width:0}
.card{background:var(--xa-color-white);border:1px solid var(--xa-color-line);border-radius:var(--xa-radius-lg);box-shadow:var(--xa-shadow-sm)}
.lecture{overflow:hidden}
.lecture[hidden],.entry[hidden]{display:none}
.lecture-head{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:20px 22px 16px;border-bottom:2px solid var(--xa-color-rose-soft)}
.lecture-head h2{font-size:1.35rem;margin-top:4px}
.badge{display:inline-flex;align-items:center;font-size:.76rem;font-weight:700;padding:3px 9px;border-radius:999px;line-height:1.3;white-space:nowrap;background:var(--xa-color-slate-soft);color:var(--xa-color-slate)}
dl{margin:0}
.entry{padding:15px 22px 16px;border-top:1px solid var(--xa-color-line);transition:background .3s}
.entry:first-child{border-top:none}
.entry:target{background:var(--xa-color-rose-soft)}
dt{color:var(--xa-color-navy);font-weight:700;font-size:1.06rem;line-height:1.3}
dd{margin:5px 0 0;max-width:860px}
dd p{margin:0 0 .5rem}dd p:last-child{margin-bottom:0}
.xref{color:var(--xa-color-link)}
.no-results{padding:22px;color:var(--xa-color-slate)}
.no-results[hidden]{display:none}
footer{padding:12px 0 48px;color:var(--xa-color-muted);font-size:.85rem;text-align:center}
@media (max-width:960px){.layout{grid-template-columns:1fr;gap:16px}
.toc{top:64px;z-index:50;max-height:none;display:flex;gap:6px;overflow-x:auto;background:var(--xa-color-canvas);margin:0 -28px;padding:8px 28px;border-bottom:1px solid var(--xa-color-line);scrollbar-width:none}
.toc::-webkit-scrollbar{display:none}
.toc .label,.toc .t,.toc .n{display:none}
.toc a{display:block;flex-shrink:0;padding:6px 11px;border:1px solid var(--xa-color-line);background:var(--xa-color-white);border-radius:999px}
.toc .tm{font-weight:700;font-family:var(--xa-font-sans);font-size:.82rem;color:inherit}
html{scroll-padding-top:124px}}
@media (max-width:640px){.wrap{padding:0 16px}.toc{margin:0 -16px;padding:8px 16px}.xa-header-title{display:none}
.c-hero{padding:30px 0 20px}.c-hero h1{font-size:2rem}.c-hero .intro{font-size:1rem}
.lecture-head{padding:16px 16px 12px;align-items:flex-start;flex-direction:column;gap:6px}.entry{padding:13px 16px 14px}}
@media print{body{background:#fff;font-size:11pt}.xa-header,.toc,.search{display:none}.layout{display:block}
.card{box-shadow:none;border:none;border-radius:0}.lecture{break-before:page}.entry{break-inside:avoid;padding:8px 0}
.lecture-head{padding:0 0 8px}.c-hero{padding:0 0 12px}.xref{color:inherit}}
'''

HTML_SCRIPT = '''
(function(){
  var input=document.getElementById('term-search'),status=document.getElementById('search-status'),
      none=document.getElementById('no-results'),sections=[].slice.call(document.querySelectorAll('.lecture')),
      links={},total=document.querySelectorAll('.entry').length;
  [].forEach.call(document.querySelectorAll('.toc a'),function(a){links[a.hash.slice(1)]=a;});
  document.getElementById('search').hidden=false;
  function norm(s){return s.toLowerCase().replace(/\\s+/g,' ');}
  function filter(){
    var q=norm(input.value.trim()),shown=0;
    sections.forEach(function(sec){
      var n=0;
      [].forEach.call(sec.querySelectorAll('.entry'),function(e){
        var hit=!q||norm(e.textContent).indexOf(q)>=0;e.hidden=!hit;if(hit)n++;});
      sec.hidden=n===0;shown+=n;links[sec.id].classList.toggle('empty',n===0);
    });
    none.hidden=shown>0;
    status.textContent=q?shown+' of '+total+' terms match':total+' terms';
  }
  input.addEventListener('input',filter);
  input.addEventListener('keydown',function(e){if(e.key==='Escape'){input.value='';filter();}});
  var current=null,pending=false;
  function spy(){
    pending=false;
    var visible=sections.filter(function(s){return !s.hidden;}),active=visible[0];
    visible.forEach(function(s){if(s.getBoundingClientRect().top<=150)active=s;});
    if(!active||active===current)return;
    if(current)links[current.id].removeAttribute('aria-current');
    current=active;var a=links[active.id],nav=a.parentNode;a.setAttribute('aria-current','true');
    if(getComputedStyle(nav).display==='flex')nav.scrollLeft+=a.getBoundingClientRect().left-nav.getBoundingClientRect().left-16;
  }
  function queue(){if(!pending){pending=true;requestAnimationFrame(spy);}}
  window.addEventListener('scroll',queue,{passive:true});
  window.addEventListener('resize',queue);
  input.addEventListener('input',queue);
  spy();
})();
'''


def html_document(title, intro, sections, logo):
    count = sum(len(entries) for _, entries in sections)
    anchors = {term.casefold(): f'term-{slug(term)}' for _, entries in sections for term, _ in entries}
    code, rest = course_code(title)
    *lead, last = rest.split(' ')
    eyebrow = ' · '.join(filter(None, [code, lecture_range(sections)]))
    heading = ' '.join(html.escape(w) for w in lead) + f' <span class="hl">{html.escape(last)}</span>'
    toc = ['<nav class="toc" aria-label="Lectures"><div class="label">Lectures</div>']
    body = []
    for i, (lecture, entries) in enumerate(sections, 1):
        label, name = split_heading(lecture)
        toc.append(f'<a href="#lecture-{i}"><span class="tm">{html.escape(label)}</span>'
                   f'<span class="t">{html.escape(name)}</span><span class="n">{len(entries)}</span></a>')
        body.append(f'<section class="card lecture" id="lecture-{i}" aria-labelledby="lecture-{i}-title">'
                    f'<div class="lecture-head"><div><div class="eyebrow">{html.escape(label)}</div>'
                    f'<h2 id="lecture-{i}-title">{html.escape(name)}</h2></div>'
                    f'<span class="badge">{len(entries)} terms</span></div><dl>')
        for term, definition in entries:
            body.append(f'<div class="entry" id="{anchors[term.casefold()]}"><dt>{html.escape(term)}</dt>'
                        f'<dd>{linked_definition(definition, anchors)}</dd></div>')
        body.append('</dl></section>')
    toc.append('</nav>')
    body.append('<div class="card no-results" id="no-results" hidden>No terms match this search.</div>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=PT+Sans:ital,wght@0,400;0,700;1,400&amp;family=JetBrains+Mono:wght@400;600&amp;display=swap">
<style>{HTML_CSS}</style></head><body>
<header class="xa-header"><div class="wrap xa-header-row">{logo}<span class="xa-header-title">{html.escape(title)}</span>
<div class="xa-header-spacer"></div><span class="ver-badge">{count} terms</span></div></header>
<div class="wrap"><section class="c-hero"><div class="eyebrow">{html.escape(eyebrow)}</div>
<h1>{heading}</h1><div class="intro">{to_html(intro)}</div>
<div class="search" id="search" role="search" hidden><label for="term-search">Search terms</label>
<input class="xa-input" id="term-search" type="search" placeholder="Search terms and definitions" autocomplete="off">
<span class="search-status" id="search-status" aria-live="polite">{count} terms</span></div></section>
<div class="layout">{''.join(toc)}<main class="lectures">{''.join(body)}</main></div></div>
<footer class="wrap">{html.escape(title)} · {lecture_range(sections)} · {count} terms</footer>
<script>{HTML_SCRIPT}</script></body></html>
'''


def moodle_document(title, intro, sections):
    root = ET.Element('GLOSSARY')
    info = ET.SubElement(root, 'INFO')
    settings = {'NAME': title, 'INTRO': to_html(intro), 'INTROFORMAT': 1,
                'ALLOWDUPLICATEDENTRIES': 0, 'DISPLAYFORMAT': 'dictionary',
                'SHOWSPECIAL': 1, 'SHOWALPHABET': 1, 'SHOWALL': 1,
                'ALLOWCOMMENTS': 0, 'USEDYNALINK': 0, 'DEFAULTAPPROVAL': 1,
                'GLOBALGLOSSARY': 0, 'ENTBYPAGE': 20}
    for tag, value in settings.items():
        ET.SubElement(info, tag).text = str(value)
    nodes = ET.SubElement(info, 'ENTRIES')
    for heading, entries in sections:
        for term, definition in entries:
            entry = ET.SubElement(nodes, 'ENTRY')
            fields = {'CONCEPT': term, 'DEFINITION': to_html(definition), 'FORMAT': 1,
                      'DEFINITIONTRUST': 0, 'USEDYNALINK': 0, 'CASESENSITIVE': 0,
                      'FULLMATCH': 1, 'TEACHERENTRY': 1}
            for tag, value in fields.items():
                ET.SubElement(entry, tag).text = str(value)
            category = ET.SubElement(ET.SubElement(entry, 'CATEGORIES'), 'CATEGORY')
            ET.SubElement(category, 'NAME').text = heading
            ET.SubElement(category, 'USEDYNALINK').text = '0'
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def register_fonts(root):
    registered = pdfmetrics.getRegisteredFontNames()
    for name, path in FONTS.items():
        if name not in registered:
            pdfmetrics.registerFont(TTFont(name, str(root/'assets/fonts'/path)))
    pdfmetrics.registerFontFamily('PTSans', normal='PTSans', bold='PTSans-Bold',
                                  italic='PTSans-Italic', boldItalic='PTSans-BoldItalic')


def pdf_document(root, path, title, intro, sections):
    register_fonts(root)
    c = {name: colors.HexColor(value) for name, value in XA.items()}
    text = lambda value: inline(value, mono='JetBrainsMono')
    styles = {
        'eyebrow': ParagraphStyle('eyebrow', fontName='PTSans-Bold', fontSize=8.5, leading=11, textColor=c['rose'], spaceAfter=3),
        'title': ParagraphStyle('title', fontName='PTSans-Bold', fontSize=26, leading=31, textColor=c['navy'], spaceAfter=12),
        'intro': ParagraphStyle('intro', fontName='PTSans', fontSize=11.5, leading=16.5, textColor=c['slate'], spaceAfter=18),
        'label': ParagraphStyle('label', fontName='PTSans-Bold', fontSize=8, leading=10, textColor=c['muted'], spaceAfter=6),
        'toc_num': ParagraphStyle('toc_num', fontName='JetBrainsMono', fontSize=8.5, leading=12, textColor=c['rose']),
        'toc_name': ParagraphStyle('toc_name', fontName='PTSans-Bold', fontSize=10.5, leading=13, textColor=c['navy']),
        'toc_count': ParagraphStyle('toc_count', fontName='JetBrainsMono', fontSize=8.5, leading=12, textColor=c['muted'], alignment=2),
        'lecture': ParagraphStyle('lecture', fontName='PTSans-Bold', fontSize=8.5, leading=11, textColor=c['rose'],
                                  spaceBefore=26, spaceAfter=3, keepWithNext=True),
        'heading': ParagraphStyle('heading', fontName='PTSans-Bold', fontSize=18, leading=22, textColor=c['navy'],
                                  spaceAfter=7, keepWithNext=True),
        'term': ParagraphStyle('term', fontName='PTSans-Bold', fontSize=11.5, leading=15, textColor=c['navy'], spaceBefore=9, spaceAfter=2),
        'body': ParagraphStyle('body', fontName='PTSans', fontSize=10.3, leading=14.4, textColor=c['ink'], spaceAfter=6),
    }
    count = sum(len(entries) for _, entries in sections)
    rows = []
    for heading, entries in sections:
        label, name = split_heading(heading)
        rows.append([Paragraph(text(label.upper()), styles['toc_num']), Paragraph(text(name), styles['toc_name']),
                     Paragraph(f'{len(entries)} terms', styles['toc_count'])])
    width = A4[0] - 80
    contents = Table(rows, colWidths=[76, width - 76 - 60, 60])
    contents.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'PTSans'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                  ('LINEBELOW', (0, 0), (-1, -1), 0.6, c['line']),
                                  ('LINEABOVE', (0, 0), (-1, 0), 0.6, c['line']), ('TOPPADDING', (0, 0), (-1, -1), 6),
                                  ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    code, rest = course_code(title)
    eyebrow = ' · '.join(filter(None, [code, lecture_range(sections)])).upper()
    story = [Spacer(1, 24), Paragraph(text(eyebrow), styles['eyebrow']), Paragraph(text(rest), styles['title']),
             HRFlowable(width=56, thickness=3, color=c['rose'], hAlign='LEFT', spaceBefore=2, spaceAfter=16),
             Paragraph(text(intro), styles['intro']),
             Paragraph(f'CONTENTS · {count} TERMS', styles['label']), contents]
    for i, (heading, entries) in enumerate(sections):
        label, name = split_heading(heading)
        story += [PageBreak() if i == 0 else CondPageBreak(A4[1] * 0.28),
                  Paragraph(text(label.upper()), styles['lecture']), Paragraph(text(name), styles['heading']),
                  HRFlowable(width='100%', thickness=1.2, color=c['rose'], spaceBefore=0, spaceAfter=6)]
        for term, definition in entries:
            paragraphs = [Paragraph(text(term), styles['term'])]
            paragraphs += [Paragraph(text(p).replace('\n', '<br/>'), styles['body'])
                           for p in re.split(r'\n\s*\n', definition)]
            story.append(KeepTogether(paragraphs))

    footer_text = ascii_text(f'{title} · {lecture_range(sections)}')

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(c['line'])
        canvas.setLineWidth(0.6)
        canvas.line(40, 36, A4[0]-40, 36)
        canvas.setStrokeColor(c['rose'])
        canvas.setLineWidth(1.6)
        canvas.line(40, 36, 64, 36)
        canvas.setFont('PTSans', 8)
        canvas.setFillColor(c['muted'])
        canvas.drawString(40, 24, footer_text)
        canvas.setFont('JetBrainsMono', 8)
        canvas.drawRightString(A4[0]-40, 24, f'{doc.page:02d}')
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=40, rightMargin=40,
                      topMargin=40, bottomMargin=50, title=title, author='ICA0024',
                      initialFontName='PTSans', invariant=1).build(story, onFirstPage=footer, onLaterPages=footer)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def normalized_text(value):
    parser = PlainText()
    parser.feed(to_html(value))
    return ' '.join(ascii_text(''.join(parser.parts)).split())


def build_glossary(root, check=False):
    title, intro, sections = load_glossary(root)
    output = root/'exports'
    expected_html = html_document(title, intro, sections, logo_svg(root))
    expected_xml = moodle_document(title, intro, sections)
    if not check:
        output.mkdir(exist_ok=True)
        (output/'glossary.html').write_text(expected_html, encoding='utf-8')
        (output/'moodle-glossary.xml').write_bytes(expected_xml)
        pdf_document(root, output/'glossary.pdf', title, intro, sections)
    assert (output/'glossary.html').read_text(encoding='utf-8') == expected_html, 'Stale glossary HTML'
    assert (output/'moodle-glossary.xml').read_bytes() == expected_xml, 'Stale glossary XML'
    entries = [(heading, term, definition) for heading, group in sections for term, definition in group]
    nodes = ET.parse(output/'moodle-glossary.xml').findall('./INFO/ENTRIES/ENTRY')
    assert len(nodes) == len(entries)
    for (heading, term, definition), node in zip(entries, nodes):
        assert node.findtext('CONCEPT') == term
        assert node.findtext('DEFINITION') == to_html(definition)
        assert node.findtext('CATEGORIES/CATEGORY/NAME') == heading
        assert node.findtext('FORMAT') == '1'
    categories = [node.findtext('CATEGORIES/CATEGORY/NAME') for node in nodes]
    assert list(dict.fromkeys(categories)) == [heading for heading, _ in sections], 'Moodle categories differ from lectures'
    reader = PdfReader(output/'glossary.pdf')
    assert len(reader.pages) >= 2, 'PDF needs a contents page followed by the lecture pages'
    text = ' '.join(' '.join(page.extract_text().split()) for page in reader.pages)
    for heading, _ in sections:
        assert normalized_text(split_heading(heading)[1]) in text, f'Missing PDF lecture heading: {heading}'
    for _, term, definition in entries:
        assert normalized_text(term) in text, f'Missing PDF term: {term}'
        assert normalized_text(definition) in text, f'Stale or missing PDF definition: {term}'
    fonts = set()
    for page in reader.pages:
        for font in (page.get('/Resources', {}).get('/Font') or {}).values():
            fonts.add(str(font.get_object().get('/BaseFont', '')).split('+')[-1])
    assert fonts and fonts <= XA_PDF_FONTS, f'PDF uses fonts outside the XA set: {sorted(fonts - XA_PDF_FONTS)}'
    assert {'PTSans-Regular', 'PTSans-Bold'} <= fonts, f'PDF does not use PT Sans: {sorted(fonts)}'
    return {'terms': len(entries), 'lectures': len(sections), 'pdf_pages': len(reader.pages),
            'terms_per_lecture': {split_heading(heading)[0]: len(group) for heading, group in sections},
            'moodle_live_import_tested': False}
