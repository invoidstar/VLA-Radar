"""Extract candidate benchmark rows from a specified HTML table; never auto-rank.
The caller must identify the reporting paper, version, table and protocol. PDFs and
unresolved merged table headers remain manual review, not guessed percentages.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from html.parser import HTMLParser
from pathlib import Path
from catalog_core import load, public_url, today, write
from http_public import fetch
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.depth=0;self.table=None;self.row=None;self.cell=None;self.capture=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table':
            self.depth+=1
            if self.depth==1:self.table={'id':a.get('id',''),'rows':[],'merged':False}
        if self.depth==1:
            if tag=='tr':self.row=[]
            if tag in {'td','th'}:
                self.cell=[];self.capture=True
                if a.get('rowspan','1')!='1' or a.get('colspan','1')!='1':self.table['merged']=True
            if tag=='br' and self.capture:self.cell.append(' ')
    def handle_data(self,text):
        if self.capture and self.cell is not None:self.cell.append(text)
    def handle_endtag(self,tag):
        if self.depth==1:
            if tag in {'td','th'} and self.cell is not None:
                if self.row is not None:self.row.append(' '.join(''.join(self.cell).split()))
                self.cell=None;self.capture=False
            if tag=='tr' and self.row is not None:
                if self.row:self.table['rows'].append(self.row)
                self.row=None
            if tag=='table':self.tables.append(self.table);self.table=None
        if tag=='table':self.depth=max(0,self.depth-1)
def number(text):
    text=text.strip().replace('−','-')
    if text in {'','–','—','-','N/A','n/a'}:return None
    # Ignore math accessibility duplicates only when a caller resolves them explicitly.
    m=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)(?:\s*%|\s*±\s*\d+(?:\.\d+)?)?',text)
    if not m:raise ValueError('ambiguous numeric cell: '+text)
    return float(m[1])
def extract(html, paper_id, source, version, table_index, track, columns):
    public_url(source); parser=Tables();parser.feed(html)
    if not 0<=table_index<len(parser.tables):raise ValueError('table index not found')
    table=parser.tables[table_index];out=[];rejected=[]
    for row in table['rows']:
        if not row or len(row)<=max(columns.values()):continue
        if row[0].lower() in {'method','model','policy',''}:continue
        try:values={k:number(row[pos]) for k,pos in columns.items()}
        except ValueError:rejected.append(row);continue
        if all(v is None for v in values.values()):continue
        if any(v is not None and not 0<=v<=100 for v in values.values()):rejected.append(row);continue
        identity='|'.join([paper_id,row[0],track,version,str(table_index)])
        out.append({'id':'r-'+hashlib.sha256(identity.encode()).hexdigest()[:20],'paperId':paper_id,'method':row[0],'trackId':track,
            'values':values,'evidence':'candidate','verifiedAt':None,'source':source,'sourceVersion':version,
            'locator':f'HTML table {table_index+1}'+(' #'+table['id'] if table['id'] else ''),
            'attribution':'reported-baseline','trainingData':'待核验','evaluationNotes':'候选自动抽取；逐项核对数值、方法身份、输入与协议后才可入榜。','supersedes':'',
        })
    return {'schemaVersion':1,'extractedAt':today(),'source':source,'tableIndex':table_index,'mergedCells':table['merged'],'candidates':out,'rejectedRows':rejected,
        'reviewRequired':True,'note':'Exact table extraction is not publication or leaderboard verification; no candidate is auto-promoted.'}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source');ap.add_argument('--paper',required=True);ap.add_argument('--version',required=True);ap.add_argument('--table',type=int,required=True,help='zero-based HTML table index');ap.add_argument('--track',required=True);ap.add_argument('--columns',required=True,help='JSON: column label to zero-based cell index');ap.add_argument('--html',type=Path,help='already retrieved public HTML');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    text=a.html.read_text(encoding='utf-8') if a.html else fetch(a.source)[0]
    write(a.output,extract(text,a.paper,a.source,a.version,a.table,a.track,json.loads(a.columns)))
