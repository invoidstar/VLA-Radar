/* Small bounded public-JSON cache. Reading progress never leaves the browser. */
'use strict';
(function(g){
  class LRU {
    constructor(limit=32){this.limit=limit;this.map=new Map();}
    get(key){if(!this.map.has(key))return undefined;const v=this.map.get(key);this.map.delete(key);this.map.set(key,v);return v;}
    set(key,value){this.map.delete(key);this.map.set(key,value);while(this.map.size>this.limit)this.map.delete(this.map.keys().next().value);return value;}
    delete(key){this.map.delete(key);}
  }
  const cache=new LRU(40);
  function safePath(path){return typeof path==='string'&&/^data\/[a-zA-Z0-9_./?=\-]+$/.test(path)&&!path.includes('..');}
  function loadJson(path){
    if(!safePath(path))return Promise.reject(new Error('Invalid static JSON path'));
    const prior=cache.get(path);if(prior)return prior;
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
    const promise=fetch(path,{credentials:'omit',cache:/\.[a-f0-9]{16}\.json$/.test(path)?'force-cache':'no-cache',signal:controller.signal})
      .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
      .catch(e=>{if(cache.map.get(path)===promise)cache.delete(path);throw e;}).finally(()=>clearTimeout(timer));
    return cache.set(path,promise);
  }
  g.RadarRuntime={LRU,loadJson,safePath};
  if(typeof module!=='undefined')module.exports=g.RadarRuntime;
})(typeof window!=='undefined'?window:globalThis);
