// Private transfer is optional. Never infer trusted hosts from client input.
export function transferCapability(media, configuredHosts) {
 const hosts=String(configuredHosts||'').split(/[\s,，;；]+/u).filter(Boolean).map(s=>s.toLowerCase());
 if(!hosts.length)return {can_save:false,save_reason:'Private transfer is not configured. Original media remains available; download within 30 days.'};
 if(!media?.length)return {can_save:false,save_reason:'No media available yet.'};
 for(const m of media) {
  let u;try{u=new URL(m.url);}catch{return {can_save:false,save_reason:'Invalid media URL.'};}
  if(u.protocol!=='https:'||u.username||u.password||u.port||!hosts.includes(u.hostname.toLowerCase()))return {can_save:false,save_reason:'Private transfer is not configured for this media host. Original media remains available.'};
 }
 return {can_save:true,save_reason:''};
}
