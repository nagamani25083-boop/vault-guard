#!/usr/bin/env python3
"""Generation-time operator tool only; never expose to app users.
Environment: INTEGRATIONS_API_KEY. Run inside the platform gateway-enabled runtime.
The filename is retained for compatibility; this script now calls the managed gateway.
A receipt is a private local task record, not an app authorization mechanism.
"""
import argparse,json,os,sys,urllib.request,urllib.error,uuid
from pathlib import Path
KINDS=['text','video']
IDS={'text': ('api-ELbW03DAPQrY', 'api-wYqgkBmrQvw9'), 'video': ('api-NLZ1R6MBQ4J9', 'api-zYm4DrmyA0eL')}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('action',choices=['create','query']);p.add_argument('--receipt',required=True)
 p.add_argument('--kind',choices=KINDS,default='text');p.add_argument('--params',default='{}')
 a=p.parse_args()
 try:
  path=Path(a.receipt)
  key=os.environ['INTEGRATIONS_API_KEY']
  if a.action=='create':
   body=json.loads(a.params)
   allowed=['prompt','duration'] if a.kind=='text' else ['video_url','sound_effect_prompt','bgm_prompt','asmr_mode']
   if set(body)-set(allowed):raise ValueError('unexpected fields; video_id requires verified app ownership')
   for k in ['prompt','sound_effect_prompt','bgm_prompt']:
    if k in body and (not isinstance(body[k],str) or len(body[k])>200):raise ValueError('prompt length/type')
   if a.kind=='text':
    t=body.get('duration')
    if not body.get('prompt','').strip() or isinstance(t,bool) or not isinstance(t,(float,int)) or not 3<=t<=10 or abs(t*10-round(t*10))>1e-8:raise ValueError('invalid text parameters')
   else:
    from urllib.parse import urlparse
    u=urlparse(body.get('video_url',''))
    if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('valid HTTPS video_url required')
    if 'asmr_mode' in body and not isinstance(body['asmr_mode'],bool):raise ValueError('asmr_mode boolean required')
   body['external_task_id']=str(uuid.uuid4())
   record={'kind':a.kind,'external_task_id':body['external_task_id'],'state':'submitting'}
   # Exclusive create prevents repeating a paid request using the same receipt.
   fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'w') as f:json.dump(record,f)
   idx=0;tail=''
  else:
   record=json.loads(path.read_text());body=None;idx=1
   if not record.get('task_id'):raise ValueError('submission outcome uncertain; reconcile, do not recreate')
   from urllib.parse import quote
   tail='/'+quote(record['task_id'],safe='')
  kind=record['kind'];url='https://'+IDS[kind][idx]+'@app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/v1/audio/'+kind+'-to-audio'+tail
  req=urllib.request.Request(url,data=json.dumps(body).encode() if body else None,headers={'X-Gateway-Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST' if body else 'GET')
  with urllib.request.urlopen(req,timeout=60) as r:j=json.load(r)
  if j.get('code')!=0:raise ValueError('upstream business failure: '+str(j.get('code')))
  d=j['data'];tid=d.get('task_id');state=d.get('task_status')
  if not tid or (idx and tid!=record['task_id']):raise ValueError('task ID mismatch')
  if state not in ['submitted','processing','succeed','failed']:raise ValueError('unknown task state')
  record.update(task_id=tid,state=state)
  if d.get('task_result'):record['result']=d['task_result']
  path.write_text(json.dumps(record,ensure_ascii=False));os.chmod(path,0o600)
  print(json.dumps(record,ensure_ascii=False));return 1 if state=='failed' else 0
 except urllib.error.HTTPError as e:
  print(json.dumps({'error':'HTTP '+str(e.code),'retry_create':False}));return 1
 except Exception as e:
  print(json.dumps({'error':type(e).__name__,'retry_create':False}));return 1
if __name__=='__main__':sys.exit(main())
