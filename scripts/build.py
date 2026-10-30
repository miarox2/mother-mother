"""Dependency-free sitemap generation and clean static build. Run: python3 scripts/build.py."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import shutil
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.mothermother.org'
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__();self.canonical=None;self.noindex=False;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href')
  if tag=='meta' and a.get('name','').lower() in ('robots','googlebot') and 'noindex' in a.get('content','').lower():self.noindex=True

def build():
 pages=[f for f in ROOT.rglob('*.html') if not any(x in ('dist','.git','scripts') for x in f.relative_to(ROOT).parts)]
 ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
 tree=ET.Element('{'+ns+'}urlset');urls=[]
 for f in sorted(pages):
  page=Page(f.read_text())
  if page.noindex:continue
  rel=f.relative_to(ROOT).as_posix();path='/'+rel
  if path.endswith('index.html'):path=path[:-10]
  expected=BASE+path
  if page.canonical!=expected:raise ValueError(f'{rel}: expected canonical {expected}')
  urls.append(expected);ET.SubElement(ET.SubElement(tree,'{'+ns+'}url'),'{'+ns+'}loc').text=expected
 ET.indent(tree);ET.ElementTree(tree).write(ROOT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
 # Replace only the generated build directory; retain source and original photographs.
 dist=ROOT/'dist'
 if dist.exists():shutil.rmtree(dist)
 dist.mkdir()
 for f in pages+[ROOT/n for n in ('styles.css','robots.txt','sitemap.xml','CNAME','.nojekyll')]:
  out=dist/f.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out)
 # Include only assets used by public HTML/CSS, not original photos or review drafts.
 import re
 used=set()
 for f in pages+[ROOT/'styles.css']:
  used.update(re.findall(r'assets/([\w.-]+)',f.read_text()))
 (dist/'assets').mkdir()
 for name in sorted(used):shutil.copy2(ROOT/'assets'/name,dist/'assets'/name)
 print('Built dist with sitemap:',*urls,sep='\n')
if __name__=='__main__':build()
