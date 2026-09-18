/* Optional workspace: no feature data is requested at startup. */
'use strict';
(function(g){
 let config,api,pending;
 function script(path){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=path;s.onload=resolve;s.onerror=()=>{s.remove();reject(new Error('功能模块加载失败，请重试'));};document.head.append(s);});}
 function ensure(){if(!pending)pending=(g.RadarExperienceCore?Promise.resolve():script('experience-core.js?v=workspace-20260918')).then(()=>g.RadarExperience?null:script('experience.js?v=workspace-20260918')).then(()=>{g.RadarExperience.configure(config,api);return g.RadarExperience;}).catch(e=>{pending=null;throw e;});return pending;}
 let generation=0;
 function leave(){generation++;g.RadarExperience?.leave();}
 async function show(view){leave();const token=generation,host=document.getElementById(view+'-content');host.innerHTML='<p class="workspace-loading" role="status">正在打开研究工作台…</p>';try{const x=await ensure();if(token===generation)await x.render(view,host);}catch(e){if(token!==generation)return;host.innerHTML='<p role="alert">功能暂未载入。</p><button class="btn" data-view="'+view+'">重试</button>';}}
 async function action(type,id){try{const x=await ensure();await x.action(type,id);}catch(e){api?.notify('功能暂不可用，请重试。');console.warn(e.message);}}
 function configure(c,a){config=c;api=a;const key='vla-radar.visit.v1';try{api.previousVisit=JSON.parse(localStorage.getItem(key)||'null');if(typeof api.previousVisit!=='string'||!Number.isFinite(Date.parse(api.previousVisit)))api.previousVisit=null;localStorage.setItem(key,JSON.stringify(new Date().toISOString()));}catch{api.previousVisit=null;}}
 g.RadarWorkspace={configure,show,leave,action};
})(window);
