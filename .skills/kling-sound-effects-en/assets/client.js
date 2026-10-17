// Browser module. Pass the application's existing Supabase client, never an upstream key.
export function audioClient(supabase) {
 async function call(body) {
  const {data,error}=await supabase.functions.invoke('kling-audio',{body});
  if(error)throw Error('Request failed: '+error.message);
  if(data.error)throw Error(data.error);
  return data;
 }
 async function watch(id,onUpdate,signal) {
  const deadline=Date.now()+15*60*1000;
  while(!signal?.aborted && Date.now()<deadline) {
   const t=await call({action:'query',id});onUpdate(t);
   if(['succeeded','failed','timeout'].includes(t.state))return t;
   await new Promise(r=>setTimeout(r,5000));
  }
  if(!signal?.aborted)onUpdate({id,state:'timeout',message:'Waiting timed out. Resume this task; do not generate again.'});
 }
 function render(root,t) {
  root.replaceChildren();const label=document.createElement('p');label.textContent=t.state+(t.message?' — '+t.message:'');root.append(label);
  if(t.state!=='succeeded')return;
  for(const m of (t.media||[]).map(m=>(t.saved||[]).find(s=>s.format===m.format)||m)) {
   const player=document.createElement(m.format==='mp4'?'video':'audio');player.controls=true;player.src=m.url;root.append(player);
   const a=document.createElement('a');a.href=m.url;a.textContent='Open / Download '+m.format.toUpperCase();a.target='_blank';a.rel='noopener';root.append(a);
  }
  const note=document.createElement('p');note.textContent='Original links are temporary (provider retention: 30 days). Download promptly; playback/history does not mean a permanent copy has been saved.';root.append(note);
  if(t.can_save!==true)return;
  const button=document.createElement('button');button.textContent='Save to my files';button.onclick=async()=>{button.disabled=true;try{render(root,await call({action:'save',id:t.id}));}catch(e){label.textContent=e.message;}finally{button.disabled=false;}};root.append(button);
 }
 return {call,watch,render};
}
