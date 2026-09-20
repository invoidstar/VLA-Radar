/* Tiny optional-tool entrypoint; no feed, news or bibliography request on initial load. */
'use strict';
(function(g){
 let config,api,pending,observer;const KEY='vla-radar.follows.v1';
 function js(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>{s.remove();reject(Error('工具加载失败'));};document.head.append(s);});}
 function style(){if(document.getElementById('daily-tools-css'))return Promise.resolve();return new Promise((resolve,reject)=>{const s=document.createElement('link');s.id='daily-tools-css';s.rel='stylesheet';s.href='tools.css';s.onload=resolve;s.onerror=()=>{s.remove();reject(Error('样式加载失败'));};document.head.append(s);});}
 function ensure(){if(!pending)pending=Promise.all([style(),(g.RadarToolsCore?Promise.resolve():js('tools-core.js')).then(()=>g.RadarDaily?null:js('tools.js'))]).then(()=>{g.RadarDaily.configure(config,api);return g.RadarDaily;}).catch(e=>{pending=null;throw e;});return pending;}
 async function call(method,arg){try{return await (await ensure())[method](arg);}catch{api?.notify('工具暂未载入，请重试。');}}
 function following(id){const memory=g.RadarDaily?.isFollowing(id);if(memory!==null&&memory!==undefined)return memory;try{const f=JSON.parse(localStorage.getItem(KEY)||'{}');return Array.isArray(f.papers)&&f.papers.includes(id);}catch{return false;}}
 function refresh(){for(const b of document.querySelectorAll('[data-follow-paper]')){const on=following(b.dataset.followPaper),text=on?'✓ 已关注':'＋ 关注';if(b.textContent!==text)b.textContent=text;b.setAttribute('aria-pressed',String(on));}}
 function configure(c,a){config=c;api=a;if(observer)return;let frame=0;observer=new MutationObserver(()=>{if(!frame)frame=requestAnimationFrame(()=>{frame=0;refresh();});});for(const id of ['results','paper-detail','reader-content']){const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true});}refresh();
 document.addEventListener('click',e=>{const b=e.target.closest('[data-follow-paper],[data-command]');if(!b)return;e.preventDefault();if(b.hasAttribute('data-command'))call('command');else call('followPaper',b.dataset.followPaper);});
 document.addEventListener('keydown',e=>{if(e.defaultPrevented||e.isComposing)return;const editing=e.target.closest?.('input,textarea,select,[contenteditable="true"],[role="textbox"]');if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'||(!editing&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&e.key==='/')){const opened=document.querySelector('dialog[open]');if(opened){if(opened.id==='paper-dialog'&&(e.ctrlKey||e.metaKey))api.closePaper();else return;}e.preventDefault();call('command');}});
 window.addEventListener('storage',e=>{if(e.key===KEY||e.key===null){g.RadarDaily?.storageChanged();refresh();}});
 }
 async function show(host){host.innerHTML='<p role="status">正在打开 My Radar…</p>';try{const d=await ensure();if(new URLSearchParams(location.search).get('view')==='radar')await d.radar(host);}catch{if(new URLSearchParams(location.search).get('view')==='radar')host.innerHTML='<p role="alert">关注页暂未载入，请重试。</p><button class="btn" data-view="radar">重试</button>';}}
 g.RadarTools={configure,show,refresh,export:list=>call('exportDialog',list),command:()=>call('command')};
})(window);
