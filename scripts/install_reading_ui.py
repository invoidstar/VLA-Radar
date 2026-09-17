"""Idempotent upgrade of the existing lightweight reading UI; no framework migration."""
from pathlib import Path

HELPERS = r'''
  // Source-scoped deep-note rendering. All imported text is escaped, never executed.
  function metricValue(v,unit){return v==null?'—':esc(v)+(unit==='percent'?'%':unit==='seconds'?' s':'');}
  function benchmarkFamilies(data){return [...new Set(data.tracks.map(t=>t.dataset))];}
  function scopeNotice(note){
    const c=note.coverage;if(!c)return '';
    const labels={'primary-methods-experiments':'已阅读原文方法与实验指定范围','primary-theory':'理论原文与证明范围解读；不产生实验排名','official-technical-report':'官方技术报告解读；公开细节范围见下文','official-abstract-only':'仅依据官方摘要：全文方法、实验细节仍待核验'};
    return `<p class="note-coverage ${c.scope==='official-abstract-only'?'limited':''}">${esc(labels[c.scope]||c.scope)} · ${note.sections.length} 个解释章节。所有数值为指定来源报告，不代表本站独立复现。</p>`;
  }
  function richEvidence(note){
    const source=note.coverage?.source||note.sections[0]?.sources[0]?.url;
    const tables=(note.tables||[]).map((t,i)=>`<section class="note-table-block"><h3>结果与推理对照 ${i+1} · ${esc(t.title)}</h3><div class="note-table-scroll" tabindex="0" role="region" aria-label="${esc(t.title)}"><table class="note-table"><thead><tr>${t.columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${t.rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="note-small">${esc(t.caption)}</p>${links([{label:t.locator+' · 原文依据',url:source}])}</section>`).join('');
    const figures=(note.figures||[]).map(f=>`<figure class="note-figure"><h3>${esc(f.title)}</h3>${f.imageUrl?`<a href="${esc(external(f.url))}" target="_blank" rel="noopener noreferrer"><img src="${esc(external(f.imageUrl))}" alt="${esc(f.title)}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></a>`:''}<figcaption>${para(f.caption)}${f.license?`<p class="note-small">原作者图像 · ${esc(f.license)} · 未修改。图片不可达时仍可访问下方原文。</p>`:'<p class="note-small">提供原图定位和阅读说明，不复制未确认再分发许可的图像。</p>'}${links([{label:'查看论文原图 / 上下文',url:f.url}])}</figcaption></figure>`).join('');
    const br=note.benchmarkReview;const labels={pending:'待检查',extracted:'已有提取记录', 'not-applicable':'无适用标准榜单','protocol-unresolved':'协议或数据待核验'};
    const review=br?`<aside class="note-benchmark-review"><strong>评测提取：${esc(labels[br.status])}</strong><p>${esc(br.note)}</p><small>检查时间：${esc(br.checkedAt||'尚未完成')}</small></aside>`:'';
    return tables+figures+review;
  }
'''
CSS = '''
/* Deep reading: bounded tables, source figures and explicit evidence scope. */
.note-coverage{font-size:12px;line-height:1.9;color:#496786}.note-coverage.limited{color:#895d25;background:#fff5df;padding:10px;border-radius:6px}.note-table-block,.note-figure{margin:30px 0;padding:20px 0;border-top:1px solid #e4e8ef}.note-table-block h3,.note-figure h3{font-size:15px;line-height:1.8;color:#293750;margin:0 0 14px}.note-table-scroll{max-width:100%;overflow:auto;border:1px solid #e2e7ef;border-radius:9px}.note-table{width:100%;border-collapse:collapse;font-size:12px;min-width:460px}.note-table th{background:#f3f6fb;color:#485774;text-align:left;font-size:11px;padding:11px 13px}.note-table td{border-top:1px solid #e8ecf2;line-height:1.9;padding:11px 13px;vertical-align:top;color:#4e5f77}.note-figure img{display:block;max-width:100%;max-height:560px;object-fit:contain;height:auto;margin:auto;border:1px solid #e8edf2;background:white}.note-figure figcaption p{font-size:12px;line-height:1.95;color:#687287}.note-benchmark-review{padding:15px 17px;margin:24px 0;background:#f6f8fc;border:1px solid #e5e9f3;border-radius:10px;font-size:12px;color:#65758d;line-height:1.9}.note-benchmark-review strong{color:#445d7c}.note-benchmark-review small{color:#7f8da4}.dataset-tabs{flex-wrap:wrap;max-width:100%}.dataset-tabs button{font-size:11px;padding:8px 12px}.note-section>div{min-width:0}.note-section p{overflow-wrap:anywhere}.note-table-block .note-small{margin-top:12px}.note-figure{max-width:100%}.note-toc{display:grid;grid-template-columns:1fr 1fr}.note-toc button{line-height:1.8;padding:8px 10px}
@media(max-width:650px){.note-toc{grid-template-columns:1fr}.note-section p{font-size:13px}.dataset-tabs button{padding:7px 10px;font-size:10px}.note-table-block h3,.note-figure h3{font-size:14px}.note-table{min-width:430px}.note-figure{margin:20px 0}}
'''

