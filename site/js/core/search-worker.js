'use strict';
importScripts('dates.js','search-core.js');
let loaded,pathLoaded;
const saved=new Map();
self.onmessage=async e=>{
  const {id,path,query}=e.data;
  try{
    if(!/^data\/search-index\.[a-f0-9]{16}\.json$/.test(path))throw new Error('Invalid search index');
    if(pathLoaded!==path){pathLoaded=path;loaded=null;saved.clear();}
    if(!loaded)loaded=(async()=>{const c=new AbortController(),timer=setTimeout(()=>c.abort(),15000);try{const r=await fetch(path,{credentials:'omit',cache:'force-cache',signal:c.signal});if(!r.ok)throw new Error('Index HTTP '+r.status);return RadarSearchCore.buildIndex(await r.json());}finally{clearTimeout(timer);}})().catch(err=>{loaded=null;throw err;});
    let rows=saved.get(query);
    if(!rows){rows=RadarSearchCore.search(await loaded,query);saved.set(query,rows);if(saved.size>32)saved.delete(saved.keys().next().value);}
    self.postMessage({id,rows});
  }catch(error){self.postMessage({id,error:error.message});}
};
