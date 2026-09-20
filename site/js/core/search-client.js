/* Use a worker for large libraries, with an equivalent cooperative local fallback. */
'use strict';
(function(g){
  function create(path,fixture=null){
    let indexPromise,worker,workerReady=false,workerAttempted=false,sequence=0;const pending=new Map(),cache=new g.RadarRuntime.LRU(32);
    function source(){if(!indexPromise)indexPromise=(fixture?Promise.resolve(fixture):g.RadarRuntime.loadJson(path)).then(d=>g.RadarSearchCore.buildIndex(d)).catch(e=>{indexPromise=null;throw e;});return indexPromise;}
    function failWorker(){workerReady=false;if(worker)worker.terminate();worker=null;for(const item of pending.values()){clearTimeout(item.timer);item.reject(new Error('Worker unavailable'));}pending.clear();}
    function startWorker(){
      if(workerAttempted)return;workerAttempted=true;
    if(path&&!fixture&&typeof Worker!=='undefined')try{
      worker=new Worker('js/core/search-worker.js?v=maintenance-20260918');workerReady=true;
      worker.onmessage=e=>{const item=pending.get(e.data.id);if(!item)return;pending.delete(e.data.id);clearTimeout(item.timer);e.data.error?item.reject(new Error(e.data.error)):item.resolve(e.data.rows);};
      worker.onerror=failWorker;
    }catch{workerReady=false;}
    }
    async function localSearch(q){
      const all=await source(),rows=[];
      for(let i=0;i<all.length;i+=256){rows.push(...g.RadarSearchCore.search(all.slice(i,i+256),q));if(i+256<all.length)await new Promise(r=>setTimeout(r,0));}
      return rows;
    }
    async function query(q){
      q=g.RadarSearchCore.norm(q);const old=cache.get(q);if(old)return old;
      let rows;startWorker();
      if(workerReady){try{rows=await new Promise((resolve,reject)=>{const id=++sequence;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Worker timeout'));},20000);pending.set(id,{resolve,reject,timer});worker.postMessage({id,path,query:q});});}
        catch{failWorker();rows=await localSearch(q);}}
      else rows=await localSearch(q);
      cache.set(q,rows);return rows;
    }
    return {query};
  }
  g.RadarSearchClient={create};
})(typeof window!=='undefined'?window:globalThis);