def install(root):
    root=Path(root);p=root/'research.js';text=p.read_text(encoding='utf-8')
    if '// Source-scoped deep-note rendering.' in text:return
    def change(old,new):
        nonlocal text
        if old not in text:raise ValueError('UI layout changed; missing '+old[:80])
        text=text.replace(old,new)
    change('  async function enhance(p,root){',HELPERS+'\n  async function enhance(p,root){')
    change("${note.status==='expanded'?'已扩展 · 有原文定位':stale?'笔记已扩展 · 新版本待复核':'既有笔记 · 待深化核验'}", "${note.coverage?.scope==='official-abstract-only'?'摘要解读 · 全文待核验':stale?'深入笔记 · 新版本待复核':note.coverage?.level==='deep'?'深入笔记 · 分节原文依据':note.status==='expanded'?'已扩展 · 有原文定位':'既有笔记 · 待深化核验'}")
    change('<strong>阅读版本：${esc(note.version)}</strong>', '<strong>阅读版本：${esc(note.version)}</strong>${scopeNotice(note)}')
    change("</section>`).join('')}</div><div id=\"panel-life\"", "</section>`).join('')}${richEvidence(note)}</div><div id=\"panel-life\"")
    change("const rows=b.results.filter(x=>x.paperId===p.id&&x.evidence==='checked');", "const rows=b.tracks.flatMap(t=>visibleResults(b,t.id)).filter(x=>x.paperId===p.id);")
    change("${v==null?'—':esc(v)+'%'}", "${metricValue(v,b.tracks.find(t=>t.id===row.trackId)?.unit)}")
    change("let dataset=['LIBERO','RoboTwin','RoboCasa'].includes(query.get('dataset'))?query.get('dataset'):'LIBERO';", "const families=benchmarkFamilies(data);let dataset=families.includes(query.get('dataset'))?query.get('dataset'):(families.includes('LIBERO')?'LIBERO':families[0]);")
    change("${['LIBERO','RoboTwin','RoboCasa'].map(d=>", "${families.map(d=>")
    change('data-dataset="${d}"','data-dataset="${esc(d)}"')
    change('aria-pressed="${d===dataset}">${d}</button>','aria-pressed="${d===dataset}">${esc(d)}</button>')
    change('global.RadarResearch={enhance,renderBoards,pageWindow,rankRows,visibleResults};','global.RadarResearch={enhance,renderBoards,pageWindow,rankRows,visibleResults,metricValue,benchmarkFamilies,richEvidence};')
    p.write_text(text,encoding='utf-8')
    p=root/'research.css';p.write_text(p.read_text(encoding='utf-8')+CSS,encoding='utf-8')
    p=root/'scripts/test_research.cjs'
    p.write_text(p.read_text(encoding='utf-8')+'''\na.equal(R.metricValue(4.42,'score'),'4.42');\na.equal(R.metricValue(0,'percent'),'0%');\na.equal(R.metricValue(null,'seconds'),'—');\na.equal(R.metricValue(0.5,'seconds'),'0.5 s');\na.deepEqual(R.benchmarkFamilies({tracks:[{dataset:'CALVIN'},{dataset:'LIBERO'},{dataset:'CALVIN'}]}),['CALVIN','LIBERO']);\nconst html=R.richEvidence({sections:[{sources:[{url:'https://example.com/paper'}]}],tables:[{title:'<script>',columns:['a','b'],rows:[['<img onerror=x>','2']],locator:'Table 1',caption:'Test'}]});\na(!html.includes('<script>'));a(!html.includes('<img onerror'));a(html.includes('&lt;script&gt;'));\nconsole.log('PASS: deep-note escaping, dynamic benchmark families, score/seconds/percent units.');\n''',encoding='utf-8')
