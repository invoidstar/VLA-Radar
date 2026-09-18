"""Validate editorial structure, not scientific truth. Network-free and public-only."""
from __future__ import annotations
import re
from datetime import date

EXTRA_KEYS = {'coverage', 'figures', 'tables', 'benchmarkReview'}
SCOPES = {'primary-methods-experiments', 'primary-theory', 'official-technical-report', 'official-abstract-only', 'author-materials-partial'}

def validate_note_extras(note, public_url, require):
    cov = note.get('coverage')
    if cov is not None:
        require(set(cov) == {'level', 'scope', 'source'}, 'note coverage fields')
        require(cov['level'] in {'deep','limited'} and cov['scope'] in SCOPES, 'note coverage level/scope')
        require((cov['level']=='limited') == (cov['scope'] in {'official-abstract-only','author-materials-partial'}), 'abstract-only cannot be promoted to full-source notes')
        public_url(cov['source'])
        require(len(note['sections']) >= (8 if cov['level']=='deep' else 3), 'source-scoped section count')
        require(sum(len(s['body']) for s in note['sections']) >= (1200 if cov['level']=='deep' else 300), 'source-scoped note is too short')
        require(all(len(s['body']) >= (90 if cov['level']=='deep' else 40) and s['sources'] for s in note['sections']), 'deep sections need explanatory content and sources')
        require(note['verifiedAt'] and note['version'], 'deep notes need a checked date and read version')
    figures = note.get('figures', [])
    require(isinstance(figures, list) and len(figures) <= 8, 'note figure count')
    for f in figures:
        required = {'title','url','caption'}
        require(isinstance(f,dict) and required <= set(f) <= required | {'imageUrl','license'}, 'figure fields')
        require(all(isinstance(f[k],str) and f[k] for k in required), 'figure text')
        public_url(f['url'])
        if 'imageUrl' in f:
            public_url(f['imageUrl'])
            require(f.get('license') in {'CC BY 4.0','CC BY 3.0','CC0'}, 'inline figures need a confirmed redistribution license')
            require(len(f['caption']) >= 25, 'figure needs attribution and an explanatory caption')
        else:
            require('license' not in f, 'a figure link does not assert an image license')
    tables = note.get('tables', [])
    require(isinstance(tables,list) and len(tables) <= 8, 'note table count')
    for t in tables:
        require(isinstance(t,dict) and set(t)=={'title','columns','rows','locator','caption'}, 'table fields')
        require(all(isinstance(t[k],str) and t[k] for k in ('title','locator','caption')), 'table attribution and explanation')
        require(isinstance(t['columns'],list) and 2 <= len(t['columns']) <= 12 and all(isinstance(x,str) and x for x in t['columns']), 'table columns')
        require(isinstance(t['rows'],list) and 1 <= len(t['rows']) <= 30, 'table rows')
        require(all(isinstance(row,list) and len(row)==len(t['columns']) and all(isinstance(v,str) for v in row) for row in t['rows']), 'table must be rectangular text, no guessed zeros')
    review = note.get('benchmarkReview')
    if review is not None:
        require(isinstance(review,dict) and set(review)=={'status','checkedAt','note'}, 'benchmark review fields')
        require(review['status'] in {'pending','extracted','not-applicable','protocol-unresolved'}, 'benchmark review status')
        require(isinstance(review['note'],str) and review['note'], 'benchmark review explanation')
        if review['checkedAt'] is not None: date.fromisoformat(review['checkedAt'])
        if review['status'] != 'pending': require(review['checkedAt'] is not None, 'completed benchmark review needs date')


def install(root):
    """One-time, idempotent compatibility upgrade; keeps legacy fixtures valid."""
    from pathlib import Path
    root=Path(root)
    p=root/'scripts/catalog_core.py';text=p.read_text(encoding='utf-8')
    if '# source-scoped deep-note extensions' not in text:
        text=text.replace("note=rec['note']; keys(note,NOTE_KEYS,'note');", "note=rec['note']; keys(note,NOTE_KEYS | (set(note) & {'coverage','figures','tables','benchmarkReview'}),'note');")
        needle="\ndef validate_track(t):"
        require_text="\n    # source-scoped deep-note extensions\n    from note_quality import validate_note_extras\n    validate_note_extras(note, public_url, require)\n"
        if needle not in text: raise ValueError('catalog validator layout changed; reconcile explicitly')
        text=text.replace(needle,require_text+needle)
        text=text.replace("require(t['dataset'] in {'LIBERO','RoboTwin','RoboCasa'},'supported dataset family')", "require(isinstance(t['dataset'],str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._+()-]{0,59}',t['dataset']),'public benchmark family name')")
        p.write_text(text,encoding='utf-8')
