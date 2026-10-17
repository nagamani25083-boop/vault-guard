import { createClient } from 'npm:@supabase/supabase-js@2';
import { validate, parseTask, owned } from './core.mjs';
import { transferCapability } from './media-policy.mjs';
const env=(k:string)=>{const v=Deno.env.get(k);if(!v)throw Error('Missing server configuration: '+k);return v;};
const db=createClient(env('SUPABASE_URL'),env('SUPABASE_SERVICE_ROLE_KEY'));
const table=()=>db.from('kling_audio_jobs');
const check=(r:any)=>{if(r.error)throw Error('Database/storage operation failed');return r.data;};
async function upstream(kind:string, id:string|null, body?:any) {
 const route=kind==='text'?'text-to-audio':'video-to-audio';
 const ids={"text_create": "api-ELbW03DAPQrY", "text_query": "api-wYqgkBmrQvw9", "video_create": "api-NLZ1R6MBQ4J9", "video_query": "api-zYm4DrmyA0eL"};
 const apiId=ids[(kind+(id?'_query':'_create')) as keyof typeof ids];
 const r=await fetch('https://'+apiId+'@app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/v1/audio/'+route+(id?'/'+encodeURIComponent(id):''),{
 method:id?'GET':'POST',headers:{'Content-Type':'application/json','X-Gateway-Authorization':'Bearer '+env('INTEGRATIONS_API_KEY')},
 body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(25000)});
 if(!r.ok)throw Error('Upstream HTTP '+r.status);
 return parseTask(await r.json(),id);
}
async function present(row:any) {
 const saved=[];
 for(const m of row.saved||[]) {const d=check(await db.storage.from('kling-audio').createSignedUrl(m.path,600));saved.push({...m,url:d.signedUrl});}
 return {id:row.id,kind:row.kind,state:row.state,message:row.message,media:row.media,saved,...transferCapability(row.media,Deno.env.get('MEDIA_HOSTS'))};
}
Deno.serve(async req=>{
 const origin=Deno.env.get('APP_ORIGIN')||'';
 const h={'Content-Type':'application/json','Access-Control-Allow-Origin':origin,'Access-Control-Allow-Headers':'authorization, apikey, content-type, x-client-info','Access-Control-Allow-Methods':'POST, OPTIONS','Vary':'Origin'};
 const reply=(v:any,s=200)=>new Response(JSON.stringify(v),{status:s,headers:h});
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:h});
 if(req.method!=='POST')return reply({error:'method not allowed'},405);
 let status=400;
 try {
  const jwt=req.headers.get('Authorization')?.replace(/^Bearer\s+/i,'');
  if(!jwt)return reply({error:'login required'},401);
  const {data,error}=await db.auth.getUser(jwt);
  if(error||!data.user)return reply({error:'login required'},401);
  const uid=data.user.id;
  const b=await req.json();
  if(b.action==='list') {
   const rows=check(await table().select('*').eq('user_id',uid).order('created_at',{ascending:false}).limit(50));
   return reply({jobs:await Promise.all(rows.map(present))});
  }
  if(b.action==='create') {
   const params=validate(b.kind,b.params||{});
   if(params.video_id) {
    const sources=check(await table().select('media').eq('user_id',uid).eq('state','succeeded'));
    if(!sources.some((r:any)=>r.media.some((m:any)=>m.upstream_video_id===params.video_id)))throw Error('Reference video ownership not verified; use your uploaded video URL');
   }
   if(typeof b.id!=='string'||! /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(b.id))throw Error('UUID v4 id required');
   // Insert before the paid call. Reusing an ID never issues another POST.
   const ins=await table().insert({id:b.id,user_id:uid,kind:b.kind}).select().single();
   if(ins.error) {
    if(ins.error.code!=='23505')throw Error('Database insert failed');
    const old=check(await table().select('*').eq('id',b.id).eq('user_id',uid).maybeSingle());
    if(!old)return reply({error:'not found'},404);
    return reply(await present(old));
   }
   try {
    const result=await upstream(b.kind,null,{...params,external_task_id:b.id});
    const row=check(await table().update(result).eq('id',b.id).eq('user_id',uid).select().single());
    return reply(await present(row));
   }catch(e) {
    // Could have been accepted upstream: do not silently recreate a paid task.
    check(await table().update({state:'timeout',message:'Submission outcome uncertain; reconcile existing external_task_id before any new generation.'}).eq('id',b.id).eq('user_id',uid));
    throw e;
   }
  }
  const row=check(await table().select('*').eq('id',b.id).eq('user_id',uid).maybeSingle());
  if(!row)return reply({error:'not found'},404);
  owned(row,uid);
  if(b.action==='query') {
   if(!['submitted','processing'].includes(row.state))return reply(await present(row));
   // Atomic five-second lease across tabs/requests; requests never overlap in a tight loop.
   const claim=check(await table().update({next_poll:new Date(Date.now()+30000).toISOString()}).eq('id',row.id).eq('user_id',uid).lte('next_poll',new Date().toISOString()).select());
   if(!claim.length)return reply(await present(row));
   const result=await upstream(row.kind,row.upstream_id);
   const updated=check(await table().update({...result,next_poll:new Date(Date.now()+5000).toISOString()}).eq('id',row.id).eq('user_id',uid).select().single());
   return reply(await present(updated));
  }
  if(b.action==='save') {
   if(row.state!=='succeeded')throw Error('task has not succeeded');
   const capability=transferCapability(row.media,Deno.env.get('MEDIA_HOSTS'));
   if(!capability.can_save)return reply({error:capability.save_reason,code:'TRANSFER_NOT_CONFIGURED'},409);
   const saved=[];
   for(const [i,m] of row.media.entries()) {
    const path=uid+'/'+row.id+'/'+i+'.'+m.format;
    const previous=row.saved.find((s:any)=>s.path===path);
    if(previous){saved.push(previous);continue;}
    const u=new URL(m.url);
    const allowed=env('MEDIA_HOSTS').split(',').map(s=>s.trim());
    if(u.protocol!=='https:'||u.username||u.password||!allowed.includes(u.hostname))throw Error('Media hostname not configured');
    const r=await fetch(u,{redirect:'error',signal:AbortSignal.timeout(20000)});
    if(!r.ok||!r.body)throw Error('Media download HTTP '+r.status);
    const reader=r.body.getReader(), chunks:Uint8Array[]=[];let size=0;
    while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>32*1024*1024){await reader.cancel();throw Error('Media exceeds 32 MiB transfer budget; configure a larger transfer worker');}chunks.push(value);}
    if(!size)throw Error('Empty media');
    const type=m.format==='mp4'?'video/mp4':m.format==='wav'?'audio/wav':'audio/mpeg';
    check(await db.storage.from('kling-audio').upload(path,new Blob(chunks,{type}),{contentType:type,upsert:true}));
    saved.push({path,format:m.format});
    check(await table().update({saved}).eq('id',row.id).eq('user_id',uid));
   }
   return reply(await present({...row,saved}));
  }
  return reply({error:'unknown action'},400);
 }catch(e){return reply({error:String((e as Error).message)},status);}
});
