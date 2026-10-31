# -*- coding: utf-8 -*-
"""Same-origin generation client. Provider credentials exist only in the backend."""

JS = r"""<script>
(function(){
const API = new URL('api/generation/', new URL(document.querySelector('#rc').dataset.up, location.href)).href;
const PROV = {
 relay:{name:'自定义中转 · OpenAI 兼容',base:'',models:['gpt-image-2','gpt-image-2.5-sunburst','gpt-image-2.5-flare']},
 openai:{name:'OpenAI GPT Image',base:'https://api.openai.com/v1',models:['gpt-image-2','gpt-image-1.5']},
 gemini:{name:'Google Gemini · Nano Banana',base:'https://generativelanguage.googleapis.com/v1beta',models:['gemini-2.5-flash-image','gemini-3-pro-image-preview','gemini-3.1-flash-image']},
 seedream:{name:'豆包 Seedream · 火山方舟',base:'https://ark.cn-beijing.volces.com/api/v3',models:['doubao-seedream-4-0-250828','doubao-seedream-4-5-251128','doubao-seedream-5-0-flash-260915']},
 qwen:{name:'通义 Qwen-Image',base:'https://dashscope.aliyuncs.com/api/v1',models:['qwen-image-2.0-pro','qwen-image-2.0']}
};
const RATIOS = ['auto','3:4','2:3','1:1','4:3','9:16','16:9'];
let refreshing = null;
let session = null, profiles = [], available = false, active = false, pending = null, jobList = [];
const L = localStorage;
const read = (k,d) => {try{return JSON.parse(L.getItem(k)||'null')||d;}catch(_){return d;}};
const cfg = () => Object.assign({profile:'',p:'relay',ratio:'3:4',n:1,parameters:{}}, read('pl.gen',{}));
function setCfg(o){try{L.setItem('pl.gen',JSON.stringify(Object.assign(cfg(),o)));}catch(_){} fire();}
function fire(){dispatchEvent(new Event('pl:gen'));}
try{localStorage.removeItem('pl.genkey');sessionStorage.removeItem('pl.genkey');}catch(_){}
async function api(path, options){
 const o=Object.assign({credentials:'same-origin',cache:'no-store'},options||{});
 o.headers=Object.assign({},o.headers);
 if(o.method&&o.method!=='GET'){o.headers['x-csrf-token']=session&&session.csrf||'';if(o.body)o.headers['content-type']='application/json';}
 let r;try{r=await fetch(API+path,o);}catch(_){throw {k:'network',msg:'生图服务连接失败'};}
 let j;try{j=await r.json();}catch(_){throw {k:'unavailable',msg:'生图服务未启用，请使用带后端的在线版本'};}
 if(!r.ok)throw j.error||{k:'server',msg:'生图服务出错'};
 return j;
}
async function init(){
 if(location.protocol==='file:')return false;
 if(pending)return pending;
 pending=(async()=>{try{
   session=await api('session');available=true;
   if(read('pl.genSession','')!==session.session_id){await cacheClear();try{L.setItem('pl.genSession',JSON.stringify(session.session_id));}catch(_){} }
   await refreshProfiles(); await refresh(); return true;
 }catch(_){available=false;return false;}finally{pending=null;}})();return pending;
}
async function refreshProfiles(){const j=await api('profiles');profiles=j.profiles||[];
 const c=cfg();if(!profiles.some(p=>p.id===c.profile)){const p=profiles.find(p=>p.id===j.default_profile_id)||profiles[0];setCfg({profile:p?.id||'',p:p?.kind||c.p,selectedModel:p?.model||''});}
 return profiles;
}
const profile = id => profiles.find(p=>p.id===(id||cfg().profile));
const modelOf = (c,p) => {const pr=profile(c.profile);return pr&&pr.model||PROV[p]?.models[0]||'';};
async function saveProfile(id,value){
 const p=await api('profiles/'+encodeURIComponent(id),{method:'PUT',body:JSON.stringify(value)});
 await refreshProfiles();setCfg({profile:p.id,p:p.kind,selectedModel:p.model});return p;
}
async function deleteProfile(id){await api('profiles/'+encodeURIComponent(id),{method:'DELETE'});await refreshProfiles();fire();}
async function defaultProfile(id){await api('profiles/'+encodeURIComponent(id)+'/default',{method:'PUT'});}
async function forgetKey(id){return saveProfile(id,{remove_api_key:true});}
async function models(id){const p=await api('profiles/'+encodeURIComponent(id)+'/models/refresh',{method:'POST'});await refreshProfiles();fire();return p.models;}
async function erase(){await api('session',{method:'DELETE'});available=false;session=null;profiles=[];jobList=[];try{L.removeItem('pl.genSession');}catch(_){}await cacheClear();fire();}
function db(){return new Promise((ok,no)=>{const r=indexedDB.open('pl-gen',1);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains('jobs'))r.result.createObjectStore('jobs',{keyPath:'id'});};r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error);});}
async function tx(mode,fn){const d=await db();try{return await new Promise((ok,no)=>{const t=d.transaction('jobs',mode),r=fn(t.objectStore('jobs'));let v;if(r)r.onsuccess=()=>v=r.result;t.oncomplete=()=>ok(v);t.onerror=()=>no(t.error);});}finally{d.close();}}
const cacheClear=()=>tx('readwrite',s=>s.clear()).catch(()=>{});
async function cached(){const a=await tx('readonly',s=>s.getAll()).catch(()=>[]);return (a||[]).filter(j=>session&&j.owner===session.session_id).sort((a,b)=>b.at-a.at);}
async function cacheJob(j){
 if(!session)return;
 const owner=session.session_id;const old=await tx('readonly',s=>s.get(j.id)).catch(()=>null);if(old&&old.owner===owner&&old.out.length===(j.out||[]).length)return;
 const out=[];for(const x of j.out||[]){try{const r=await fetch(x.url,{credentials:'same-origin',cache:'no-store'});if(r.ok)out.push({blob:await r.blob(),mime:x.mime});}catch(_){}}
 if(!session||session.session_id!==owner||read('pl.genSession','')!==owner)return;
 if(out.length)await tx('readwrite',s=>s.put(Object.assign({},j,{out,owner})));
 const a=await cached();for(const x of a.slice(30))await tx('readwrite',s=>s.delete(x.id));
}
async function refresh(){
 if(refreshing)return refreshing;
 refreshing=refreshOnce().finally(()=>{refreshing=null;});return refreshing;
}
async function refreshOnce(){
 if(!available)return;
 if(read('pl.genSession','')!==session?.session_id){available=false;jobList=[];return;}
 const owner=session.session_id,j=await api('jobs'),remote=j.jobs||[];
 if(owner!==session?.session_id||read('pl.genSession','')!==owner)return;
 for(const x of remote)if(x.state==='done')await cacheJob(x).catch(()=>{});
 const local=await cached(),ids=new Set(remote.map(x=>x.id));
 if(owner!==session?.session_id||read('pl.genSession','')!==owner)return;
 jobList=[...remote.map(x=>{const hit=local.find(c=>c.id===x.id);return x.state==='done'&&hit?Object.assign({},x,{out:hit.out}):x;}),...local.filter(x=>!ids.has(x.id))].sort((a,b)=>b.at-a.at).slice(0,30);
 active=remote.some(x=>x.state==='queued'||x.state==='running');fire();
}
async function jobs(){return jobList;}
const loadImg=src=>new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=()=>no({k:'bad',msg:'参考图读取失败'});im.src=src;});
async function refImg(src){
 const im=await loadImg(src),s=Math.min(1,1024/Math.max(im.naturalWidth,im.naturalHeight));
 const c=document.createElement('canvas');c.width=Math.round(im.naturalWidth*s);c.height=Math.round(im.naturalHeight*s);
 const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.drawImage(im,0,0,c.width,c.height);
 return {mime:'image/jpeg',data:c.toDataURL('image/jpeg',.92).split(',')[1]};
}
async function run({items,prompt,up}){
 if(location.protocol==='file:')throw{k:'offline'};
 if(!available&&!await init())throw{k:'unavailable',msg:'生图服务未启用'};
 const c=cfg(),p=profile();if(!p||!p.api_key_present)throw{k:'nokey'};
 const images=await Promise.all(items.map(x=>refImg(up+(x.send||x.im||x.th))));
 const parameters=Object.assign({},c.parameters,{ratio:c.ratio,model:c.selectedModel||p.model});
 const j=await api('jobs',{method:'POST',body:JSON.stringify({request_id:crypto.randomUUID(),profile_id:p.id,prompt,images,n:+c.n||1,parameters})});
 active=true;await refresh();return j.id;
}
async function cancel(id){await api('jobs/'+id+'/cancel',{method:'POST'});await refresh();}
async function del(id){if(jobList.some(j=>j.id===id))try{await api('jobs/'+id,{method:'DELETE'});}catch(e){if(e.k!=='missing')throw e;}
 await tx('readwrite',s=>s.delete(id));jobList=jobList.filter(j=>j.id!==id);fire();}
async function clear(){if(available)await api('jobs',{method:'DELETE'});await cacheClear();jobList=[];fire();}
PL.gen = {PROV,RATIOS,cfg,setCfg,modelOf,profile,profiles:()=>profiles,saveProfile,deleteProfile,defaultProfile,forgetKey,models,erase,run,cancel,jobs,del,clear,init,available:()=>available,session:()=>session};
if('serviceWorker'in navigator&&location.protocol!=='file:')navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>{const u=r.active&&r.active.scriptURL;if(u&&new URL(u).pathname===new URL('gen-sw.js',API.replace('api/generation/','')).pathname)r.update().catch(()=>{});})).catch(()=>{});
addEventListener('storage',e=>{if(e.key==='pl.genSession'){available=false;session=null;profiles=[];jobList=[];fire();if(e.newValue)init().then(fire);}});
init().then(fire);
setInterval(()=>{if(available&&(active||!document.hidden))refresh().catch(e=>{if(e.k==='session'){available=false;jobList=[];profiles=[];cacheClear();fire();}});},2000);
})();
</script>"""
