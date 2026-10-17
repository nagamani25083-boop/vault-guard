export function validate(kind, p) {
  if (!['text','video'].includes(kind)) throw Error('invalid kind');
  const keys = kind==='text'?['prompt','duration']:['video_id','video_url','sound_effect_prompt','bgm_prompt','asmr_mode'];
  const out = Object.fromEntries(keys.filter(k=>p[k]!==undefined && p[k]!=='').map(k=>[k,p[k]]));
  for (const k of ['prompt','sound_effect_prompt','bgm_prompt']) if(out[k]!==undefined && (typeof out[k]!=='string'||[...out[k]].length>200)) throw Error(k+' must be <=200 characters');
  if(kind==='text') {
    if(!out.prompt?.trim()) throw Error('prompt required');
    if(typeof out.duration!=='number'||out.duration<3||out.duration>10||Math.abs(out.duration*10-Math.round(out.duration*10))>1e-8) throw Error('duration: 3–10 seconds, one decimal');
  } else {
    if(Boolean(out.video_id)===Boolean(out.video_url)) throw Error('choose video_id OR video_url');
    if(out.video_id!==undefined && (typeof out.video_id!=='string'||!out.video_id.trim())) throw Error('invalid video_id');
    if(out.video_url!==undefined) {const u=new URL(out.video_url); if(u.protocol!=='https:'||u.username||u.password) throw Error('HTTPS video URL required');}
    if(out.asmr_mode!==undefined && typeof out.asmr_mode!=='boolean') throw Error('asmr_mode must be boolean');
  }
  return out;
}
export function parseTask(j, expected) {
  if(j.code!==0) throw Error('Upstream code '+j.code+': '+String(j.message||''));
  const d=j.data;
  if(!d || typeof d.task_id!=='string'||!d.task_id || (expected && d.task_id!==expected)) throw Error('task ID mismatch or missing');
  const state={submitted:'submitted',processing:'processing',succeed:'succeeded',failed:'failed'}[d.task_status];
  if(!state) throw Error('unknown upstream task state');
  const media=[];
  if(state==='succeeded') {
    for(const a of d.task_result?.audios||[]) for(const f of ['mp3','wav']) if(a['url_'+f]) media.push({url:a['url_'+f],format:f});
    for(const v of d.task_result?.videos||[]) if(v.url) media.push({url:v.url,format:'mp4',upstream_video_id:v.id});
    if(!media.length) throw Error('success without media');
    for(const m of media) if(new URL(m.url).protocol!=='https:') throw Error('invalid media URL');
  }
  return {upstream_id:d.task_id,state,message:d.task_status_msg||'',media};
}
export function owned(row, user) {if(!row||row.user_id!==user) throw Error('not found'); return row;}
