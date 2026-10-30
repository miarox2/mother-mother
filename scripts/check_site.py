"""Static SEO, link, content preservation and contact configuration checks."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,xml.etree.ElementTree as ET
from build import ROOT,BASE
class Doc(HTMLParser):
 def __init__(self,text):
  super().__init__();self.tags=[];self.ids=[];self.headings=[];self.titles=[];self.json=[];self.mode=None;self.feed(text)
 def handle_starttag(self,t,attrs):
  a=dict(attrs);self.tags.append((t,a))
  if 'id' in a:self.ids.append(a['id'])
  if t in ('h1','h2','h3','h4'):self.headings.append(int(t[1]))
  if t=='title':self.mode='title'
  if t=='script' and a.get('type')=='application/ld+json':self.mode='json'
 def handle_endtag(self,t):
  if t in ('title','script'):self.mode=None
 def handle_data(self,d):
  if self.mode=='title':self.titles.append(d)
  if self.mode=='json':self.json.append(json.loads(d))
 def attr(self,tag,key,value,out):return [a.get(out) for t,a in self.tags if t==tag and a.get(key)==value]
def check():
 root=ROOT/'dist';docs={f:Doc(f.read_text()) for f in root.rglob('*.html')};titles=[];descs=[];canon=[]
 for f,d in docs.items():
  assert len(d.ids)==len(set(d.ids)),f'duplicate ids {f}'
  assert d.headings.count(1)==1,f'H1 {f}'
  assert all(b<=a+1 for a,b in zip(d.headings,d.headings[1:])),f'heading hierarchy {f}'
  assert ('html',{'lang':'en'}) in d.tags
  if f.name!='404.html':
   assert len(d.titles)==1; titles+=d.titles
   desc=d.attr('meta','name','description','content');assert len(desc)==1 and desc[0];descs+=desc
   cs=d.attr('link','rel','canonical','href');assert len(cs)==1;canon+=cs
   assert d.attr('meta','property','og:url','content')==cs
   for name in ['og:title','og:description','og:image','og:site_name']:assert len(d.attr('meta','property',name,'content'))==1
   assert d.attr('meta','name','twitter:card','content')==['summary_large_image']
   assert d.json and all(x['@context']=='https://schema.org' for x in d.json)
   assert not any('noindex' in a.get('content','') for t,a in d.tags if t=='meta')
  for t,a in d.tags:
   if t=='img':assert all(a.get(x) for x in ['alt','width','height']),f'image metadata {f}'
   url=a.get('href') if t=='a' else a.get('src') if t in ['img','script'] else a.get('href') if t=='link' and a.get('rel')=='stylesheet' else None
   if not url:continue
   u=urlsplit(url)
   if u.scheme or u.netloc:continue
   target=(root/unquote(u.path).lstrip('/')) if u.path.startswith('/') else (f.parent/unquote(u.path)) if u.path else f
   if target.is_dir():target=target/'index.html'
   assert target.is_file(),f'broken link {f}: {url}'
   if u.fragment:assert u.fragment in docs[target].ids,f'broken anchor {url}'
 assert len(set(titles))==len(titles) and len(set(descs))==len(descs)
 urls=[x.text for x in ET.parse(root/'sitemap.xml').findall('.//{*}loc')]
 assert set(urls)==set(canon) and len(urls)==4
 assert BASE+'/sitemap.xml' in (root/'robots.txt').read_text()
 home=docs[root/'index.html'];forms=[a for t,a in home.tags if t=='form']
 assert forms[0]['action']=='https://formsubmit.co/mia@mothermother.org' and forms[0]['method']=='POST'
 assert home.attr('input','name','_subject','value')==['MOTHERMOTHER.ORG INQUIRY']
 assert home.attr('select','name','service','id')==['service']
 assert len([a for t,a in home.tags if t=='figure' and a.get('class')=='testimonial'])==10
 assert docs[root/'404.html'].attr('meta','name','robots','content')==['noindex']
 print('PASS: four indexable pages, XML, metadata, JSON-LD syntax, headings, local assets/anchors, contact configuration, 10 original reviews and noindex 404.')
if __name__=='__main__':check()
